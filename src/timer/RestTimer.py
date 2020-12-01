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


class GenerateTid(object):

    def _get_user_tid(self, oss_url):
        params = {
            'key': 'ksjaflnnsjiowe3',
            'faceurl': oss_url
        }
        payload = """------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data;
            name=\"key\"\r\n\r\n{}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data;
            name=\"products\"\r\n\r\n {}\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--""".format(
            params['key'], params['faceurl'])
        headers = {
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
        }
        resp = None
        try:
            resp = requests.post('http://api.pinganxiaoche.com/face/regface',
                                 data=payload,
                                 params=params,
                                 verify=False, timeout=3, headers=headers)
        except:
            return None
        c = json.loads(resp.content)
        print c
        if not c['code']:
            return c['tid']
        return None

    @db.transaction(is_commit=True)
    def generate_tid(self, mysql_cur):
        """
        生成tid (因为远程服务器执行能力不够,同一时间单线程执行)
        :return:
        """
        print u"==================生成tid====================="
        print datetime.now()
        mysql_db = db.MysqlDbUtil(mysql_cur)
        rds_conn = db.rds_conn
        setnx_key = rds_conn.setnx('generate_tid', 1)
        if setnx_key:
            try:
                sql = """
                SELECT F.`id`,F.`oss_url`,F.`update_time` FROM `face` AS F 
                INNER JOIN `user_profile` AS UP ON UP.`id`=F.`user_id` 
                WHERE F.`status`=-1 AND UP.`status`=1
                ORDER BY F.`id` ASC LIMIT 6
                """
                results = mysql_db.query(sql)
                for row in results:
                    update_time = row[2]
                    # 如果是刚刚更新,需要等一会儿去生成tid
                    if update_time + timedelta(seconds=20) > datetime.now():
                        continue
                    tid = self._get_user_tid(row[1])
                    if tid:
                        d = {
                            '`id`': row[0],
                            '`tid`': tid,
                            '`status`': 0  # 处理中
                        }
                        mysql_db.update(d, table_name='`face`')
            finally:
                rds_conn.delete('generate_tid')


class QueryFeature(object):

    def _get_feature_by_tid(self, tid):
        """
        feature_status (0未处理 1处理中 2处理完成 3失败)
        :param tid:
        :return:
        """
        url = 'http://api.pinganxiaoche.com/face/getresult?' \
              'key=ksjaflnnsjiowe3&tid={}'.format(tid)
        r = requests.get(url)
        d = json.loads(r.content)
        return d

    @db.transaction(is_commit=True)
    def query_feature(self, mysql_cur):
        print u"==================生成tid====================="
        print datetime.now()
        mysql_db = db.MysqlDbUtil(mysql_cur)
        rds_conn = db.rds_conn
        sql = "SELECT F.`id`,F.`tid` FROM `face` AS F \
    INNER JOIN `user_profile` AS UP ON UP.`id`=F.`user_id` " \
              "WHERE F.`status`=0 AND UP.`status`=1 " \
              "ORDER BY F.`id` ASC LIMIT 100"
        setnx_key = rds_conn.setnx('query_feature', 1)
        if setnx_key:
            try:
                results = mysql_db.query(sql)
                for row in results:
                    d = self._get_feature_by_tid(row[1])
                    results = d['result']
                    if results:
                        obj = results[0]
                        feature_status = obj['feature_status']
                        if feature_status == 2:
                            feature = obj['feature']
                            d = {
                                '`id`': row[0],
                                '`feature`': feature,
                                '`feature_crc`': zlib.crc32(
                                    base64.b64decode(feature)),
                                '`status`': 1  # 处理完成
                            }
                            mysql_db.update(d, table_name='`face`')

                        elif feature_status in [0, 1]:
                            continue
                        elif feature_status == 3:
                            d = {
                                '`id`': row[0],
                                '`status`': 11  # 11生成feature失败
                            }
                            mysql_db.update(d, table_name='`face`')
                    else:
                        # 如果results为空,修改状态为-1未处理
                        d = {
                            '`id`': row[0],
                            '`status`': -1  # -1未处理
                        }
                        mysql_db.update(d, table_name='`face`')
            finally:
                rds_conn.delete('query_feature')


class EveryMinuteExe(object):

    @db.transaction(is_commit=True)
    def every_minute_execute(self, mysql_cur):
        """每分钟执行一次"""
        print u"==================每分钟执行一次====================={}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print datetime.now()

        mysql_db = db.MysqlDbUtil(mysql_cur)
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
                    result = mysql_db.get(sql.format(tid))
                    if result:
                        face_id = result[0]
                        d = {
                            '`id`': face_id,
                            '`status`': 11  # 生成feature失败
                        }
                        mysql_db.update(d, table_name='`face`')
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
        results = mysql_db.query(expire_sql.format(time.time()))
        for row in results:
            face_id = row[0]
            d = {
                '`id`': face_id,
                '`status`': 2  # 过期
            }
            mysql_db.update(d, table_name='`face`')

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
    def from_oss_get_face(self, mysql_cur):
        """从oss获取人脸"""
        print u"==================从oss获取人脸====================="
        print datetime.now()
        start = time.time()
        # 获取未绑定的人脸
        mysql_db = db.MysqlDbUtil(mysql_cur)
        sql = "SELECT F.`id`,F.`emp_no` FROM `face` AS F \
    INNER JOIN `user_profile` AS UP ON UP.`id`=F.`user_id` WHERE " \
              "F.`status`=-2 AND UP.`status`=1 order by rand()"
        results = mysql_db.query(sql)
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
                mysql_db.update(d, table_name='`face`')
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
        print u"==================每五分钟执行一次====================={}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

            # 服务器IP上报
            OSSAccessKeyId = 'LTAI4FyQdrFKZrydCeP2QUvx'
            OSSAccessKeySecret = 'BbPNdGxn0Qv6LpSl2jVyPhtcWiC8fu'
            OSSEndpoint = 'oss-cn-shenzhen.aliyuncs.com'
            OSSBucketName = 'animal-test-mirror'

            my_ip = urlopen('http://ip.42.pl/raw').read()

            auth = oss2.Auth(OSSAccessKeyId, OSSAccessKeySecret)
            bucket = oss2.Bucket(auth, OSSEndpoint,
                                 OSSBucketName)
            prefix = "ip"

            now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + str(
                random.randint(1, 100000)))
            bucket.put_object(prefix + '/{}.txt'.format(now), my_ip)

            # 五分钟一个连接
            data = {
                "username": "jianchao",
                "password": "jianchao"
            }
            requests.post("http://47.108.201.70/user/login",
                          json.dumps(data),
                          headers={'Content-Type': 'application/json'})
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