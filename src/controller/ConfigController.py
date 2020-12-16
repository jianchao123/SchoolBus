# coding:utf-8
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user
from service.ConfigService import ConfigService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('ConfigController', __name__)
"""蓝图url前缀"""
url_prefix = '/config'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user([])
def config_list(user_id, data):
    """
    配置
    配置，需要先登录
    ---
    tags:
      - 配置
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
              type: object
              properties:
                oss:
                  properties:
                    oss_key:
                      type: string
                      description: KEY
                    oss_secret:
                      type: string
                      description: secret


    """
    return ConfigService.config_list()