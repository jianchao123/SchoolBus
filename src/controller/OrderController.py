# coding:utf-8
from datetime import datetime
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.OrderService import OrderService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('OrderController', __name__)
"""蓝图url前缀"""
url_prefix = '/order'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def order_list(user_id, data):
    """
    订单列表
    订单列表，需要先登录
    ---
    tags:
      - 订单
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: school_id
        in: query
        type: integer
        description: 学校id
      - name: order_type
        in: query
        type: integer
        description: 订单类型 1 上学上车 2上学下车 3 放学上车 4 放学下车
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
        description: 查询串
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
                  stu_no:
                    type: string
                    description: 身份证号
                  stu_name:
                    type: string
                    description: 学生名字
                  school_name:
                    type: string
                    description: 学校名字
                  order_type:
                    type: integer
                    description: 订单类型 1 上学上车 2上学下车 3 放学上车 4 放学下车
                  gps:
                    type: string
                    description: gps
                  license_plate_number:
                    type: string
                    description: 车牌
    """
    school_id = data.get('school_id', None)
    order_type = data.get('order_type', None)
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)
    query_str = data.get('query_str', None)
    page = int(data['page'])
    size = int(data['size'])
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise AppError(*GlobalErrorCode.PARAM_ERROR)
    return OrderService.order_list(school_id, query_str, order_type,
                                   start_date, end_date, page, size)


@bp.route('/export', methods=['POST'])
@post_require_check_with_user([])
def order_export(user_id, data):
    """
    导出乘车记录
    导出乘车记录，需要先登录
    ---
    tags:
      - 订单
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
            school_id:
              type: integer
              description: 学校id
            car_id:
              type: integer
              description: 车辆id
            order_type:
              type: integer
              description: 订单类型
            start_date:
              type: string
              description: 开始日期
            end_date:
              type: string
              description: 结束日期
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
    school_id = data.get('school_id')
    order_type = data.get('order_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    car_id = data.get('car_id')

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise AppError(*GlobalErrorCode.PARAM_ERROR)
    else:
        raise AppError(*GlobalErrorCode.PARAM_ERROR)
    ret = OrderService.order_export(school_id, car_id, order_type,
                                    start_date, end_date)
    if ret == -11:
        raise AppError(*SubErrorCode.ORDER_NUMBER_TOO_BIG)
    if ret == -10:
        raise AppError(*SubErrorCode.ORDER_EXPORTING)
    if ret == -12:
        raise AppError(*SubErrorCode.TASK_NON_RECORD)
    return {'id': ret}


@bp.route('/order_data_bytes', methods=['GET'])
def order_data_bytes():
    """
    订单数据-监控中心
    报警数据，需要先登录
    ---
    tags:
      - 订单
    parameters:
      - name: page
        in: query
        type: integer
        description: 页码
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
                is_display:
                  type: integer
                  description: 是否显示红点 1是 0否
    """
    from flask import request
    d = request.values.to_dict()
    return OrderService.order_data_bytes(d['page'])