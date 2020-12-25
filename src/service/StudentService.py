# coding:utf-8
import time
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Student import Student
from database.Face import Face
from database.Car import Car
from database.School import School

from ext import cache
from utils.defines import grade, classes, gender
from msgqueue import producer
import xlrd


class StudentService(object):

    @staticmethod
    def student_list(query_str, school_id, grade_id, class_id, face_status,
                     start_date, end_date, car_id, license_plate_number,
                     page, size):
        """
        学生姓名/身份证号
        """
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Student, Face).join(
            Face, Face.stu_id == Student.id).join(Car, Car.id == Student.car_id)
        if face_status:
            query = query.filter(Face.status == face_status)
        if school_id:
            query = query.filter(Student.school_id == school_id)
        if grade_id:
            query = query.filter(Student.grade_id == grade_id)
        if class_id:
            query = query.filter(Student.class_id == class_id)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(
                Student.nickname.like(query_str),
                Student.stu_no.like(query_str)))
        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(or_(Student.create_time > start_date,
                                     Student.create_time < end_date))
        if car_id:
            query = query.filter(Student.car_id == car_id)
        if license_plate_number:
            query = query.filter(Car.license_plate_number == license_plate_number)

        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            student = row[0]
            face = row[1]

            school = db.session.query(School).filter(
                School.id == student.school_id).first()

            data.append({
                'id': student.id,
                'stu_no': student.stu_no,
                'nickname': student.nickname,
                'gender': student.gender,
                'parents_1': student.parents_1,
                'mobile_1': student.mobile_1,
                'parents_2': student.parents_2,
                'mobile_2': student.mobile_2,
                'address': student.address,
                'remarks': student.remarks,
                'school_id': student.school_id,
                'grade_id': student.grade_id,
                'class_id': student.class_id,
                'create_time': student.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': student.end_time.strftime('%Y-%m-%d'),
                'car_id': student.car_id,
                'license_plate_number': student.license_plate_number,
                'status': student.status,
                'face_status': face.status,
                'school_name': school.school_name,
                'grade_name': grade[student.grade_id],
                'class_name': classes[student.class_id],
                'oss_url': face.oss_url
            })
        return {'results': data, 'count': count}

    @staticmethod
    def student_add(stu_no, nickname, gender, parents_1, mobile_1, parents_2,
                    mobile_2, address, remarks, school_id, grade_id, class_id,
                    end_time, car_id, oss_url):
        """增加学生"""
        db.session.commit()
        car = db.session.query(Car).filter(
            Car.id == car_id).first()
        if not car:
            return -10 # 找不到车辆

        student = db.session.query(Student).filter(
            Student.stu_no == stu_no).first()
        if student:
            return -11 # 身份证号已经存在

        student = Student()
        student.stu_no = stu_no
        student.nickname = nickname
        student.gender = gender
        student.parents_1 = parents_1
        student.mobile_1 = mobile_1
        student.parents_2 = parents_2
        student.mobile_2 = mobile_2
        student.address = address
        student.remarks = remarks
        student.school_id = school_id
        student.grade_id = grade_id
        student.class_id = class_id
        student.create_time = datetime.now()
        student.end_time = end_time
        student.car_id = car.id
        student.license_plate_number = car.license_plate_number
        student.status = 1          # 有效

        try:
            db.session.add(student)
            db.session.flush()
            new_id = student.id
            face = Face()
            face.nickname = nickname
            face.oss_url = oss_url
            if face.oss_url:
                face.status = 2
            else:
                face.status = 1
            face.stu_id = new_id
            face.stu_no = stu_no
            face.end_timestamp = time.mktime(end_time.timetuple())
            db.session.add(face)
            db.session.commit()
            return {'id': new_id}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def student_update(pk,  stu_no, nickname, gender, parents_1, mobile_1,
                       parents_2, mobile_2, address, remarks, school_id,
                       grade_id, class_id, end_time, car_id,
                       oss_url):
        """更新学生
        stu_no 身份证号不能修改
        """
        db.session.commit()

        student = db.session.query(Student).filter(
            Student.id == pk).first()
        if not student:
            return -1  # 未找到学生
        face = db.session.query(Face).filter(
            Face.stu_id == student.id).first()
        if stu_no:
            cnt = db.session.query(Student).filter(
                Student.id != pk, Student.stu_no == stu_no).count()
            if cnt:
                return -12 # 身份证已经存在
            else:
                student.stu_no = stu_no

        if nickname:
            student.nickname = nickname
            face.nickname = nickname

        if gender:
            student.gender = gender
        if parents_1:
            student.parents_1 = parents_1
        if mobile_1:
            student.mobile_1 = mobile_1
            # 清除open_id
            if student.mobile_1 != mobile_1:
                student.open_id_1 = None

        if parents_2:
            student.parents_2 = parents_2
        if mobile_2:
            student.mobile_2 = mobile_2
            # 清除open_id
            if student.mobile_2 != mobile_2:
                student.open_id_2 = None

        if address:
            student.address = address
        if remarks:
            student.remarks = remarks
        if school_id:
            student.school_id = school_id
        if grade_id:
            student.grade_id = grade_id
        if class_id:
            student.class_id = class_id

        if car_id:
            if car_id == -10:
                student.car_id = None
                student.license_plate_number = None
            else:
                car = db.session.query(Car).filter(
                    Car.id == car_id).first()
                if not car:
                    return -11  # 找不到车辆
                student.car_id = car.id
                student.license_plate_number = car.license_plate_number
        if oss_url:
            face.oss_url = oss_url
            face.status = 2     # 未处理
            print oss_url
            print "====================="

        if end_time:
            student.end_time = end_time
            face.end_timestamp = time.mktime(end_time.timetuple())
        try:
            d = {'id': student.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def batch_add_student(excel_file):
        db.session.commit()

        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        stu_no_list = []
        results = db.session.query(Student).filter(Student.status == 1).all()
        for row in results:
            stu_no_list.append(row.stu_no)

        # 查询所有学校
        school_dict = {}
        results = db.session.query(School).all()
        for row in results:
            school_dict[row.school_name] = row.id

        # 查询所有车辆
        car_dict = {}
        results = db.session.query(Car).filter(Car.status == 1).all()
        for row in results:
            car_dict[row.license_plate_number] = row.id
        print car_dict
        error_msg_list = []
        for index in range(1, table.nrows):
            is_err = 0

            row_data = table.row_values(index)
            stu_no = str(row_data[0]).strip()
            nickname = str(row_data[1]).strip()
            gender_name = str(row_data[2]).strip()
            parents_1 = str(row_data[3]).strip()
            mobile_1 = str(row_data[4]).strip()
            parents_2 = str(row_data[5]).strip()
            mobile_2 = str(row_data[6]).strip()
            address = str(row_data[7]).strip()
            remarks = str(row_data[8]).strip()
            school_name = str(row_data[9]).strip()
            grade_name = str(row_data[10]).strip()
            class_name = str(row_data[11]).strip()
            end_time = str(row_data[12]).strip()
            license_plate_number = str(row_data[13]).strip()

            err_str = u"\n第{}行,".format(index + 1)
            # 先检查是否为空
            if not stu_no:
                err_str += u"身份证为空,"
                is_err = 1
            if not nickname:
                err_str += u"姓名为空,"
                is_err = 1
            if not gender_name:
                err_str += u"性别为空,"
                is_err = 1
            if not parents_1:
                err_str += u"家长1名字为空,"
                is_err = 1
            if not mobile_1:
                err_str += u"家长1手机号为空,"
                is_err = 1
            if not parents_2:
                err_str += u"家长2名字为空,"
                is_err = 1
            if not mobile_2:
                err_str += u"家长2手机号为空,"
                is_err = 1
            if not address:
                err_str += u"地址为空,"
                is_err = 1
            if not remarks:
                err_str += u"备注为空,"
                is_err = 1
            if not school_name:
                err_str += u"学校为空,"
                is_err = 1
            if not grade_name:
                err_str += u"年纪为空,"
                is_err = 1
            if not class_name:
                err_str += u"班级为空,"
                is_err = 1
            if not end_time:
                err_str += u"截至日期为空,"
                is_err = 1
            if not license_plate_number:
                err_str += u"车牌号为空,"
                is_err = 1

            # 检查格式
            if gender_name not in gender:
                err_str += u"性别只有'男'或'女'"
                is_err = 1
            if school_name not in school_dict.keys():
                err_str += u"未知的学校名字"
                is_err = 1
            if grade_name not in grade:
                err_str += u"未知的年纪名字"
                is_err = 1
            if class_name not in classes:
                err_str += u"未知的班级名字"
                is_err = 1
            print license_plate_number
            if license_plate_number.decode('utf8') not in car_dict:
                err_str += u"未知的车牌"
                is_err = 1

            if end_time:
                try:
                    datetime.strptime(end_time, '%Y-%m-%d')
                except ValueError:
                    err_str += u"有效期格式错误"
                    is_err = 1
                except:
                    err_str += u"不支持公式"
                    is_err = 1
            # 检查重复
            if stu_no in stu_no_list:
                err_str += u"工号{}重复".format(stu_no)
                is_err = 1
            else:
                stu_no_list.append(stu_no)

            if err_str:
                err_str += "\n"

            if is_err:
                error_msg_list.append(err_str)
        if error_msg_list:
            return {"c": 1, "msg": "\n".join(error_msg_list)}

        if cache.get('batch_add_student'):
            return -10  # 导入学生任务执行中

        cache.set('batch_add_student', 1)
        cache.expire('batch_add_student', 300)

        print grade, classes
        student_list = []
        for index in range(1, table.nrows):
            row_data = table.row_values(index)
            stu_no = str(row_data[0]).strip()
            nickname = str(row_data[1]).strip()
            gender_name = str(row_data[2]).strip()
            parents_1 = str(row_data[3]).strip()
            mobile_1 = str(row_data[4]).strip()
            parents_2 = str(row_data[5]).strip()
            mobile_2 = str(row_data[6]).strip()
            address = str(row_data[7]).strip()
            remarks = str(row_data[8]).strip()
            school_name = str(row_data[9]).strip()
            grade_name = str(row_data[10]).strip()
            class_name = str(row_data[11]).strip()
            end_time = str(row_data[12]).strip()
            license_plate_number = str(row_data[13]).strip()

            student_list.append([
                stu_no, nickname, gender.index(gender_name), parents_1, mobile_1,
                parents_2, mobile_2, address, remarks,
                school_dict[school_name.decode('utf8')],
                grade.index(grade_name.decode('utf8')),
                classes.index(class_name.decode('utf8')), end_time,
                car_dict[license_plate_number.decode('utf8')],
                license_plate_number])
        # 发送消息
        print student_list
        start = 0
        end = 1000
        send_list = student_list[start: end]
        while send_list:
            producer.batch_add_student(send_list)
            send_list = student_list[start + 1000: end + 1000]
        return {"c": 0, 'msg': ''}
