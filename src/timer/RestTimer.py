# coding:utf-8
import random
from urllib2 import urlopen
import time
import zlib
import base64
import json
import requests
import oss2
from datetime import datetime, timedelta

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest

from timer import db
from timer import config


def pub_msg(rds_conn, devname, jdata):
    print u"-----------加入顺序发送消息的队列--------"
    print jdata
    k = rds_conn.get("stream_no_incr")
    if k:
        stream_no = rds_conn.incr("stream_no_incr")
    else:
        rds_conn.set("stream_no_incr", 1000000)
        stream_no = 1000000
    jdata["stream_no"] = stream_no
    k = "mns_list_" + devname
    rds_conn.rpush(k, json.dumps(jdata, encoding="utf-8"))


class GenerateFeature(object):
    """生成feature"""

    DEVICE_CUR_TIMESTAMP = 'device_cur_timestamp_hash'
    DEVICE_USED = "device_used_hash"

    @db.transaction(is_commit=False)
    def generate_feature(self, pgsql_cur):
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        cur_timestamp = int(time.time())
        on_line_devices = []
        # 获取在线设备
        devices = rds_conn.hgetall(GenerateFeature.DEVICE_CUR_TIMESTAMP)
        for k, v in devices:
            if cur_timestamp - int(v) <= 30:
                on_line_devices.append(k)

        used_devices = []
        # 获取闲置中的设备
        devices = rds_conn.hgetall(GenerateFeature.DEVICE_USED)
        for k, v in devices:
            used_devices.append(k)
        unused_devices = set(on_line_devices) - set(used_devices)
        # 未处理的
        jdata = {
            "cmd": "addface",
            "fid": 0,
            "faceurl": ""
        }

        sql = "SELECT id,oss_url FROM face WHERE status == 2"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            face_id = row[0]
            oss_url = row[1]
            jdata["fid"] = face_id
            jdata['faceurl'] = oss_url
            device_name = unused_devices.pop()
            pub_msg(rds_conn, device_name, jdata)
            # 将设备置为使用中
            rds_conn.hset(GenerateFeature.DEVICE_USED, device_name)
            d = {
                'id': face_id,
                'status': 3
            }
            pgsql_db.update(pgsql_cur, d, table_name='face')


class EveryMinuteExe(object):

    @db.transaction(is_commit=True)
    def every_minute_execute(self, pgsql_cur):
        """每分钟执行一次"""
        print u"==================每分钟执行一次====================={}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print datetime.now()

        mysql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        rds_key = 'task_count'
        url = "http://api.pinganxiaoche.com/face/gettask?key=ksjaflnnsjiowe3"
        del_req = "http://api.pinganxiaoche.com/face/deltask?" \
                  "key=ksjaflnnsjiowe3&tid={}"
        sql = 'SELECT `id` FROM `face` WHERE `tid`={} LIMIT 1'
        r = requests.get(url)
        d = json.loads(r.content)
        for row in d["result"]:
            tid = row['tid']
            tid_count = rds_conn.hget(rds_key, str(tid))
            if tid_count:
                if int(tid_count) > 1:
                    requests.get(del_req.format(tid))
                    result = mysql_db.get(pgsql_cur, sql.format(tid))
                    if result:
                        face_id = result[0]
                        d = {
                            '`id`': face_id,
                            '`status`': 11  # 生成feature失败
                        }
                        mysql_db.update(pgsql_cur, d, table_name='`face`')
                else:
                    rds_conn.hset(rds_key, str(tid), int(tid_count) + 1)
            else:
                rds_conn.hset(rds_key, str(tid), 1)

        length = rds_conn.hlen(rds_key)
        if length and int(length) > 50:
            rds_conn.delete(rds_key)

        # 过期人脸更新状态
        expire_sql = """SELECT F.`id` FROM `user_profile` AS UP 
        INNER JOIN `face` AS F ON F.`user_id`=UP.`id` 
        WHERE UP.`deadline` < {} """
        results = mysql_db.query(pgsql_cur, expire_sql.format(time.time()))
        for row in results:
            face_id = row[0]
            d = {
                '`id`': face_id,
                '`status`': 2  # 过期
            }
            mysql_db.update(pgsql_cur, d, table_name='`face`')

        # msgqueue的心跳包
        try:
            from msgqueue import producer
            producer.heartbeat()
        except:
            pass


class FromOssQueryFace(object):

    def __init__(self):
        self.auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, config.OSSEndpoint,
                                  config.OSSBucketName)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey

    @db.transaction(is_commit=True)
    def from_oss_get_face(self, pgsql_cur):
        """从oss获取人脸"""
        print u"==================从oss获取人脸====================="
        print datetime.now()
        start = time.time()
        # 获取未绑定的人脸
        mysql_db = db.PgsqlDbUtil
        sql = "SELECT F.`id`,F.`emp_no` FROM `face` AS F \
    INNER JOIN `user_profile` AS UP ON UP.`id`=F.`user_id` WHERE " \
              "F.`status`=-2 AND UP.`status`=1 order by rand()"
        results = mysql_db.query(pgsql_cur, sql)
        emp_no_pk_map = {}
        server_face_list = []       # 服务器上的工号列表
        for row in results:
            pk = row[0]
            emp_no = row[1]
            server_face_list.append(emp_no)
            emp_no_pk_map[emp_no] = pk

        print server_face_list
        if server_face_list:
            oss_face = []       # oss上的工号列表
            for obj in oss2.ObjectIterator(self.bucket, prefix='people/face/'):
                slash_arr = obj.key.split("/")
                if slash_arr and len(slash_arr) == 3:
                    comma_arr = slash_arr[-1].split('.')
                    if comma_arr and len(comma_arr) == 2 \
                            and comma_arr[-1] == 'jpg':
                        oss_face.append(comma_arr[0])
            oss_face_set = set(oss_face)
            server_face_set = set(server_face_list)
            intersection = list(oss_face_set & server_face_set)
            intersection = intersection[:100]
            for row in intersection:
                d = {
                    '`id`': emp_no_pk_map[row],
                    '`oss_url`': config.OSSDomain + "/people/face/" + row + ".jpg",
                    '`status`': -1  # 未处理
                }
                mysql_db.update(pgsql_cur, d, table_name='`face`')
        end = time.time()
        print end - start


class EveryFewMinutesExe(object):

    def __init__(self):
        self.auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, config.OSSEndpoint, config.OSSBucketName)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey

    def every_few_minutes_execute(self):
        """
        每五分钟执行一次 删除不规则人脸
        :return:
        """
        try:
            # 删除不规则的人脸
            for obj in oss2.ObjectIterator(self.bucket, prefix='people/face/'):
                is_del = 0
                slash_arr = obj.key.split("/")
                if slash_arr and len(slash_arr) != 3:
                    is_del = 1
                if slash_arr and len(slash_arr) == 3 and not is_del:
                    comma_arr = slash_arr[-1].split('.')
                    if comma_arr and len(comma_arr) != 2:
                        is_del = 1
                    if comma_arr and comma_arr[-1] == 'JPG':
                        is_del = 1
                if is_del:
                    self.bucket.delete_object(obj.key)
        except:
            import traceback
            db.logger.error(traceback.format_exc())


class OrderSendMsg(object):

    def __init__(self):
        self.auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, config.OSSEndpoint,
                                  config.OSSBucketName)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey

    def order_sent_msg(self):
        """顺序发送消息"""
        try:
            request = PubRequest()
            request.set_accept_format('json')

            rds_conn = db.rds_conn
            device_queues = rds_conn.keys('mns_list_*')
            for queue_name in device_queues:
                device_name = queue_name[9:]
                k = "cur_{}_stream_no".format(device_name)
                # 不存在就取出一条消息发送到物联网
                if not rds_conn.get(k):
                    print u"key 不存在"
                    raw_msg_content = rds_conn.lpop(queue_name)
                    print raw_msg_content
                    data = json.loads(raw_msg_content)

                    stream_no = data['stream_no']
                    rds_conn.set(k, stream_no)
                    rds_conn.expire(k, 30)
                    # 发送消息
                    topic = '/' + self.product_key + '/' \
                            + device_name + '/user/get'
                    request.set_TopicFullName(topic)

                    b64_str = base64.b64encode(json.dumps(data, encoding='utf8'))
                    request.set_MessageContent(b64_str)
                    request.set_ProductKey(self.product_key)
                    self.client.do_action_with_exception(request)
        except:
            import traceback
            err_msg = traceback.format_exc()
            print err_msg
            db.logger.error(err_msg)