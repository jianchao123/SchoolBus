# coding:utf-8

from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user, \
    form_none_param_with_permissions
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.WorkerService import WorkerService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('WorkerController', __name__)
"""蓝图url前缀"""
url_prefix = '/worker'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def worker_list(user_id, data):
    """
    工作人员列表
    工作人员列表，需要先登录
    ---
    tags:
      - 工作人员
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: query_str
        in: query
        type: string
        description: 员工姓名/工号
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
                  emp_no:
                    type: string
                    description: 工号
                  gender:
                    type: integer
                    description: 1男2女
                  license_plate_number:
                    type: string
                    description: 车牌号
                  company_name:
                    type: string
                    description: 公司名字
                  remarks:
                    type: string
                    description: 备注
                  duty_id:
                    type: integer
                    description: 职务id 1驾驶员 2照管员

    """
    query_str = data.get('query_str', None)
    page = int(data['page'])
    size = int(data['size'])

    return WorkerService.worker_list(query_str, page, size)


@bp.route('/add', methods=['POST'])
@post_require_check_with_user([])
def worker_add(user_id, data):
    """
    添加工作人员
    添加工作人员，需要先登录
    ---
    tags:
      - 工作人员
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
            emp_no:
              type: string
              description: 工号
            nickname:
              type: string
              description: 姓名
            gender:
              type: integer
              description: 性别 1男2女
            mobile:
              type: string
              description: 手机号
            remarks:
              type: string
              description: 备注
            company_name:
              type: string
              description: 公司名字
            department_name:
              type: string
              description: 部门名字
            duty_id:
              type: integer
              description: 职务id 1驾驶员 2照管员
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
                  description: 新增的工作人员Id

    """
    emp_no = data['emp_no']
    nickname = data['nickname']
    gender = data['gender']
    mobile = data['mobile']
    remarks = data['remarks']
    company_name = data['company_name']
    department_name = data['department_name']
    duty_id = data['duty_id']
    license_plate_number = data['license_plate_number']

    ret = WorkerService.worker_add(
        emp_no, nickname, gender, mobile, remarks, company_name, 
        department_name, duty_id, license_plate_number)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.WORKER_EMP_NO_ALREADY_EXISTS)
    if ret == -11:
        raise AppError(*SubErrorCode.CAR_NOT_FOUND)
    if ret == -12:
        raise AppError(*SubErrorCode.WORKER_ALREADY_EXISTS_DUTY)
    return ret


@bp.route('/update/<int:pk>', methods=['POST'])
@post_require_check_with_user([])
def worker_update(user_id, data, pk):
    """
    编辑工作人员
    编辑工作人员，需要先登录
    ---
    tags:
      - 工作人员
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
            emp_no:
              type: string
              description: 工号
            nickname:
              type: string
              description: 姓名
            gender:
              type: integer
              description: 性别 1男2女
            mobile:
              type: string
              description: 手机号
            remarks:
              type: string
              description: 备注
            company_name:
              type: string
              description: 公司名字
            department_name:
              type: string
              description: 部门名字
            duty_id:
              type: integer
              description: 职务id 1驾驶员 2照管员
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
                  description: 新增的工作人员Id

    """
    emp_no = data['emp_no']
    nickname = data['nickname']
    gender = data['gender']
    mobile = data['mobile']
    remarks = data['remarks']
    company_name = data['company_name']
    department_name = data['department_name']
    duty_id = data['duty_id']
    license_plate_number = data['license_plate_number']

    ret = WorkerService.worker_update(
        pk, emp_no, nickname, gender, mobile, remarks, company_name, 
        department_name, duty_id, license_plate_number)
    if ret == -1:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.WORKER_EMP_NO_ALREADY_EXISTS)
    if ret == -11:
        raise AppError(*SubErrorCode.CAR_NOT_FOUND)
    if ret == -12:
        raise AppError(*SubErrorCode.WORKER_NO_CHANGE_DUTY)
    return ret


@bp.route('/batchadd', methods=['POST'])
@form_none_param_with_permissions()
def worker_batch_add(user_id, data):
    """
    批量添加工作人员
    批量添加工作人员，需要先登录
    ---
    tags:
      - 工作人员
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
    data = WorkerService.batch_add_worker(fd)
    return data
