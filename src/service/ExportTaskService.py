# coding:utf-8
import xlrd
import time
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Car import Car
from database.ExportTask import ExportTask


class ExportTaskService(object):

    @staticmethod
    def export_task_list(page, size):
        db.session.commit()
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