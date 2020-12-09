# coding:utf-8

import time
from datetime import datetime
from collections import defaultdict
from flask import jsonify
from flask.blueprints import Blueprint

from core.framework import make_error_resp, post_require_check, \
    get_require_check, parse_page_size_arg, make_correct_resp, \
    get_require_check_with_user, post_require_check_with_user, \
    get_require_check_with_permissions, post_require_check_with_permissions, \
    form_none_param_with_permissions
from core.AppError import AppError
from utils.tools import gen_token, md5_encrypt, mobile_verify
from utils.defines import SubErrorCode, GlobalErrorCode
from ext import conf

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


@bp.route('/order/list', methods=['GET'])
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
              properties:
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
    school_id = data.get('school_id')
    order_type = data.get('order_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    query_str = data.get('query_str')
    page = data['page']
    size = data['size']
    return OrderService.order_list(school_id, query_str, order_type,
                                   start_date, end_date, page, size)


@bp.route('/order/export', methods=['GET'])
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
    ret = OrderService.order_export(school_id, car_id, order_type,
                                    start_date, end_date)
    if ret == -11:
        raise AppError(*SubErrorCode.ORDER_NUMBER_TOO_BIG)
    if ret == -10:
        raise AppError(*SubErrorCode.ORDER_EXPORTING)
    return {'id': ret}
