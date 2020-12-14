# coding:utf-8
import xlrd
import time
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Device import Device
from database.DeviceFaceInfo import DeviceFaceInfo
from database.Student import Student
from database.Face import Face
from utils import defines
from utils import tools
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
        if status:
            query = query.filter(Device.status == status)

        count = query.count()
        results = query.offset(offset).limit(size).all()

        now = datetime.now()
        data = []
        for row in results:
            device_timestamp = cache.hget(
                defines.RedisKey.DEVICE_CUR_TIMESTAMP, row.device_name)
            if now - device_timestamp > 30:
                is_online = u"离线"
            else:
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
    def device_update(pk, license_plate_number, car_id, sound_volume):
        """
        设备ID 关联车辆  设备音量
        """
        device = db.session.query(Device).filter(
            Device.pk == pk).first()
        if not device:
            return -1
        if license_plate_number:
            cnt = db.session.query(Device).filter(
                Device.pk != pk,
                Device.license_plate_number == license_plate_number).count()
            if cnt:
                return -10  # 车牌已经存在

        if car_id:
            device.car_id = car_id
        if sound_volume:
            device.sound_volume = sound_volume
            producer.update_chepai(device.device_name,
                                   device.license_plate_number,
                                   device.sound_volume)
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