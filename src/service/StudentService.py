# coding:utf-8
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Student import Student
from database.Face import Face


class StudentService(object):

    @staticmethod
    def student_list(query_str, school_id, grade_id, class_id, face_status,
                     start_date, end_date, page, size):
        """
        学生姓名/身份证号
        """
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Student).join(Face, Face.stu_id == Student.id)
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
        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'stu_no': row.stu_no,
                'nickname': row.nickname,
                'gender': row.gender,
                'parents_1': row.parents_1,
                'mobile_1': row.mobile_1,
                'parents_2': row.parents_2,
                'mobile_2': row.mobile_2,
                'address': row.address,
                'remarks': row.remarks,
                'school_id': row.school_id,
                'grade_id': row.grade_id,
                'class_id': row.class_id,
                'create_time': row.create_time,
                'end_time': row.end_time,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number,
                'status': row.status
            })
        return {'results': data, 'count': count}


