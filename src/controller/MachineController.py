# coding:utf-8

from flask.blueprints import Blueprint

from core.framework import get_require_check
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode
from service.MachineService import MachineService

try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('MachineController', __name__)
"""蓝图url前缀"""
url_prefix = '/machine'


@bp.route('/newdev_info', methods=['GET'])
@get_require_check(['mac'])
def newdev_info(data):
    """
    newdev信息
    newdev信息，需要先登录
    ---
    tags:
      - 物联网
    parameters:
      - name: mac
        in: query
        type: string
        description: mac地址

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
                  product_key:
                    type: string
                    description: 产品key
                  newdev_secret:
                    type: string
                    description: newdev的secret
                  newdev_name:
                    type: string
                    description: 设备名字
    """
    mac = data['mac']
    ret = MachineService.newdev_info(mac)
    if ret == -1:
        raise AppError(*SubErrorCode.IOT_MAC_NOT_FOUND)
    return ret
