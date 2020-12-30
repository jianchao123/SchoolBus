# coding:utf-8
from datetime import datetime
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.AlertInfoService import AlertInfoService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('AlertInfoController', __name__)
"""蓝图url前缀"""
url_prefix = '/alert_info'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def alert_info_list(user_id, data):
    """
    报警信息列表
    报警信息列表，需要先登录
    ---
    tags:
      - 报警
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: status
        in: query
        type: integer
        description: 状态1 正在报警  2 已解除
      - name: start_date
        in: query
        type: string
        description: 开始日期
      - name: end_date
        in: query
        type: string
        description: 结束日期
      - name: query_str
        in: query
        type: string
        description: 学生名字/乘坐车辆车牌
      - name: first_alert
        in: query
        type: integer
        description: 可空,  1第一次提醒
      - name: second_alert
        in: query
        type: integer
        description: 可空, 1第二次提醒
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
                  license_plate_number:
                    type: string
                    description: 车牌
                  worker_name_1:
                    type: string
                    description: 驾驶员
                  worker_name_2:
                    type: stirng
                    description: 照顾员
                  company_name:
                    type: string
                    description: 公司名字
                  people_number:
                    type: string
                    description: 遗漏人数
                  people_info:
                    type: string
                    description: 遗漏人员信息
                  first_alert:
                    type: string
                    description: 第一次提醒 1已提醒 0没有
                  second_alert:
                    type: string
                    description: 第二次提醒
                  alert_start_time:
                    type: string
                    description: 第一次提醒时间
                  alert_second_time:
                    type: string
                    description: 第二次提醒时间
                  alert_location:
                    type: string
                    description: gps
                  status:
                    type: string
                    description: 状态1 正在报警  2 已解除

    """
    status = data.get('status', None)
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)
    query_str = data.get('query_str', None)
    first_alert = data.get('first_alert', None)
    second_alert = data.get('second_alert', None)
    page = int(data['page'])
    size = int(data['size'])

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            import traceback
            print traceback.format_exc()
            raise AppError(*GlobalErrorCode.PARAM_ERROR)

    return AlertInfoService.alert_info_list(
        query_str, status, start_date, end_date, first_alert,
        second_alert, page, size)


@bp.route('/export', methods=['POST'])
@post_require_check_with_user([])
def alert_info_export(user_id, data):
    """
    导出报警记录
    导出报警记录，需要先登录
    ---
    tags:
      - 报警
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
            car_id:
              type: integer
              description: 车辆id
            alert_info_type:
              type: integer
              description: 订单类型 1一次报警 2两次报警
            start_date:
              type: string
              description: 开始日期
            end_date:
              type: string
              description: 结束日期
            status:
              type: integer
              description: 1 正在报警 2已解除
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
                  description: 新增的task_id
    """
    status = data.get('status', None)
    alert_info_type = data.get('alert_info_type', None)
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)
    car_id = data.get('car_id', None)
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise AppError(*GlobalErrorCode.PARAM_ERROR)
        
    ret = AlertInfoService.alert_info_export(status, start_date, end_date,
                                             alert_info_type, car_id)
    if ret == -11:
        raise AppError(*SubErrorCode.ORDER_NUMBER_TOO_BIG)
    if ret == -10:
        raise AppError(*SubErrorCode.ORDER_EXPORTING)
    return {'id': ret}
