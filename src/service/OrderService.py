# coding:utf-8
from datetime import timedelta

from sqlalchemy import func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Order import Order
from database.ExportTask import ExportTask
from ext import conf


class OrderService(object):

    @staticmethod
    def order_list(school_id, query_str, order_type,
                   start_date, end_date, page, size):
        db.session.commit()
        offset = (page - 1) * size
        query = db.session.query(Order)
        if school_id:
            query = query.filter(Order.school_id == school_id)
        if order_type:
            query = query.filter(Order.order_type == order_type)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(
                Order.stu_name.like(query_str),
                Order.license_plate_number.like(query_str)))
        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(and_(Order.create_time > start_date,
                                      Order.create_time < end_date))

        query = query.order_by(Order.id.desc())
        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            oss_url = 'https://' + conf.config['OSS_BUCKET'] + '.' + \
                      conf.config['OSS_POINT'] + '/snap_{}_{}.jpg'.format(
                row.fid, row.cur_timestamp)
            data.append({
                'id': row.id,
                'stu_no': row.stu_no,
                'stu_id': row.stu_id,
                'stu_name': row.stu_name,
                'school_id': row.school_id,
                'school_name': row.school_name,
                'order_type': row.order_type,
                'create_time': row.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'up_location': row.up_location,
                'gps': row.gps,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number,
                'device_id': row.device_id,
                'oss_url': oss_url
            })
        return {'results': data, 'count': count}

    @staticmethod
    def order_export(school_id, car_id, order_type,
                     start_date, end_date):
        """
        订单导出
        """
        db.session.commit()
        from msgqueue.producer import export_order_excel_msg

        # 处理中的乘车记录
        cnt = db.session.query(ExportTask).filter(
            ExportTask.status == 1, ExportTask.task_type == 1).count()
        if cnt:
            return -10

        # 检查导出的条数
        query = db.session.query(Order)
        if school_id:
            query = query.filter(Order.school_id == school_id)
        if car_id:
            query = query.filter(Order.car_id == car_id)
        if order_type:
            query = query.filter(Order.order_type == order_type)
        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(and_(Order.create_time > start_date,
                                     Order.create_time < end_date))
        count = query.count()
        if not count:
            return -12
        if count > 15000000:
            return -11

        et = ExportTask()
        et.status = 1
        et.task_name = u"乘车记录{}-{}".format(start_date, end_date)
        et.task_type = 1
        try:
            db.session.add(et)
            db.session.flush()
            new_id = et.id
            db.session.commit()
            export_order_excel_msg(school_id, car_id, order_type,
                                   start_date.strftime('%Y-%m-%d'),
                                   end_date.strftime('%Y-%m-%d'), new_id)
            return new_id
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def order_data_bytes(page):
        """
        乘车记录类型 身份证 学生姓名 学校 乘车时间 乘坐车辆 gps
        :param page:
        :return:
        """
        import zlib
        import struct
        import base64
        offset = (int(page) - 1) * 1000
        results = db.session.query(Order).order_by(
            Order.id.desc()).offset(offset).limit(1000).all()
        final_string = ""
        for row in results:
            stuno = row.stu_no.encode('utf8')
            stuname = row.stu_name.encode('utf8')
            schoolname = row.school_name.encode('utf8')
            takebustime = int(row.cur_timestamp)
            chepai = row.license_plate_number.encode('utf8')

            final_string += struct.pack('!i', row.id)
            final_string += struct.pack('!b', row.order_type)
            final_string += struct.pack('!b', len(stuno))
            final_string += stuno
            final_string += struct.pack('!b', len(stuname))
            final_string += stuname
            final_string += struct.pack('!b', len(schoolname))
            final_string += schoolname
            final_string += struct.pack('!b', 4)
            final_string += struct.pack('!i', takebustime)
            final_string += struct.pack('!b', len(chepai))
            final_string += chepai
            if row.gps:
                gps = row.gps.encode('utf8')
                final_string += struct.pack('!b', len(gps))
                final_string += gps
            else:
                final_string += struct.pack('!b', 0)
        if final_string:
            crc_code = zlib.crc32(final_string) & 0xffffffff
            raw_str = struct.pack('!q', crc_code) + final_string
            return base64.b64encode(raw_str)
        return ""
