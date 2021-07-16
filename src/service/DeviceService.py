# coding:utf-8
import time
from datetime import datetime
from datetime import timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Device import Device
from database.DeviceFaceInfo import DeviceFaceInfo
from database.Student import Student
from database.Face import Face
from database.Car import Car
from database.Worker import Worker
from utils import defines
from database.School import School
from msgqueue import producer
from ext import cache


class DeviceService(object):

    @staticmethod
    def device_list(device_iid, license_plate_number, status, page, size):
        """
        设备id  车牌号 设备状态
        """
        db.session.commit() # SELECT
        offset = (page - 1) * size
        query = db.session.query(Device)
        if device_iid:
            query = query.filter(Device.device_iid.like('%%{}%%'.format(device_iid)))
        if license_plate_number:
            query = query.filter(Device.license_plate_number.like(
                '%%{}%%'.format(license_plate_number)))

        cur_timestamp = int(time.time())
        if status:
            status = int(status)
            devices = []
            ks = cache.hgetall(defines.RedisKey.DEVICE_CUR_TIMESTAMP)
            for device_name, tstmp in ks.items():
                print device_name, tstmp
                if status == 1:
                    if tstmp and (cur_timestamp - int(tstmp)) < 30:
                        devices.append(device_name)
                elif status == 2:
                    if not tstmp or ((cur_timestamp - int(tstmp)) > 30):
                        devices.append(device_name)

            query = query.filter(Device.device_name.in_(devices))
        query = query.filter(Device.status != 10)

        count = query.count()
        query = query.order_by(Device.id.desc())
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            device_timestamp = cache.hget(
                defines.RedisKey.DEVICE_CUR_TIMESTAMP, row.device_name)
            if not device_timestamp or (cur_timestamp - int(device_timestamp) > 30):
                is_online = u"离线"
            else:   # if cur_timestamp - int(device_timestamp) < 30:
                is_online = u"在线"

            device_gps = cache.hget(
                defines.RedisKey.DEVICE_CUR_GPS, row.device_name)
            if device_timestamp:
                device_last_time = datetime.fromtimestamp(
                    float(int(device_timestamp))).strftime('%Y-%m-%d %H:%M:%S')
            else:
                device_last_time = ""
            data.append({
                'id': row.id,
                'device_name': row.device_name,
                'device_iid': row.device_iid,
                'imei': row.imei,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number,
                'status': row.status,
                'sound_volume': row.sound_volume,
                'device_type': row.device_type,
                'mac': row.mac,
                'is_online': is_online,
                'device_timestamp': device_last_time,
                'gps': device_gps
            })
        return {'results': data, 'count': count}

    @staticmethod
    def device_update(pk, license_plate_number, car_id,
                      sound_volume, device_type, mfr_id):
        """
        设备ID 关联车辆  设备音量
        license_plate_number 似乎没有使用
        """
        db.session.commit() # SELECT
        device = db.session.query(Device).filter(
            Device.id == pk).first()
        if not device:
            return -1

        if sound_volume:
            device.sound_volume = sound_volume

        if device_type:
            # 当前已创建虚拟设备
            if device.status == 1:
                device.device_type = device_type
                # 如果设备是生成特征值
                if device.device_type == 2:
                    device.status = 2   # 直接修改为2
                    car_id = -10
                    # 将设备名字存入缓存
                    cache.sadd(defines.RedisKey.GENERATE_DEVICE_NAMES,
                               device.device_name)
            else:
                if device.device_type != device_type:
                    return -11  # 初始化已完成,不能再修改设备类型

        if car_id:
            # 清空
            if car_id == -10:
                device.car_id = None
                device.license_plate_number = None
            else:
                # 该车辆是否已经绑定设备
                if db.session.query(Device).filter(
                        Device.car_id == car_id).first():
                    return -13

                # 该车辆是否已经绑定工作人员
                cnt = db.session.query(Worker).filter(
                    Worker.car_id == car_id).count()
                if cnt < 2:
                    return -12

                car = db.session.query(Car).filter(Car.id == car_id).first()

                device.car_id = car_id
                device.license_plate_number = car.license_plate_number
                device.person_limit = car.capacity
                # 如果用户关联设备和车辆,判断状态是否为1,为1就修改到2
                if device.status == 1:
                    device.status = 2

                # 修改设备关联的车辆需要删除缓存
                cache.hdel(defines.RedisKey.CACHE_CAR_DATA,
                           device.device_name)
        device.mfr_id = mfr_id
        if not device.device_type:
            device.device_type = 1
        try:
            d = {'id': device.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def get_device_person_data(pk):
        """获取设备上的人员信息"""
        db.session.commit() # SELECT
        try:
            device = db.session.query(Device).filter(
                Device.id == pk).one()
        except (MultipleResultsFound, NoResultFound) as ex:
            return -2

        obj = db.session.query(DeviceFaceInfo). \
            filter(DeviceFaceInfo.device_id == device.id).first()
        if obj and obj.update_timestamp and \
                int(time.time()) - int(obj.update_timestamp) < 60:
            d = {}
            person_fid_list = []
            if obj.info_str:
                raw = obj.info_str.split(",")
                for row in raw:
                    person_fid_list.append(int(row))

            students = db.session.query(Student, School.school_name).join(
                Face, Face.stu_id == Student.id).join(
                School, School.id == Student.school_id).filter(
                Face.id.in_(person_fid_list)).all()
            person_list = []
            for row in students:
                student = row[0]
                school_name = row[1]
                person_list.append({
                    'id': student.id,
                    'nickname': student.nickname,
                    'school_name': school_name,
                    'grade_name': defines.grade[student.grade_id],
                    'class_name': defines.classes[student.class_id],
                    'stu_no': student.stu_no
                })
            d["published"] = person_list
            d["published_numbers"] = len(person_fid_list)

            return d
        else:

            k = cache.get(defines.RedisKey.QUERY_DEVICE_PEOPLE)
            if k:
                return -1  # 正在刷新数据到数据库

            if device.status != 5:
                return -3  # 设备还未初始化人员

            dev_timestamp = cache.hget(
                defines.RedisKey.DEVICE_CUR_TIMESTAMP, device.device_name)
            time_diff = int(time.time()) - int(dev_timestamp)
            if time_diff > 30:
                return -4  # 设备未开机

            # 已在线且三分钟后
            if time_diff < 30 and \
                    datetime.now() - timedelta(minutes=3) < device.open_time:
                return -5

            # 发送消息
            cache.set(defines.RedisKey.QUERY_DEVICE_PEOPLE, 1)
            cache.expire(defines.RedisKey.QUERY_DEVICE_PEOPLE, 30)
            producer.get_device_people_data(device.device_name)

            return {"published": [], "published_numbers": 0}