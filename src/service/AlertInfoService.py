# coding:utf-8

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
        print "======================="
        print count
        print start_date, end_date
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
        cnt = db.session.query(AlertInfo).count()
        query_cnt = cache.hget('QUERY_CNT_ALARM', 'cnt')
        if query_cnt < cnt:
            return 1
        return 0
