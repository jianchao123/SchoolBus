# coding:utf-8
import time
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Device import Device
from database.DeviceFaceInfo import DeviceFaceInfo
from database.Student import Student
from database.Face import Face
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
                'is_online': is_online
            })
        return {'results': data, 'count': count}

    @staticmethod
    def device_update(pk, license_plate_number, car_id,
                      sound_volume, device_type):
        """
        设备ID 关联车辆  设备音量
        """
        device = db.session.query(Device).filter(
            Device.pk == pk).first()
        if not device:
            return -1

        if device.status == 5 and device_type:
            return -11  # 初始化已完成,不能再修改设备类型

        if license_plate_number:
            cnt = db.session.query(Device).filter(
                Device.pk != pk,
                Device.license_plate_number == license_plate_number).count()
            if cnt:
                return -10  # 车牌已经存在

        if car_id:
            device.car_id = car_id
            device.status = 2   # 已关联车辆
        if sound_volume:
            device.sound_volume = sound_volume
            producer.update_chepai(device.device_name,
                                   device.license_plate_number,
                                   device.sound_volume)
        if device_type:
            device.device_type = device_type
            # 将设备名字存入缓存
            cache.sadd(defines.RedisKey.GENERATE_DEVICE_NAMES, device.device_name)

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