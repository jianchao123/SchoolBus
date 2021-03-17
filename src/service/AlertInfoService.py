# coding:utf-8
import time
import struct
import zlib
import base64
from datetime import timedelta
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.AlertInfo import AlertInfo
from database.ExportTask import ExportTask
from ext import cache


class AlertInfoService(object):

    @staticmethod
    def alert_info_list(query_str, status, start_time, end_time,
                        first_alert, second_alert, page, size):
        """
        车牌/家使用/照管员 status start_time end_time first_alert second_alert
        """
        db.session.commit() # SELECT

        offset = (page - 1) * size
        query = db.session.query(AlertInfo)
        if status:
            query = query.filter(AlertInfo.status == status)
        if not (first_alert and second_alert):
            if first_alert:
                query = query.filter(AlertInfo.first_alert == 1).filter(
                    AlertInfo.second_alert == 0)
            if second_alert:
                query = query.filter(AlertInfo.second_alert == 1)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(
                AlertInfo.license_plate_number.like(query_str),
                AlertInfo.worker_name_1.like(query_str),
                AlertInfo.worker_name_2.like(query_str)))
        if start_time and end_time:
            end_time += timedelta(days=1)
            print end_time
            query = query.filter(and_(AlertInfo.alert_start_time > start_time,
                                      AlertInfo.alert_start_time < end_time))
        count = query.count()
        query = query.order_by(AlertInfo.id.desc())
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            alert_start_time_str = ''
            if row.alert_start_time:
                alert_start_time_str = \
                    row.alert_start_time.strftime('%Y-%m-%d %H:%M:%S')
            alert_second_time_str = ''
            if row.alert_second_time:
                alert_second_time_str = \
                    row.alert_second_time.strftime('%Y-%m-%d %H:%M:%S')
            cancel_time_str = None
            if row.cancel_time:
                cancel_time_str = row.cancel_time.strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                'id': row.id,
                'license_plate_number': row.license_plate_number,
                'worker_name_1': row.worker_name_1,
                'worker_name_2': row.worker_name_2,
                'company_name': row.company_name,
                'people_number': row.people_number,
                'people_info': row.people_info,
                'first_alert': row.first_alert,
                'second_alert': row.second_alert,
                'alert_start_time': alert_start_time_str,
                'alert_second_time': alert_second_time_str,
                'alert_location': row.gps,
                'status': row.status,
                'cancel_worker_name': row.cancel_worker_name,
                'cancel_type_id': row.cancel_type_id,
                'cancel_time': cancel_time_str,
                'cancel_reason': row.cancel_reason
            })
        cnt = db.session.query(AlertInfo).count()
        cache.hset('QUERY_CNT_ALARM', 'cnt', cnt)
        return {'results': data, 'count': count}

    @staticmethod
    def alert_info_export(status, start_date, end_date,
                          alert_info_type, car_id):
        """
        导出报警记录
        alert_info_type 1一次报警 2二次报警
        """
        db.session.commit() # SELECT
        from msgqueue.producer import export_alert_info_msg

        # 处理中的乘车记录
        cnt = db.session.query(ExportTask).filter(
            ExportTask.status == 1, ExportTask.task_type == 1).count()
        if cnt:
            return -10

        # 检查导出的条数
        query = db.session.query(AlertInfo)
        if status:
            query = query.filter(AlertInfo.status == int(status))
        if car_id:
            query = query.filter(AlertInfo.car_id == int(car_id))
        if alert_info_type:
            alert_info_type = int(alert_info_type)
            if alert_info_type == 1:
                query = query.filter(AlertInfo.first_alert == 1,
                                     AlertInfo.second_alert == 0)
            elif alert_info_type == 2:
                query = query.filter(AlertInfo.second_alert == 1)

        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(and_(AlertInfo.alert_start_time > start_date,
                                      AlertInfo.alert_start_time < end_date))
        count = query.count()
        if not count:
            return -12
        if count > 15000000:
            return -11

        et = ExportTask()
        et.status = 1
        et.task_name = u"报警记录{}-{}".format(start_date, end_date)
        et.task_type = 2
        try:
            db.session.add(et)
            db.session.flush()
            new_id = et.id
            db.session.commit()
            export_alert_info_msg(status, start_date.strftime('%Y-%m-%d'),
                                  end_date.strftime('%Y-%m-%d'),
                                  alert_info_type, car_id, new_id)
            return new_id
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def is_display():
        db.session.commit() # SELECT
        cnt = db.session.query(AlertInfo).count()
        query_cnt = cache.hget('QUERY_CNT_ALARM', 'cnt')
        if int(query_cnt) < cnt:
            return 1
        return 0

    @staticmethod
    def data_centre_query(page):
        """
        1 - 9999999
        车辆 驾驶员 照管员 公司 遗漏人数 遗漏学生 首次报警开始时间 二次报警开始时间 报警状态 gps位置 报警解除人员 报警解除时间 报警解除理由

             # id: 4字节
            # 报警人数 1字节
            # 报警次数 1字节
            # 报警状态 1字节
            # 第一次报警时间戳 4字节
            # 后续的车牌数据字节数 1字节
            # 车牌 N字节
            # 驾驶员数据字节数 1字节
            # 驾驶员名字 N字节
            # 照管员数据字节数 1字节
            # 照管员名字 N字节
            # 公司名字字节数 1字节
            # 公司名字 N字节
            # 报警学生数据字节数 1字节
            # 报警学生数据 N字节
            # gps字节数 1字节
            # gps N字节
            # 第二次报警时间戳字节数 1字节
            # 第二次报警时间戳
            # 取消报警人的名字字节数 1字节
            # 取消报警人的名字
            # 取消报警理由字节数 1字节
            # 取消报警理由
            # 取消报警时间字节数 1字节
            # 取消报警时间
        """
        final_string = ""
        offset = (int(page) - 1) * 100
        results = db.session.query(AlertInfo).order_by(
            AlertInfo.id.desc()).offset(offset).limit(100).all()
        for row in results:
            alarm_cnt = 1
            if row.second_alert:
                alarm_cnt = 2

            string = struct.pack('!i', row.id) + \
            struct.pack('!b', row.people_number) + \
            struct.pack('!b', alarm_cnt) + \
            struct.pack('!b', row.status) + \
            struct.pack('!i', time.mktime(row.alert_start_time.timetuple())) + \
            struct.pack('!b', len(row.license_plate_number.encode('utf8'))) + \
            row.license_plate_number.encode('utf8') + \
            struct.pack('!b', len(row.worker_name_1.encode('utf8'))) + \
            row.worker_name_1.encode('utf8') + \
            struct.pack('!b', len(row.worker_name_2.encode('utf8'))) + \
            row.worker_name_2.encode('utf8') + \
            struct.pack('!b', len(row.company_name.encode('utf8'))) + \
            row.company_name.encode('utf8') + \
            struct.pack('!b', len(row.people_info.encode('utf8'))) + \
            row.people_info.encode('utf8') + \
            struct.pack('!b', len(row.gps.encode('utf8'))) + row.gps.encode('utf8')
            if row.alert_second_time:
                alarm_second_timestamp = int(time.mktime(row.alert_second_time.timetuple()))
                print alarm_second_timestamp, len(struct.pack('!i', alarm_second_timestamp))
                string += (struct.pack('!b', 4) + struct.pack('!i', alarm_second_timestamp))
            else:
                string += struct.pack('!b', 0)

            if row.cancel_worker_name:
                string += struct.pack('!b', len(row.cancel_worker_name.encode('utf8')))
                string += row.cancel_worker_name.encode('utf8')
            else:
                string += struct.pack('!b', 0)
            if row.cancel_reason:
                string += struct.pack('!b', len(row.cancel_reason.encode('utf8')))
                string += row.cancel_reason.encode('utf8')
            else:
                string += struct.pack('!b', 0)
            if row.cancel_time:
                cancel_timestamp = time.mktime(
                    row.cancel_time.timetuple())
                string += (struct.pack('!b', 4) + struct.pack('!i', cancel_timestamp))
            else:
                string += struct.pack('!b', 0)
            final_string += string
        if final_string:
            crc_code = zlib.crc32(final_string) & 0xffffffff
            return base64.b64encode(struct.pack('!q', crc_code) + final_string)
        return ""
