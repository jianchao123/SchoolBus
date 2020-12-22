# coding:utf-8
import time
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Device import Device
from database.DeviceFaceInfo import DeviceFaceInfo
from database.Student import Student
from database.Face import Face
from database.Car import Car
from utils import defines
from msgqueue import producer
from ext import cache


class DeviceService(object):

    @staticmethod
    def device_list(device_iid, license_plate_number, status, page, size):
        """
        设备id  车牌号 设备状态
        """
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Device)
        if device_iid:
            query = query.filter(Device.device_iid == device_iid)
        if license_plate_number:
            query = query.filter(Device.license_plate_number == license_plate_number)

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
                    print "========================="
                    if not tstmp or ((cur_timestamp - int(tstmp)) > 30):
                        devices.append(device_name)

            query = query.filter(Device.device_name.in_(devices))
        query = query.filter(Device.status != 10)

        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            device_timestamp = cache.hget(
                defines.RedisKey.DEVICE_CUR_TIMESTAMP, row.device_name)
            if not device_timestamp or (cur_timestamp - int(device_timestamp) > 30):
                is_online = u"离线"
            elif cur_timestamp - int(device_timestamp) < 30:
                is_online = u"在线"

            device_gps = cache.hget(
                defines.RedisKey.DEVICE_CUR_GPS, row.device_name)
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
                'device_timestamp': device_timestamp,
                'gps': device_gps
            })
        return {'results': data, 'count': count}

    @staticmethod
    def device_update(pk, license_plate_number, car_id,
                      sound_volume, device_type):
        """
        设备ID 关联车辆  设备音量
        license_plate_number 似乎没有使用
        """
        device = db.session.query(Device).filter(
            Device.id == pk).first()
        if not device:
            return -1

        if license_plate_number:
            # 这里只能修改设备上的车牌,需要先在车辆修改车牌
            cnt = db.session.query(Car).filter(
                Car.license_plate_number == license_plate_number).count()
            if not cnt:
                return -10  # 车牌找不到

        if sound_volume:
            device.sound_volume = sound_volume
            workmode = 0 if device.device_type == 1 else 3
            producer.update_chepai(device.device_name,
                                   device.license_plate_number,
                                   device.sound_volume, workmode)

        if device_type:
            # 当前已创建虚拟设备
            if device.status == 1:
                device.device_type = device_type
                # 如果设备是生成特征值
                if device.device_type == 2:
                    device.status = 2   # 直接修改为2
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
            else:
                # 该车辆是否已经绑定工作人员
                cnt = db.session.query(Car).filter(
                    Car.id == car_id).filter(
                    or_(Car.worker_1_id == None, Car.worker_2_id == None)
                ).count()
                if cnt:
                    return -12

                car = db.session.query(Car).filter(Car.id == car_id).first()
                device.car_id = car_id
                device.license_plate_number = car.license_plate_number
                # 如果用户关联设备和车辆,判断状态是否为1,为1就修改到2
                if device.status == 1:
                    device.status = 2

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
        db.session.commit()
        try:
            device = db.session.query(Device).filter(
                Device.id == pk).one()
        except (MultipleResultsFound, NoResultFound) as ex:
            return -2

        obj = db.session.query(DeviceFaceInfo). \
            filter(DeviceFaceInfo.device_id == device.id).first()
        if obj:
            d = {}
            person_fid_list = []
            if obj.info_str:
                raw = obj.info_str.split(",")
                for row in raw:
                    person_fid_list.append(row.split("|"))
            from database.School import School
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
                    'grade_name': defines.grade[students.grade_id],
                    'class_name': defines.classes[students.class_id],
                    'stu_no': student.stu_no
                })
            d["published"] = person_list
            d["published_numbers"] = len(person_fid_list)

            return d
        else:
            return {"published": [], "published_numbers": 0}