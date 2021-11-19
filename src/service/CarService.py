# coding:utf-8
import xlrd
import sys
import json
import time
import inspect
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from sqlalchemy import or_
from database.db import db
from database.Car import Car
from database.Student import Student
from database.Device import Device
from database.Worker import Worker
from utils import defines
from msgqueue import producer
from ext import cache
from utils.tools import get_frame_name_param


class CarService(object):

    @staticmethod
    def car_name_list():
        db.session.commit() # SELECT

        d = []
        results = db.session.query(Car.id, Car.license_plate_number).filter(
            Car.status == 1).order_by(Car.id.desc()).all()

        for row in results:
            rid = row[0]
            license_plate_number = row[1]
            d.append({"id": rid, "name": license_plate_number})

        return {'results': d, 'count': 0}

    @staticmethod
    def car_list(query_str, is_online, scheduling, status, page, size):
        db.session.commit() # SELECT
        cur_timestamp = int(time.time())
        offset = (page - 1) * size
        query = db.session.query(Car)
        if query_str:
            query_str = '%%{keyword}%%'.format(keyword=query_str)

            results = db.session.query(Device).filter(
                Device.device_iid.like(query_str)).all()
            car_ids = [row.car_id for row in results]

            query = query.filter(or_(
                Car.id.in_(car_ids), Car.license_plate_number.like(query_str)))
        if is_online:
            is_online = int(is_online)
            devices = []
            ks = cache.hgetall(defines.RedisKey.DEVICE_CUR_TIMESTAMP)
            for device_name, tstmp in ks.items():
                print device_name, tstmp
                if is_online == 1:
                    if tstmp and (cur_timestamp - int(tstmp)) < 30:
                        devices.append(device_name)
                elif is_online == 2:
                    if not tstmp or ((cur_timestamp - int(tstmp)) > 30):
                        devices.append(device_name)
            car_ids = []
            device_results = db.session.query(Device).filter(
                Device.device_name.in_(devices)).all()
            for row in device_results:
                if row.car_id:
                    car_ids.append(row.car_id)
            query = query.filter(Car.id.in_(car_ids))
        if scheduling:
            worker_group = db.session.query(
                Worker.car_id).filter(
                Worker.status == 1).group_by(Worker.car_id).having(
                func.count(Worker.id) > 1).all()
            scheduling_cars = [row[0] for row in worker_group]
            print scheduling_cars
            scheduling_cars = [row for row in scheduling_cars if row]
            if int(scheduling) == 1:
                query = query.filter(Car.id.in_(scheduling_cars))
            if int(scheduling) == 2:
                query = query.filter(Car.id.notin_(scheduling_cars))

        if status:
            status = int(status)
            if status == 1:
                carids = []
                devices = db.session.query(Device).filter(
                    Device.car_id.isnot(None)).all()
                for row in devices:
                    carids.append(row.car_id)
                query = query.filter(Car.id.in_(carids))
            elif status == 2:
                carids = []
                devices = db.session.query(Device).filter(
                    Device.car_id.isnot(None)).all()
                for row in devices:
                    carids.append(row.car_id)
                query = query.filter(~Car.id.in_(carids))

        query = query.filter(Car.status == 1)
        count = query.count()
        results = query.order_by(Car.id.desc()).offset(offset).limit(size).all()

        now = int(time.time())
        data = []
        for row in results:
            is_online = u"未绑定设备"
            device = db.session.query(Device).filter(
                Device.car_id == row.id).first()
            device_iid = None
            if device:
                device_iid = device.device_iid
                device_timestamp = cache.hget(
                    defines.RedisKey.DEVICE_CUR_TIMESTAMP, device.device_name)
                if not device_timestamp or (now - int(device_timestamp) > 30):
                    is_online = u"离线"
                else:
                    is_online = u"在线"
            # 查询绑定的工作人员
            worker_1_id = None
            worker_1_nickname = None
            worker_1_duty_name = None
            worker_2_id = None
            worker_2_nickname = None
            worker_2_duty_name = None
            workers = db.session.query(Worker).filter(Worker.car_id == row.id).all()
            for worker in workers:
                if worker.duty_id == 1:
                    worker_1_id = worker.id
                    worker_1_nickname = worker.nickname
                    worker_1_duty_name = defines.duty[worker.duty_id]
                elif worker.duty_id == 2:
                    worker_2_id = worker.id
                    worker_2_nickname = worker.nickname
                    worker_2_duty_name = defines.duty[worker.duty_id]

            data.append({
                'id': row.id,
                'code': row.code,
                'license_plate_number': row.license_plate_number,
                'capacity': row.capacity,
                'device_iid': device_iid,
                'worker_1_id': worker_1_id,
                'worker_1_nickname': worker_1_nickname,
                'worker_1_duty_name': worker_1_duty_name,
                'worker_2_id': worker_2_id,
                'worker_2_nickname': worker_2_nickname,
                'worker_2_duty_name': worker_2_duty_name,
                'company_name': row.company_name,
                'status': row.status,
                'is_online': is_online
            })
        return {'results': data, 'count': count}

    @staticmethod
    def car_add(license_plate_number, capacity, company_name, user_id):
        """
        车辆编码 车牌号 载客量 公司

        """
        db.session.commit() # SELECT
        car = db.session.query(Car).filter(
            Car.license_plate_number == license_plate_number,
            Car.status == 1).first()
        if car:
            return -10  # 车牌已经存在

        del_car = db.session.query(Car).filter(
            Car.license_plate_number == license_plate_number,
            Car.status == 10).first()
        if del_car:
            del_car.license_plate_number = 'xxxxxx'

        car = Car()
        car.code = str(datetime.now().strftime('%Y%m%d%H%M%S%f'))
        car.license_plate_number = license_plate_number
        car.capacity = capacity
        car.device_iid = ''
        car.company_name = company_name
        car.status = 1   # 有效

        try:
            db.session.add(car)
            new_id = car.id
            db.session.commit()

            # 日志
            func_name, func_param = get_frame_name_param(inspect.currentframe())
            producer.operation_log(func_name, func_param, user_id)

            return {'id': new_id}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def car_update(pk, license_plate_number, capacity, company_name, user_id):
        db.session.commit() # SELECT
        car = db.session.query(Car).filter(
            Car.id == pk).first()
        if not car:
            return -1
        if license_plate_number and\
                license_plate_number != car.license_plate_number:
            print u"更新车牌"
            cnt = db.session.query(Car).filter(
                Car.id != pk,
                Car.license_plate_number == license_plate_number).count()
            if cnt:
                return -10  # 车牌已经存在

            car.license_plate_number = license_plate_number
            # 更新学生关于车辆的信息
            producer.car_update(car.id, license_plate_number)

            # 是否绑定设备
            device = db.session.query(Device).filter(
                Device.car_id == car.id).first()
            if device:
                workmode = 0 if device.device_type == 1 else 3
                sound_vol = int(device.sound_volume) if device.sound_volume else 100
                person_limit = int(car.capacity) if car.capacity else 40
                producer.update_chepai(device.device_name,
                                       device.license_plate_number,
                                       int(sound_vol), workmode,
                                       person_limit)
                # 修改车牌需要删除车辆数据缓存
                # cache.hdel(defines.RedisKey.CACHE_CAR_DATA, device.device_name)
                cache.delete(defines.RedisKey.CACHE_CAR_DATA)

        if company_name:
            car.company_name = company_name
        if capacity:
            car.capacity = capacity

            # 是否绑定设备
            device = db.session.query(Device).filter(
                Device.car_id == car.id).first()
            if device:
                device.person_limit = capacity

        try:
            d = {'id': car.id}
            db.session.commit()

            # 日志
            func_name, func_param = get_frame_name_param(inspect.currentframe())
            producer.operation_log(func_name, func_param, user_id)
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def delete_cars(car_ids, user_id):
        """
        car_ids 1,2,3
        """
        db.session.commit() # SELECT
        db.session.execute("SET LOCAL citus.multi_shard_modify_mode "
                           "TO 'sequential';")
        car_id_list = car_ids.split(",")
        # db.session.execute(
        #     "set citus.multi_shard_commit_protocol TO '2pc';")
        # 1.查询车辆是否已经被绑定学生或设备或工作人员
        cnt = db.session.query(Student).filter(
            Student.car_id.in_(car_id_list)).count()
        if cnt:
            return -10
        cnt = db.session.query(Device).filter(
            Device.car_id.in_(car_id_list)).count()
        if cnt:
            return -11
        cnt = db.session.query(Worker).filter(
            Worker.car_id.in_(car_id_list)).count()
        if cnt:
            return -12

        results = db.session.query(Car).filter(
            Car.id.in_(car_id_list)).all()
        for row in results:
            row.status = 10
        try:
            db.session.commit()

            # 日志
            func_name, func_param = get_frame_name_param(inspect.currentframe())
            producer.operation_log(func_name, func_param, user_id)
            return {'id': 1}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def batch_add_car(excel_file):
        """
        车牌 载客量 公司
        """
        db.session.commit() # SELECT
        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        chepai_list = []
        results = db.session.query(Car).filter(Car.status == 1).all()
        for row in results:
            chepai_list.append(row.license_plate_number)

        # 查询所有车辆
        car_dict = {}
        results = db.session.query(Car).all()
        for row in results:
            car_dict[row.license_plate_number] = row.id

        error_msg_list = []
        for index in range(1, table.nrows):
            is_err = 0

            row_data = table.row_values(index)
            license_plate_number = str(row_data[0]).strip()
            capacity = str(row_data[1]).strip()
            company_name = str(row_data[2]).strip()

            err_str = u"\n第{}行,".format(index + 1)
            # 先检查是否为空
            if not capacity:
                err_str += u"载客量为空,"
                is_err = 1
            if not company_name:
                err_str += u"公司名字为空,"
                is_err = 1
            if not license_plate_number:
                err_str += u"车牌号为空,"
                is_err = 1

            # 检查重复
            if license_plate_number in chepai_list:
                err_str += u"车牌{}重复".format(license_plate_number)
                is_err = 1
            else:
                chepai_list.append(license_plate_number)

            if err_str:
                err_str += "\n"

            if is_err:
                error_msg_list.append(err_str)
        if error_msg_list:
            return {"c": 1, "msg": "\n".join(error_msg_list)}

        if cache.get('batch_add_car'):
            return -10  # 导入车辆执行中

        cache.set('batch_add_car', 1)
        cache.expire('batch_add_car', 50)

        car_list = []
        for index in range(1, table.nrows):
            row_data = table.row_values(index)
            print row_data[1], type(row_data[1])
            license_plate_number = str(row_data[0]).strip()
            capacity = str(int(row_data[1])).strip()
            company_name = str(row_data[2]).strip()

            l = [license_plate_number, capacity, company_name]
            car_list.append(l)
        # 发送消息
        print car_list
        start = 0
        end = 1000
        send_list = car_list[start: end]
        while send_list:
            producer.batch_add_car(send_list)
            send_list = car_list[start + 1000: end + 1000]
        return {"c": 0, 'msg': ''}
