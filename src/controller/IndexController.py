# coding:utf-8
from flask.blueprints import Blueprint

from core.framework import get_require_check_with_user
from service.IndexService import IndexService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('IndexController', __name__)
"""蓝图url前缀"""
url_prefix = '/index'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user([])
def index_list(user_id, data):
    """
    首页
    首页，需要先登录
    ---
    tags:
      - 主页
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
                  today_take_bus_number:
                    type: integer
                    description: 今日乘车数
                  yesterday_take_bus_number:
                    type: integer
                    description: 昨日乘车数
                  device_online_number:
                    type: integer
                    description: 在线设备数
                  device_offline_number:
                    type: integer
                    description: 离线设备数
                  this_week_alert_number:
                    type: integer
                    description: 本周告警数
                  last_week_alert_number:
                    type: integer
                    description: 上周告警数
                  today_alert_number:
                    type: integer
                    description: 今日告警数
                  yesterday_alert_number:
                    type: integer
                    description: 昨日告警数

    """
    return IndexService.index_list()