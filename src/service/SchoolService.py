# coding:utf-8
import xlrd
import sys
import json
import inspect
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.School import School
from msgqueue import producer
from ext import cache
from utils.defines import RedisKey
from utils.tools import get_frame_name_param


class SchoolService(object):

    @staticmethod
    def school_list(school_name, page, size):
        """
        """
        db.session.commit() # SELECT
        offset = (page - 1) * size
        query = db.session.query(School)
        query = query.filter(School.status != 10)
        if school_name:
            query_str = '%{keyword}%'.format(keyword=school_name)
            query = query.filter(School.school_name.like(query_str))

        count = query.count()
        results = query.order_by(School.id.desc()).offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'school_name': row.school_name
            })
        return {'results': data, 'count': count}

    @staticmethod
    def school_add(school_name, user_id):
        db.session.commit() # SELECT
        cnt = db.session.query(School).filter(
            School.school_name == school_name).count()
        if cnt:
            return -10  # 学校名字已存在
        school = School()
        school.school_name = school_name
        school.status = 1
        try:
            db.session.add(school)
            db.session.flush()
            new_id = school.id
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
    def school_update(pk, school_name, user_id):
        """
        """
        db.session.commit() # SELECT
        school = db.session.query(School).filter(
            School.id == pk).first()
        if not school:
            return -1
        cache.hdel(RedisKey.CACHE_SCHOOL_NAME_DATA, str(school.id))
        if school_name:
            cnt = db.session.query(School).filter(
                School.id != pk, School.school_name == school_name).count()
            if cnt:
                return -10  # 学校名字已存在
            school.school_name = school_name
        try:
            d = {'id': school.id}
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
    def batch_add_school(excel_file):
        """
        """
        db.session.commit() # SELECT
        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        name_list = []
        results = db.session.query(School).filter(School.status == 1).all()
        for row in results:
            name_list.append(row.school_name)

        error_msg_list = []
        for index in range(1, table.nrows):
            is_err = 0

            row_data = table.row_values(index)
            school_name = str(row_data[0]).strip()

            err_str = u"\n第{}行,".format(index + 1)
            # 先检查是否为空
            if not school_name:
                err_str += u"学校名字为空,"
                is_err = 1

            # 检查重复
            if school_name in name_list:
                err_str += u"学校名字{}重复".format(school_name)
                is_err = 1
            else:
                name_list.append(school_name)

            if err_str:
                err_str += "\n"

            if is_err:
                error_msg_list.append(err_str)
        if error_msg_list:
            return {"c": 1, "msg": "\n".join(error_msg_list)}

        if cache.get('batch_add_school'):
            return -10  # 导入车辆执行中

        cache.set('batch_add_school', 1)
        cache.expire('batch_add_school', 50)

        school_list = []
        for index in range(1, table.nrows):
            row_data = table.row_values(index)
            school_name = str(row_data[0]).strip()
            school_list.append([school_name])
        # 发送消息
        producer.batch_add_school(school_list)
        return {"c": 0, 'msg': ''}
