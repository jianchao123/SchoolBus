# coding:utf-8

"""
向监控中心发送订单数据
"""
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import ctypes
import json
import time
import random
import string
import threading
import hashlib
import base64
import requests
from datetime import datetime


project_src_dir = os.path.dirname(os.path.realpath(__file__))
project_src_dir = os.path.dirname(project_src_dir)
sys.path.insert(0, project_src_dir)
from timer import db
from timer.define import RedisKey

url = "http://182.148.114.194:65415/school/bus/report"
access_key_id = "hnxccs8865"
access_key_secret = "3422af52-9905-4965-b678-18c0a99fc106"
access_token = "76D1B5030005F6474A3230013A7B9884"


def _get_created():
    import pytz
    tz = pytz.timezone('UTC')
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def get_header(data):
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Content-Length': 0,
        'Content-MD5': '',
        'Authorization': 'WSSE profile="UsernamePwd"',
        'X-WSSE': 'UsernamePwd Username="{}", '
                  'PasswordDigest="{}",Nonce="{}",Created="{}"'

    }
    nonce = ''.join(
        random.sample(string.ascii_letters + string.digits, 16))
    created = _get_created()

    length = len(data)
    headers['Content-Length'] = str(length)

    m = hashlib.md5()
    m.update(data.encode('utf-8'))
    content_md5 = base64.b64encode(bin(int(m.hexdigest(), 16))[2:])
    headers['Content-MD5'] = content_md5

    password_digest = \
        nonce + created + access_key_secret + content_md5
    password_digest = \
        base64.b64encode(
            hashlib.sha1(password_digest.encode('utf8')).hexdigest())
    headers['X-WSSE'] = \
        headers['X-WSSE'].format(access_key_id, password_digest, nonce, created)
    headers['ACCESS_TOKEN'] = access_token
    return headers


def send_order():
    print threading.current_thread().getName()
    print "threaing id: ", ctypes.CDLL('libc.so.6').syscall(186)
    while True:
        rds_conn = db.rds_conn
        raw_data = rds_conn.blpop(RedisKey.SC_ORDER_LIST, 100)
        if raw_data:
            raw_data = raw_data[1]
            try:
                raw_data = raw_data.encode('utf8')
                res = requests.post(url, raw_data, headers=get_header(raw_data))
                db.logger.error(res.content)
                if res.status_code == 200:
                    res_data = json.loads(res.content)
                    db.logger.error(json.dumps(res_data, ensure_ascii=False))
            except:
                import traceback
                print traceback.format_exc()
                print "ConnectionError"
#
# def send_alarm():
#     while True:
#         rds_conn = db.rds_conn
#         raw_data = rds_conn.blpop(RedisKey.SC_ALARM_LIST, 100)
#         if raw_data:
#             res = requests.post(url, raw_data, headers=get_header(raw_data))
#             if res.status_code == 200:
#                 print "-------------upload alarm data------------"
#                 res_data = json.loads(res.content)
#                 print json.dumps(res_data, ensure_ascii=False)


threads = []
t1 = threading.Thread(target=send_order)
threads.append(t1)
# t2 = threading.Thread(target=send_alarm)
# threads.append(t2)

if __name__ == '__main__':
    for t in threads:
        t.setDaemon(True)
        t.start()
    while True:
        time.sleep(10)
