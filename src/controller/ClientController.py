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
bp = Blueprint('ClientController', __name__)
"""蓝图url前缀"""
url_prefix = '/client'


@bp.route('/list', methods=['GET'])
@get_require_check_with_user([])
def client_list(user_id, data):
    pass