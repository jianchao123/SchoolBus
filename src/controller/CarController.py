# coding:utf-8
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user, form_none_param_with_permissions
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.CarService import CarService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('CarController', __name__)
"""蓝图url前缀"""
url_prefix = '/car'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def car_list(user_id, data):
    """
    车辆列表
    车辆列表，需要先登录
    ---
    tags:
      - 车辆
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: query_str
        in: query
        type: string
        description: 车牌/设备Id
      - name: is_online
        in: query
        type: integer
        description: 是否在线 1上线 2下线
      - name: scheduling
        in: query
        type: integer
        description: 是否排班 1是 2否
      - name: status
        in: query
        type: integer
        description: 状态 1已绑定 2未绑定
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
                  worker_1_id:
                    type: integer
                    description: 车辆id
                  worker_1_nickname:
                    type: string
                    description: 工作人员名字
                  worker_1_duty_name:
                    type: string
                    description: 工作人员职务名字
                  company_name:
                    type: string
                    description: 公司名字
                  capacity:
                    type: integer
                    description: 载客量
                  device_iid:
                    type: string
                    description: 设备标签id
                  license_plate_number:
                    type: string
                    description: 车牌
                  status:
                    type: integer
                    description: 1有效 10删除

    """
    query_str = data.get('query_str', None)
    is_online = data.get('is_online', None)
    status = data.get('status', None)
    page = int(data['page'])
    size = int(data['size'])
    scheduling = data.get('scheduling', None)
    return CarService.car_list(query_str, is_online, scheduling, status, page, size)


@bp.route('/add', methods=['POST'])
@post_require_check_with_user([])
def car_add(user_id, data):
    """
    添加车辆
    添加车辆，需要先登录
    ---
    tags:
      - 车辆
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
            company_name:
              type: string
              description: 公司名字
            capacity:
              type: integer
              description: 载客量
            license_plate_number:
              type: string
              description: 车牌号
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
                  description: 新增的车辆Id

    """
    company_name = data['company_name']
    capacity = data['capacity']
    license_plate_number = data['license_plate_number']
    license_plate_number = license_plate_number.upper()
    ret = CarService.car_add(license_plate_number, capacity, company_name, user_id)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.CAR_CHEPAI_ALREADY_EXISTS)
    return ret


@bp.route('/update/<int:pk>', methods=['POST'])
@post_require_check_with_user([])
def car_update(user_id, data, pk):
    """
    编辑车辆
    编辑车辆，需要先登录
    ---
    tags:
      - 车辆
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
            company_name:
              type: string
              description: 公司名字
            capacity:
              type: integer
              description: 载客量
            license_plate_number:
              type: integer
              description: 车牌号
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
                  description: 新增的车辆Id

    """
    company_name = data.get('company_name', None)
    capacity = data.get('capacity', None)
    license_plate_number = data.get('license_plate_number', None)

    if license_plate_number:
        license_plate_number = license_plate_number.upper()

    ret = CarService.car_update(pk, license_plate_number, capacity, company_name, user_id)
    if ret == -1:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.CAR_CHEPAI_ALREADY_EXISTS)
    return ret


@bp.route('/delete', methods=['POST'])
@post_require_check_with_user([])
def car_delete(user_id, data):
    """
    删除车辆
    删除车辆，需要先登录
    ---
    tags:
      - 车辆
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
            car_ids:
              type: string
              description: 车辆id串 例1,2,3,4
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
                  description: 新Id
    """
    car_ids = data['car_ids']
    ret = CarService.delete_cars(car_ids, user_id)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    elif ret == -10:
        raise AppError(*SubErrorCode.CAR_BOUNDING_TO_STUDENT)
    elif ret == -11:
        raise AppError(*SubErrorCode.CAR_BOUNDING_TO_DEVICE)
    elif ret == -12:
        raise AppError(*SubErrorCode.CAR_BOUNDING_TO_WORKER)


@bp.route('/batchadd', methods=['POST'])
@form_none_param_with_permissions()
def car_batch_add(user_id, data):
    """
    批量添加车辆
    批量添加车辆，需要先登录
    ---
    tags:
      - 车辆
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: fd
        in: formData
        type: file
        required: true
        description: excel文件
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
                c:
                  type: integer
                  description: 1错误 0正常
                msg:
                  type: string
                  description: 错误信息,需要显示给用户
    """
    from flask import request

    fd = request.files['fd']

    # "c": 1, "msg": err_str}
    data = CarService.batch_add_car(fd)
    if data == -10:
        raise AppError(*SubErrorCode.TASK_EXECUTING)
    return data


@bp.route('/names', methods=['GET'])
@get_require_check_with_user([])
def car_names(user_id, data):
    """
    车辆名字列表
    车辆名字列表，需要先登录
    ---
    tags:
      - 车辆名字列表
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
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
                  name:
                    type: string
                    description: 名字

    """
    return CarService.car_name_list()