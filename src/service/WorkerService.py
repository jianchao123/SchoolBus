# coding:utf-8
import xlrd
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Worker import Worker
from database.Car import Car
from utils import defines
from msgqueue import producer
from ext import cache


class WorkerService(object):

    @staticmethod
    def worker_list(query_str, page, size):
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Worker)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(
                Worker.emp_no.like(query_str),
                Worker.nickname.like(query_str)))

        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'emp_no': row.emp_no,
                'nickname': row.nickname,
                'gender': row.gender,
                'mobile': row.mobile,
                'remarks': row.remarks,
                'company_name': row.company_name,
                'department_name': row.department_name,
                'duty_id': row.duty_id,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number
            })
        return {'results': data, 'count': count}

    @staticmethod
    def worker_add(emp_no, nickname, gender, mobile, remarks, company_name,
                   department_name, duty_id, license_plate_number):
        worker = db.session.query(Worker).filter(
            Worker.emp_no == emp_no).first()
        if worker:
            return -10  # 工号已经存在
        car = db.session.query(Car).filter(
            Car.license_plate_number == license_plate_number).first()
        if not car:
            return -11  # 车辆未找到

        worker = Worker()
        worker.emp_no = emp_no
        worker.nickname = nickname
        worker.gender = gender
        worker.mobile = mobile
        worker.remarks = remarks
        worker.company_name = company_name
        worker.department_name = department_name
        worker.duty_id = duty_id
        worker.car_id = car.id
        worker.license_plate_number = license_plate_number
        worker.status = 1   # 有效
        producer.worker_insert(
            worker.id, worker.car_id, worker.nickname, worker.duty_id,
            defines.duty[worker.duty_id])
        try:
            db.session.add(worker)
            new_id = worker.id
            db.session.commit()
            return {'id': new_id}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def worker_update(pk, emp_no, nickname, gender, mobile, remarks,
                      company_name, department_name, duty_id,
                      license_plate_number):
        worker = db.session.query(Worker).filter(
            Worker.pk == pk).first()
        if not worker:
            return -1
        if emp_no:
            cnt = db.session.query(Worker).filter(
                Worker.pk != pk, Worker.emp_no == emp_no).count()
            if cnt:
                return -10  # 工号已经存在
        if nickname:
            worker.nickname = nickname
        if gender:
            worker.gender = gender
        if mobile:
            worker.mobile = mobile
        if remarks:
            worker.remarks = remarks
        if company_name:
            worker.company_name = company_name
        if department_name:
            worker.department_name = department_name
        if duty_id:
            worker.duty_id = duty_id
        if license_plate_number:
            car = db.session.query(Car).filter(
                Car.license_plate_number == license_plate_number).first()
            if not car:
                return -11  # 车辆未找到
            worker.car_id = car.id
            worker.license_plate_number = license_plate_number
        if nickname or duty_id:
            producer.worker_update(
                worker.id, worker.car_id, worker.nickname, worker.duty_id,
                defines.duty[worker.duty_id])
        try:
            d = {'id': worker.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def batch_add_worker(excel_file):
        """工号 姓名 性别 手机号 备注 公司 部门职务 车牌
        """
        db.session.commit()

        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        if cache.get('batch_add_worker'):
            return -10  # 导入工作人员执行中

        cache.set('batch_add_worker', 1)
        cache.expire('batch_add_worker', 300)

        emp_no_list = []
        results = db.session.query(Worker).filter(Worker.status == 1).all()
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

        worker_list = []
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
            worker_list.append(l)
        # 发送消息
        print worker_list
        start = 0
        end = 1000
        send_list = worker_list[start: end]
        while send_list:
            producer.batch_add_worker(send_list)
            send_list = worker_list[start + 1000: end + 1000]
        return {"c": 0, 'msg': ''}