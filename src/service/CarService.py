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
from database.Car import Car
from database.Car import Car
from database.Device import Device
from utils import defines
from utils import tools
from msgqueue import producer
from ext import cache


class CarService(object):

    @staticmethod
    def car_list(query_str, device_status, page, size):
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Car)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(Car.license_plate_number.like(query_str))

            results = db.session.query(Device).filter(
                Device.device_iid.like(query_str)).all()
            car_ids = [row.car_id for row in results]
            query = query.filter(Car.id.in_(car_ids))
        if device_status:
            results = db.session.query(Device).filter(
                Device.status == device_status).all()
            car_ids = [row.car_id for row in results]
            query = query.filter(Car.id.in_(car_ids))
        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'code': row.code,
                'license_plate_number': row.license_plate_number,
                'capacity': row.capacity,
                'device_iid': row.device_iid,
                'worker_1_id': row.worker_1_id,
                'worker_1_nickname': row.worker_1_nickname,
                'worker_1_duty_name': row.worker_1_duty_name,
                'worker_2_id': row.worker_2_id,
                'worker_2_nickname': row.worker_2_nickname,
                'worker_2_duty_name': row.worker_2_duty_name,
                'company_name': row.company_name,
                'status': row.status
            })
        return {'results': data, 'count': count}

    @staticmethod
    def car_add(license_plate_number, capacity, company_name):
        """
        车辆编码 车牌号 载客量 公司
        """
        car = db.session.query(Car).filter(
            Car.license_plate_number == license_plate_number).first()
        if car:
            return -10  # 车牌已经存在

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
            return new_id
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def car_update(pk, license_plate_number, capacity, company_name):
        """

    id = db.Column(db.BigInteger, primary_key=True)
    code = db.Column(db.String(16))
    license_plate_number = db.Column(db.String(16))
    capacity = db.Column(db.Integer)
    device_iid = db.Column(db.String(16))
    worker_1_id = db.Column(db.Integer)
    worker_1_nickname = db.Column(db.String(32))
    worker_1_duty_name = db.Column(db.Integer)
    worker_2_id = db.Column(db.Integer)
    worker_2_nickname = db.Column(db.String(32))
    worker_2_duty_name = db.Column(db.Integer)
    company_name = db.Column(db.String(16))     # 车辆所属公司
    status = db.Column(db.Integer)              # 1有效
        """
        car = db.session.query(Car).filter(
            Car.pk == pk).first()
        if car:
            return -1
        cnt = db.session.query(Car).filter(
            Car.pk != pk, Car.emp_no == emp_no).count()
        if cnt:
            return -10  # 工号已经存在

        if company_name:
            car.company_name = company_name
        if department_name:
            car.department_name = department_name
        if duty_id:
            car.duty_id = duty_id
        if license_plate_number:
            car = db.session.query(Car).filter(
                Car.license_plate_number == license_plate_number).first()
            if not car:
                return -11  # 车辆未找到
            car.car_id = car.id
            car.license_plate_number = license_plate_number
        if nickname or duty_id:
            producer.car_update(
                car.id, car.car_id, car.nickname, car.duty_id,
                defines.duty[car.duty_id])
        try:
            db.session.add(car)
            db.session.commit()
            return car.id
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def batch_add_car(excel_file):
        """工号 姓名 性别 手机号 备注 公司 部门职务 车牌
        """
        db.session.commit()

        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        if cache.get('batch_add_car'):
            return -10  # 导入工作人员执行中

        cache.set('batch_add_car', 1)
        cache.expire('batch_add_car', 300)

        emp_no_list = []
        results = db.session.query(Car).filter(Car.status == 1).all()
        for row in results:
            emp_no_list.append(row.emp_no)

        # 查询所有车辆
        car_dict = {}
        results = db.session.query(Car).all()
        for row in results:
            car_dict[row.license_plate_number] = row.id

        error_msg_list = []
        for index in range(1, table.nrows):
            is_err = 0

            row_data = table.row_values(index)
            emp_no = str(row_data[0]).strip()
            nickname = str(row_data[1]).strip()
            gender_name = str(row_data[2]).strip()
            mobile = str(row_data[3]).strip()
            remarks = str(row_data[4]).strip()
            company_name = str(row_data[5]).strip()
            department_name = str(row_data[6]).strip()
            duty_name = str(row_data[7]).strip()
            license_plate_number = str(row_data[8]).strip()

            err_str = u"\n第{}行,".format(index + 1)
            # 先检查是否为空
            if not emp_no:
                err_str += u"工号为空,"
                is_err = 1
            if not nickname:
                err_str += u"姓名为空,"
                is_err = 1
            if not gender_name:
                err_str += u"性别为空,"
                is_err = 1
            if not mobile:
                err_str += u"手机号为空,"
                is_err = 1
            if not remarks:
                err_str += u"备注为空,"
                is_err = 1
            if not company_name:
                err_str += u"公司名为空,"
                is_err = 1
            if not department_name:
                err_str += u"部门名为空,"
                is_err = 1
            if not duty_name:
                err_str += u"职务名为空,"
                is_err = 1
            if not license_plate_number:
                err_str += u"车牌号为空,"
                is_err = 1

            # 检查格式
            if gender_name not in defines.gender:
                err_str += u"性别只有'男'或'女'"
                is_err = 1
            if duty_name not in defines.duty:
                err_str += u"职务只有驾驶员和照管员"
                is_err = 1
            if license_plate_number not in car_dict:
                err_str += u"未知的车牌"
                is_err = 1

            # 检查重复
            if emp_no in emp_no_list:
                err_str += u"工号{}重复".format(emp_no)
                is_err = 1
            else:
                emp_no_list.append(emp_no)

            if err_str:
                err_str += "\n"

            if is_err:
                error_msg_list.append(err_str)
        if error_msg_list:
            return {"c": 1, "msg": "\n".join(error_msg_list)}

        car_list = []
        for index in range(1, table.nrows):
            row_data = table.row_values(index)
            emp_no = str(row_data[0]).strip()
            nickname = str(row_data[1]).strip()
            gender_name = str(row_data[2]).strip()
            mobile = str(row_data[3]).strip()
            remarks = str(row_data[4]).strip()
            company_name = str(row_data[5]).strip()
            department_name = str(row_data[6]).strip()
            duty_name = str(row_data[7]).strip()
            license_plate_number = str(row_data[8]).strip()

            l = [emp_no, nickname, defines.gender.index(gender_name),
                 mobile, remarks, company_name, department_name,
                 defines.duty.index(duty_name), car_dict[license_plate_number],
                 license_plate_number]
            car_list.append(l)
        # 发送消息
        print car_list
        start = 0
        end = 1000
        send_list = car_list[start: end]
        while send_list:
            producer.batch_add_student(send_list)
            send_list = car_list[start + 1000: end + 1000]
        return {"c": 0, 'msg': ''}