# coding:utf-8
import oss2
import random
from urllib2 import urlopen
import time
import json
import xlrd
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Order import Order
from utils import defines
from utils import tools
from ext import cache


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
            query = query.filter(or_(Order.stu_name.like(query_str),
                Order.passenger_name.like(query_str)))
        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(or_(Order.create_time > start_date,
                                     Order.create_time < end_date))
        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'stu_no': row.stu_no,
                'stu_id': row.stu_id,
                'stu_name': row.stu_name,
                'school_id': row.school_id,
                'school_name': row.school_name,
                'order_type': row.order_type,
                'create_time': row.create_time,
                'up_location': row.up_location,
                'gps': row.gps,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number,
                'device_id': row.device_id
            })
        return {'results': data, 'count': count}

    @staticmethod
    def order_download(workbook, school_id, query_str, order_type,
                       start_date, end_date):
        """
           'id': row.id,
            'stu_no': row.stu_no,
            'stu_id': row.stu_id,
            'stu_name': row.stu_name,
            'school_id': row.school_id,
            'school_name': row.school_name,
            'order_type': row.order_type,
            'create_time': row.create_time,
            'up_location': row.up_location,
            'gps': row.gps,
            'car_id': row.car_id,
            'license_plate_number': row.license_plate_number,
            'device_id': row.device_id

        """
        db.session.commit()
        from sqlalchemy import or_, func
        query = db.session.query(Order)
        if school_id:
            query = query.filter(Order.school_id == school_id)
        if start_date and end_date:
            query = query.filter(Order.create_time.between(
                start_date, end_date + timedelta(days=1)))
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(Order.stu_name.like(query_str),
                                     Order.passenger_name.like(query_str)))
        if order_type:
            query = query.filter(Order.order_type == order_type)

        queryset = query.order_by(Order.id.desc()).all()
        data = []
        for row in queryset:
            if row.order_type == 1:
                order_type_str = u"上学上车"
            elif row.order_type == 2:
                order_type_str = u"2上学下车"
            elif row.order_type == 3:
                order_type_str = u"放学上车"
            elif row.order_type == 4:
                order_type_str = u"放学下车"

            data.append([row.stu_no, row.stu_name, row.school_name,
                         order_type_str, row.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                         row.license_plate_number, row.up_location])

        start = 0
        step = 50000
        fields = [u"学号", u"姓名", u"学校", u"乘车记录类型", u"乘车时间",
                  u"乘坐车辆", u"gps位置"]
        while True:
            d = data[start: step]
            if d:
                sheet = workbook.add_worksheet(
                    '{}-{}条'.format(start, start + step))
                sheet.write_row('A1', fields)
                length = len(d)
                for x in range(length):
                    for y in range(9):
                        sheet.write(x + 1, y, d[x][y])
            else:
                break
            start += 50000