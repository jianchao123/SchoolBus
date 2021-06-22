# coding:utf-8
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


@bp.route('/get_children_data', methods=['GET'])
@get_require_check(['openid'])
def children_data(args):
    """
    根据openid获取绑定的学生信息
    ---
    tags:
      - 公众号
    parameters:
      - name: openid
        in: query
        type: string
        description: OPENID

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
                  description: ID
                nickname:
                  type: string
                  description: 昵称
    """
    openid = args['openid']
    return WxMPService.children_data(openid)


@bp.route('/authorize_str', methods=['GET'])
@get_require_check(['menu_name'])
def authorize_str(args):
    """
    获取授权串
    获取授权串，需要先登录
    ---
    tags:
      - 公众号
    parameters:
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
                url:
                  type: string
                  description: 授权url
    """
    menu_name = args['menu_name']
    from urllib import quote

    s = "https://open.weixin.qq.com/connect/oauth2/authorize?appid={}" \
        "&redirect_uri={}&response_type=code&scope=snsapi_base&state={}" \
        "#wechat_redirect".format(conf.config['MP_APP_ID'],
                                  quote(conf.config['MP_AUTH_URI']), menu_name)
    return {'url': s}


@bp.route('/get_open_id', methods=['GET'])
@get_require_check(['code'])
def get_open_id(args):
    """
    获取open_id
    获取open_id，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: code
        in: query
        type: string
        description: 微信提供
      - name: state
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
                openid:
                  type: string
                  description: OPENID 后面的每个接口都加上open_id的参数
                is_binding:
                  type: integer
                  description: 是否绑定手机号 1是 0否
    """
    code = args['code']
    print "===================="
    print args.get('state', None)
    return WxMPService.get_open_id(code)


@bp.route('/disable/binding', methods=['POST'])
@post_require_check(['open_id'])
def cancel_binding(args):
    """
    解除openid和手机号的绑定
    解除openid和手机号的绑定，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            open_id:
              type: string
              description: OPENID
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
                  description: 0 解绑成功
    """
    open_id = args['open_id']
    ret = WxMPService.cancel_binding(open_id)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    return ret


@bp.route('/save_mobile', methods=['POST'])
@post_require_check(['mobile', 'open_id'])
def save_mobile(args):
    """
    将openid绑定到学生或者工作人员
    将openid绑定到学生或者工作人员，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            mobile:
              type: string
              description: 手机号
            open_id:
              type: string
              description: OPENID
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
                open_id:
                  type: integer
                  description: OPENID
    """
    mobile = args['mobile']
    open_id = args['open_id']
    ret = WxMPService.save_mobile(mobile, open_id)
    if ret == -10:
        raise AppError(*SubErrorCode.STUDENT_NOT_FOUND_PARENTS_MOBILE)
    return ret


@bp.route('/get_role', methods=['GET'])
@get_require_check(['open_id'])
def get_role(args):
    """
    根据openid获取角色
    1.如果该openid只绑定了家长就只返回家长mobile
    2.如果该openid只绑定了工作人员就只返回工作人员mobile
    3.如果该openid同时绑定了家长和工作人员就只返回工作人员mobile
    获取角色，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: open_id
        in: query
        type: string
        description: OPENID
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
                parents:
                  type: integer
                  description: 是否父母 1是 0否
                driver:
                  type: integer
                  description: 是否驾驶员 1是 0否
                zgy:
                  type: integer
                  description: 是否照顾员 1是 0否
                mobile:
                  type: string
                  description: 手机号
    """
    open_id = args['open_id']
    return WxMPService.get_role(open_id)


@bp.route('/bus_where', methods=['GET'])
@get_require_check(['open_id'])
def bus_where(args):
    """
    校车在哪儿
    校车在哪儿，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: open_id
        in: query
        type: string
        description: OPENID
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
                d:
                  type: integer
                  description: 先判断此字段. 0 正常显示数据, -10 跳转到绑定手机号页面
                gps:
                  type: string
                  description: 123.123456,34.123456
                staff:
                  type: string
                  description: 职员信息 刘玉 (驾驶员 18502547895)\\n 王五 (照管员 15678941234)
                order_type:
                  type: integer
                  description: 1 上学上车 2上学下车 3 放学上车 4 放学下车
                nickname:
                  type: string
                  description: 学生名字
                create_time:
                  type: integer
                  description: 创建时间
    """
    open_id = args['open_id']
    return WxMPService.bus_where(open_id)


@bp.route('/order/retrieve', methods=['GET'])
@get_require_check(['order_id'])
def order_retrieve(args):
    """
    检索订单
    检索订单，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: order_id
        in: query
        type: integer
        description: 订单id 从页面连接上获取
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
                gps:
                  type: string
                  description: gps 逗号分割
                time:
                  type: string
                  description: 时间
                url:
                  type: integer
                  description: 实时刷脸url

    """
    order_id = args['order_id']
    return WxMPService.get_order_by_id(order_id)


@bp.route('/alarm/retrieve', methods=['GET'])
@get_require_check(['periods'])
def alarm_retrieve(args):
    """
    检索报警
    检索报警，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: periods
        in: query
        type: string
        description: 期数 从页面链接上获取
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
                numbers:
                  type: string
                  description: 报警人数
                alert_info:
                  type: string
                  description: 人员信息,前端自行分割处理
                license_plate_number:
                  type: integer
                  description: 车牌号
                time:
                  type: string
                  description: 刷脸时间
                gps:
                  type: string
                  description: gps
                worker_info:
                  type: string
                  description: 工作人员信息
                status:
                  type: integer
                  description: 1 正在报警 2已解除

    """
    periods = args['periods']
    return WxMPService.alert_info_by_id(periods)


@bp.route('/alarm/cancel', methods=['POST'])
@post_require_check(['periods'])
def alarm_cancel(args):
    """
    解除报警
    解除报警，需要先登录
    ---
    tags:
      - 公众号
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            open_id:
              type: string
              description: OPENID
            periods:
              type: string
              description: 报警期数
            cancel_type_id:
              type: integer
              description: 取消类型id 1其他 2无学生解除 3有学生解除
            cancel_reason:
              type: string
              description: 取消原因
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
                  description: 解绑的id
    """
    periods = args['periods']
    open_id = args['open_id']
    cancel_type_id = int(args['cancel_type_id'])
    cancel_reason = args.get('cancel_reason', None)
    ret = WxMPService.cancel_alert(open_id, periods, cancel_type_id, cancel_reason)
    if ret == -2:
        raise AppError(*GlobalErrorCode.DB_COMMIT_ERR)
    if ret == -10:
        raise AppError(*GlobalErrorCode.OBJ_NOT_FOUND_ERROR)
    if ret == -11:
        raise AppError(*SubErrorCode.ALARM_STATUS_ERR)
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