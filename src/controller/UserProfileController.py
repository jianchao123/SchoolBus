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

from service.UserProfileService import UserProfileService


try:
    import requests
    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('UserProfileController', __name__)
"""蓝图url前缀"""
url_prefix = '/user'


@bp.route('/login', methods=['POST'])
@post_require_check(['username', 'password'])
def user_login(args):
    """
    用户登录
    登录
    ---
    tags:
      - 用户模块
    parameters:
      - name: body
        in: body
        required: true
        schema:
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 用户名字
            password:
              type: string
              description: 密码
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
                token:
                  type: string
                  description: token串,登录的时候放到header
                user:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: 用户id
                    username:
                      type: string
                      description: 用户名字

    """
    username = args['username']
    password = args['password']

    if username == '' or password == '':
        raise AppError(*SubErrorCode.USER_PWD_ERR)

    user_obj = UserProfileService.get_user_by_username(username)
    if not user_obj:
        raise AppError(*SubErrorCode.USER_PWD_ERR)

    password_md5_str = md5_encrypt(password)
    if user_obj["password"] != password_md5_str:
        raise AppError(*SubErrorCode.USER_PWD_ERR)

    token = gen_token(password, conf.config["SALT"], 3600)
    UserProfileService.login(user_obj["id"], token)

    return {
        'token': token,
        'user': {
            'id': user_obj['id'],
            'username': user_obj['username']
        }
    }


@bp.route('/change_password', methods=['POST'])
@post_require_check_with_permissions([])
def change_password(user_id, args):
    """
    修改密码
    ---
    tags:
      - 用户模块
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
            password:
              type: string
              description: 密码
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
    """
    password = args['password']
    if 16 < len(password) < 8:
        raise AppError(*SubErrorCode.USER_PWD_LEN_ERR)
    return UserProfileService.modify_pwd(user_id, password)