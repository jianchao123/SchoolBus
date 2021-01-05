# coding:utf-8
from datetime import datetime
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user, \
    post_require_check_with_user, form_none_param_with_permissions
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode

from service.StudentService import StudentService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('StudentController', __name__)
"""蓝图url前缀"""
url_prefix = '/student'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user(['page', 'size'])
def student_list(user_id, data):
    """
    学生列表
    学生列表，需要先登录
    ---
    tags:
      - 学生
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: query_str
        in: query
        type: string
        description: 学生姓名/身份证号
      - name: school_id
        in: query
        type: integer
        description: 学校id
      - name: grade_id
        in: query
        type: integer
        description: 年纪id
      - name: class_id
        in: query
        type: integer
        description: 班级id
      - name: start_date
        in: query
        type: string
        description: 开始日期
      - name: end_date
        in: query
        type: string
        description: 结束日期
      - name: license_plate_number
        in: query
        type: string
        description: 车牌号
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
                  gender:
                    type: integer
                    description: 1男2女
                  license_plate_number:
                    type: string
                    description: 车牌号
                  face_status:
                    type: integer
                    description: 人脸状态 1没有人脸 2未处理 3处理中 4有效(处理完成) 5生成feature失败 6过期
    """
    query_str = data.get('query_str', None)
    school_id = data.get('school_id', None)
    grade_id = data.get('grade_id', None)
    class_id = data.get('class_id', None)
    face_status = data.get('face_status', None)
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)
    car_id = data.get('car_id', None)
    license_plate_number = data.get('license_plate_number', None)
    page = int(data['page'])
    size = int(data['size'])

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise AppError(*GlobalErrorCode.PARAM_ERROR)
    return StudentService.student_list(
        query_str, school_id, grade_id, class_id, face_status,
        start_date, end_date, car_id, license_plate_number, page, size)


@bp.route('/add', methods=['POST'])
@post_require_check_with_user(['stu_no', 'nickname'])
def student_add(user_id, data):
    """
    添加学生
    添加学生，需要先登录
    ---
    tags:
      - 学生
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
            stu_no:
              type: string
              description: 身份证号
            nickname:
              type: integer
              description: 姓名
            gender:
              type: integer
              description: 性别 1男2女
            parents_1:
              type: integer
              description: 家长1
            mobile_1:
              type: integer
              description: 手机号
            parents_2:
              type: integer
              description: 家长2
            mobil_2:
              type: integer
              description: 手机号
            address:
              type: integer
              description: 地址
            remarks:
              type: integer
              description: 备注
            school_id:
              type: integer
              description: 学校id
            grade_id:
              type: integer
              description: 年纪id
            class_id:
              type: integer
              description: 班级id
            end_time:
              type: integer
              description: 截至时间
            car_id:
              type: integer
              description: 车辆id
            oss_url:
              type: integer
              description: oss_url

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
                  description: 新增的学生Id

    """
    stu_no = data['stu_no']
    nickname = data['nickname']
    gender = data['gender']
    parents_1 = data['parents_1']
    mobile_1 = data['mobile_1']
    parents_2 = data['parents_2']
    mobile_2 = data['mobile_2']
    address = data['address']
    remarks = data.get('remarks', '')
    school_id = data['school_id']
    grade_id = data['grade_id']
    class_id = data['class_id']
    end_time = data['end_time']
    car_id = data['car_id']
    oss_url = data['oss_url']

    try:
        end_time = datetime.strptime(end_time, '%Y-%m-%d')
    except ValueError:
        raise AppError(*GlobalErrorCode.PARAM_ERROR)

    ret = StudentService.student_add(
        stu_no, nickname, gender, parents_1, mobile_1, parents_2,
        mobile_2, address, remarks, school_id, grade_id, class_id,
        end_time, car_id, oss_url)
    if ret == -1:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -11:
        raise AppError(*SubErrorCode.CAR_NOT_FOUND)
    if ret == -12:
        raise AppError(*SubErrorCode.STUDENT_ID_CARD_ALREADY_EXISTS)
    return ret


@bp.route('/update/<int:pk>', methods=['POST'])
@post_require_check_with_user([])
def student_update(user_id, data, pk):
    """
    编辑学生
    编辑学生，需要先登录
    ---
    tags:
      - 学生
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
            stu_no:
              type: string
              description: 身份证号
            nickname:
              type: integer
              description: 姓名
            gender:
              type: integer
              description: 性别 1男2女
            parents_1:
              type: integer
              description: 家长1
            mobile_1:
              type: integer
              description: 手机号
            parents_2:
              type: integer
              description: 家长2
            mobil_2:
              type: integer
              description: 手机号
            address:
              type: integer
              description: 地址
            remarks:
              type: integer
              description: 备注
            school_id:
              type: integer
              description: 学校id
            grade_id:
              type: integer
              description: 年纪id
            class_id:
              type: integer
              description: 班级id
            end_time:
              type: integer
              description: 截至时间
            car_id:
              type: integer
              description: 车辆id (-10为清空,类型为Int)
            oss_url:
              type: integer
              description: oss_url

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
                  description: 新增的学生Id

    """
    stu_no = data.get('stu_no', None)
    nickname = data.get('nickname', None)
    gender = data.get('gender', None)
    parents_1 = data.get('parents_1', None)
    mobile_1 = data.get('mobile_1', None)
    parents_2 = data.get('parents_2', None)
    mobile_2 = data.get('mobile_2', None)
    address = data.get('address', None)
    remarks = data.get('remarks', None)
    school_id = data.get('school_id', None)
    grade_id = data.get('grade_id', None)
    class_id = data.get('class_id', None)
    end_time = data.get('end_time', None)
    car_id = data.get('car_id', None)
    oss_url = data.get('oss_url', None)

    if end_time:
        try:
            end_time = datetime.strptime(end_time, '%Y-%m-%d')
        except ValueError:
            raise AppError(*GlobalErrorCode.PARAM_ERROR)

    ret = StudentService.student_update(
        pk, stu_no, nickname, gender, parents_1, mobile_1, parents_2,
        mobile_2, address, remarks, school_id, grade_id, class_id,
        end_time, car_id, oss_url)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -11:
        raise AppError(*SubErrorCode.CAR_NOT_FOUND)
    if ret == -12:
        raise AppError(*SubErrorCode.STUDENT_ID_CARD_ALREADY_EXISTS)
    return ret


@bp.route('/batchadd', methods=['POST'])
@form_none_param_with_permissions()
def student_batch_add(user_id, data):
    """
    批量添加学生
    批量添加学生，需要先登录
    ---
    tags:
      - 学生
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
    data = StudentService.batch_add_student(fd)
    if data == -10:
        raise AppError(*SubErrorCode.TASK_EXECUTING)
    return data
