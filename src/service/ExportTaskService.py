# coding:utf-8
import sys
import json
import inspect
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.ExportTask import ExportTask
from msgqueue import producer
from utils.tools import get_frame_name_param


class ExportTaskService(object):

    @staticmethod
    def export_task_list(page, size):
        db.session.commit() # SELECT
        offset = (page - 1) * size
        query = db.session.query(ExportTask).filter(ExportTask.status != 10)
        count = query.count()
        query = query.order_by(ExportTask.id.desc())
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'status': row.status,
                'task_name': row.task_name,
                'zip_url': row.zip_url,
                'task_type': row.task_type,
                'create_time': row.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        return {'count': count, 'results': data}

    @staticmethod
    def export_task_delete(task_ids, user_id):
        """删除导出任务"""
        db.session.commit() # SELECT
        task_id_list = [int(row) for row in task_ids.split(",")]
        results = db.session.query(ExportTask).filter(
            ExportTask.id.in_(task_id_list)).all()
        print results
        for row in results:
            if row.status == 2:
                row.status = 10
            else:
                return -10

        try:
            db.session.commit()

            # 日志
            func_name, func_param = get_frame_name_param(inspect.currentframe())
            producer.operation_log(func_name, func_param, user_id)
            return {'id': 0}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()
