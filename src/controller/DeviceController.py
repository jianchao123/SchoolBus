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

from service.DeviceService import DeviceService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('DeviceController', __name__)
"""蓝图url前缀"""
url_prefix = '/device'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def device_list(user_id, data):
    """
    设备列表
    设备列表，需要先登录
    ---
    tags:
      - 设备
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: device_iid
        in: query
        type: string
        description: 设备Id
      - name: license_plate_number
        in: query
        type: string
        description: 车牌号
      - name: status
        in: query
        type: integer
        description: 状态 1在线 2离线
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
                  device_name:
                    type: string
                    description: 设备名字
                  device_iid:
                    type: string
                    description: 设备ID
                  imei:
                    type: string
                    description: IMEI
                  car_id:
                    type: string
                    description: 车辆id
                  license_plate_number:
                    type: string
                    description: 车牌号
                  status:
                    type: integer
                    description: 状态id 1已创建虚拟设备 2已关联车辆 3已设置工作模式 4已设置oss信息 5已初始化人员
                  sound_volume:
                    type: string
                    description: 设备音量
                  device_type:
                    type: integer
                    description: 设备类型 1刷脸 2生成特征值
                  mac:
                    type: string
                    description: MAC
                  is_online:
                    type: string
                    description: 是否在线
    """
    device_iid = data.get('device_iid', None)
    license_plate_number = data.get('license_plate_number', None)
    status = data.get('status', None)
    page = int(data['page'])
    size = int(data['size'])
    return DeviceService.device_list(device_iid, license_plate_number,
                                     status, page, size)


@bp.route('/update/<int:pk>', methods=['POST'])
@post_require_check_with_user([])
def device_update(user_id, data, pk):
    """
    编辑设备
    编辑设备，需要先登录
    ---
    tags:
      - 设备
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
            sound_volume:
              type: integer
              description: 音量 0 - 100
            car_id:
              type: integer
              description: 车辆id  (-10为清空,类型为int)
            license_plate_number:
              type: integer
              description: 车牌号
            device_type:
              type: integer
              description: 设备类型 1刷脸 2生成特征值
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
                  description: 新增的设备Id

    """
    sound_volume = data.get('sound_volume', None)
    car_id = data.get('car_id', None)
    license_plate_number = data.get('license_plate_number', None)
    device_type = data.get('device_type', None)

    if device_type and int(device_type) not in [1, 2]:
        raise AppError(*GlobalErrorCode.PARAM_ERROR)

    ret = DeviceService.device_update(
        pk, license_plate_number, car_id, sound_volume, device_type)
    if ret == -1:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.DEVICE_CHEPAI_NOT_FOUND)
    if ret == -11:
        raise AppError(*SubErrorCode.DEVICE_INITED_NOT_CHANGE)
    if ret == -12:
        raise AppError(*SubErrorCode.DEVICE_FIRST_BOUNDING_WORKER)
    if ret == -13:
        raise AppError(*SubErrorCode.DEVICE_CAR_ALREADY_BINDING)
    return ret


@bp.route('/person/info/<int:pk>', methods=['POST'])
@get_require_check_with_user([])
def device_person_info(user_id, data, pk):
    """
    设备列表
    设备列表，需要先登录
    ---
    tags:
      - 设备
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: PK
        in: path
        type: integer
        description: 设备id

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
                  published_numbers:
                    type: integer
                    description: 数量
                  published:
                    type: array
                    items:
                      properties:
                        nickname:
                          type: string
                          description: 昵称
                        school_name:
                          type: string
                          description: 学校名字
                        grade_name:
                          type: string
                          description: 年纪名字
                        stu_no:
                          type: string
                          description: 身份证
    """
    ret = DeviceService.get_device_person_data(pk)
    if ret == -1:
        raise AppError(*SubErrorCode.DEVICE_PLEASE_WAITING)
    elif ret == -2:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    elif ret == -3:
        raise AppError(*SubErrorCode.DEVICE_UNINITIALIZED_ERR)
    elif ret == -4:
        raise AppError(*SubErrorCode.DEVICE_ALREADY_CLOSE)
    elif ret == -5:
        raise AppError(*SubErrorCode.DEVICE_OPEN_THREE_MINUTES_LATER)
    return ret
