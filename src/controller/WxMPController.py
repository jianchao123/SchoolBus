# coding:utf-8
import json
import hashlib
from flask import request
from flask.blueprints import Blueprint
from weixin import WeixinMsg
from ext import conf
from core.AppError import AppError
from utils.defines import SubErrorCode, GlobalErrorCode
from service.WxMPService import WxMPService
from core.framework import get_require_check, post_require_check


try:
    import requests

    client_name = 'requests'
except ImportError:
    client_name = 'httplib'

# """蓝图对象"""
bp = Blueprint('WxMPController', __name__)
"""蓝图url前缀"""
url_prefix = '/wxmp'

"""
公众号菜单填写 /authorize_str?menu_name=mobile
公众号拿到url开始跳转,到redirect_uri页面,用户填写好手机号之后,请求save_mobile
redirect_uri(静态页面)
"""


@bp.route('/authorize_str')
@get_require_check([])
def authorize_str(args):
    """
    获取授权串
    获取授权串，需要先登录
    ---
    tags:
      - 获取授权串
    parameters:
      - name: token
        in: header
        type: string
        required: true
        description: TOKEN
      - name: menu_name
        in: query
        type: string
        description: 菜单名字

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
                    url:
                      type: string
                      description: 授权url
    """
    menu_name = args['menu_name']
    s = "https://open.weixin.qq.com/connect/oauth2/authorize?appid={}" \
        "&redirect_uri={}&response_type=code&scope=snsapi_base&state={}" \
        "#wechat_redirect".format(conf.config['MP_APP_ID'],
                                  conf.config['MP_AUTH_URI'], menu_name)
    return {'url': s}


@bp.route('/save_mobile')
@post_require_check([])
def save_mobile(args):
    """
    保存手机号
    保存手机号，需要先登录
    ---
    tags:
      - 订单模块
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
          required:
            - organization_id
            - user_id
          properties:
            mobile:
              type: string
              description: 手机号
            code:
              type: string
              description: CODE
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
                  description: 新Id
    """
    mobile = args['mobile']
    code = args['code']
    ret = WxMPService.save_mobile(mobile, code)
    if ret == -10:
        raise AppError(*SubErrorCode.STUDENT_NOT_FOUND_PARENTS_MOBILE)
    return ret


wx_msg = WeixinMsg(conf.config['MP_TOKEN'])


@bp.route('/callback', methods=['POST', 'GET'])
def wx_callback_list():
    try:
        if request.method == 'GET':
            data = request.values.to_dict()
            print data
            if len(data) == 0:
                return "hello, this is handle view"
            signature = data['signature']
            timestamp = data['timestamp']
            nonce = data['nonce']
            echostr = data.get('echostr', None)
            token = conf.config['MP_TOKEN']

            ls = [token, timestamp, nonce]
            ls.sort()
            sha1 = hashlib.sha1()
            map(sha1.update, ls)
            hashcode = sha1.hexdigest()
            print "handle/GET func: hashcode, signature: ", hashcode, signature
            if hashcode == signature:
                return echostr
            else:
                return ""
        elif request.method == 'POST':
            ret = wx_msg.parse(request.data)
            print ret
            msg_type = ret['type']
            sender = ret['sender']
            if msg_type == 'text':
                print ret['content']
            elif msg_type == 'event':
                """
                {u'status': None, u'sender': 'opeBzwwl3Z34uyyZtnMIoAfF-qOc', 
                u'timestamp': 1608186951, u'receiver': 'gh_949a03d359ca', 
                u'precision': None, u'longitude': None, u'event_key': '', 
                u'event': 'unsubscribe', u'time': datetime.datetime(2020, 12, 17, 14, 35, 51), 
                u'latitude': None, u'ticket': None, u'type': 'event', 
                u'id': None}
                
                {u'status': None, u'sender': 'opeBzwwl3Z34uyyZtnMIoAfF-qOc', 
                u'timestamp': 1608187186, u'receiver': 'gh_949a03d359ca', 
                u'precision': None, u'longitude': None, u'event_key': '', 
                u'event': 'subscribe', u'time': datetime.datetime(2020, 12, 17, 14, 39, 46), 
                u'latitude': None, u'ticket': None, u'type': 'event', u'id': None}
                """
                if ret['event'] == 'subscribe':
                    return wx_msg.reply(sender, 'text', conf.config['MP_ID'],
                                        content=u'请回复您当前关注的手机号')
            return wx_msg.reply(
                sender, 'text', conf.config['MP_ID'], content='hello')
    except:
        import traceback
        print traceback.format_exc()

#
# bp.add_url_rule('/callback', view_func=msg.view_func)
#
#
# @msg.text()
# def text(**kwargs):
#     print kwargs
#     return "所有文本消息"