# coding:utf-8
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user

from service.ExportTaskService import ExportTaskService
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('ExportTaskController', __name__)
"""蓝图url前缀"""
url_prefix = '/export_task'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def export_task_list(user_id, data):
    """
    导出任务列表
    导出任务列表，需要先登录
    ---
    tags:
      - 导出任务
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: page
        in: query
        type: integer
        description: 页码
      - name: size
        in: query
        type: integer
        description: 每页数量
    responses:
      200:
        description: 正常返回http code 200
        schema:
          properties:
            msg:
              type: string
              description: 错误消息
            status:
              type: integer
              description: 状态
            data:
              type: array
              items:
                properties:
                  id:
                    type: integer
                    description: PK
                  status:
                    type: integer
                    description: 状态1处理中 2已完成 10删除
                  task_name:
                    type: string
                    description: 导出任务名字
                  zip_url:
                    type: string
                    description: zip url
                  task_type:
                    type: integer
                    description: 公司名字 1乘车记录 2报警记录
                  create_time:
                    type: string
                    description: 时间

    """
    page = int(data['page'])
    size = int(data['size'])
    return ExportTaskService.export_task_list(page, size)


@bp.route('/delete', methods=['POST'])
@post_require_check_with_user(['task_ids'])
def export_task_delete(user_id, data):
    """
    删除导出任务
    删除导出任务，需要先登录
    ---
    tags:
      - 导出任务
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: body
        in: body
        required: true
        schema:
          properties:
            task_ids:
              type: string
              description: 任务ids 逗号分割 1,2,3,4
    responses:
      200:
        description: 正常返回http code 200
        schema:
          properties:
            msg:
              type: string
              description: 错误消息
            status:
              type: integer
              description: 状态
            data:
              type: object
              properties:
                id:
                  type: integer
                  description: 0表示删除成功
    """
    task_ids = data['task_ids']
    ret = ExportTaskService.export_task_delete(task_ids)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    return ret