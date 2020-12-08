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

from service.OrderService import OrderService


try:
    import requests
    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('OrderController', __name__)
"""蓝图url前缀"""
url_prefix = '/order'


@bp.route('/order/download', methods=['GET'])
def order_download():
    pass