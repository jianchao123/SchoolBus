# coding:utf-8

from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user, form_none_param_with_permissions
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.SchoolService import SchoolService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('SchoolController', __name__)
"""蓝图url前缀"""
url_prefix = '/school'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def school_list(user_id, data):
    """
    学校列表
    学校列表，需要先登录
    ---
    tags:
      - 学校
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: school_name
        in: query
        type: string
        description: 学校名字
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
                  school_name:
                    type: string
                    description: 学校名字


    """
    school_name = data.get('school_name', None)
    page = int(data['page'])
    size = int(data['size'])
    return SchoolService.school_list(school_name, page, size)


@bp.route('/add', methods=['POST'])
@post_require_check_with_user([])
def school_add(user_id, data):
    """
    添加学校
    添加学校，需要先登录
    ---
    tags:
      - 学校
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
            school_name:
              type: string
              description: 学校名字
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
                  description: 新增的学校Id

    """
    school_name = data['school_name']

    ret = SchoolService.school_add(school_name)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.SCHOOL_NAME_ALREADY_EXISTS)
    return ret


@bp.route('/update/<int:pk>', methods=['POST'])
@post_require_check_with_user([])
def school_update(user_id, data, pk):
    """
    编辑学校
    编辑学校，需要先登录
    ---
    tags:
      - 学校
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
            school_name:
              type: string
              description: 学校名字
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
                  description: 更新的学校Id

    """
    school_name = data.get('school_name', None)

    ret = SchoolService.school_update(pk, school_name)
    if ret == -1:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*SubErrorCode.CAR_CHEPAI_ALREADY_EXISTS)
    return ret


@bp.route('/batchadd', methods=['POST'])
@form_none_param_with_permissions()
def school_batch_add(user_id, data):
    """
    批量添加学校
    批量添加学校，需要先登录
    ---
    tags:
      - 学校
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
    data = SchoolService.batch_add_school(fd)
    if data == -10:
        raise AppError(*SubErrorCode.TASK_EXECUTING)
    return data
