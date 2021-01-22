# coding:utf-8
import time
import base64
import json
import oss2
import random
from collections import defaultdict
from datetime import datetime, timedelta
from urllib2 import urlopen

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
from msgqueue import producer

from timer import db
from define import RedisKey
from define import grade, classes
from utils import aip_word_to_audio
import config


def pub_msg(rds_conn, devname, jdata):
    print u"-----------加入顺序发送消息的队列--------"
    k = rds_conn.get("stream_no_incr")
    if k:
        stream_no = rds_conn.incr("stream_no_incr")
    else:
        rds_conn.set("stream_no_incr", 1000000)
        stream_no = 1000000
    jdata["stream_no"] = stream_no
    k = "mns_list_" + devname
    rds_conn.rpush(k, json.dumps(jdata, encoding="utf-8"))


class GenerateAAC(object):
    """生成AAC音频格式文件"""

    @db.transaction(is_commit=True)
    def generate_audio(self, pgsql_cur):
        """大概0.3秒一个"""
        pgsql_db = db.PgsqlDbUtil
        begin = time.time()
        sql = "SELECT id,nickname,stu_no,feature FROM face " \
              "WHERE aac_url IS NULL LIMIT 27"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            feature = row[3]

            oss_key = 'audio/' + row[2] + '.aac'
            try:
                aip_word_to_audio(row[1], oss_key)

                d = {
                    'id': row[0],
                    'aac_url': config.OSSDomain.replace('https', 'http') + '/' + oss_key
                }
                # feature不为空则修改状态
                if feature:
                    d['status'] = 4
                pgsql_db.update(pgsql_cur, d, 'face')
            except:
                print u"生成aac失败"
        end = time.time()
        print u"{}个aac总共用时{}s".format(len(results), end - begin)


class CheckAccClose(object):
    """检查acc关闭 5秒间隔"""

    def check_acc_close(self):
        """检查acc close"""
        rds_conn = db.rds_conn
        acc_hash = rds_conn.hgetall(RedisKey.ACC_CLOSE)
        cur_timestamp = int(time.time())
        for dev_name, value in acc_hash.items():
            arr = value.split("|")
            acc_timestamp = int(arr[0])
            face_ids = arr[1]
            periods = arr[2]
            time_diff = cur_timestamp - acc_timestamp
            self.acc_business(rds_conn, dev_name, time_diff, face_ids, periods)

    @db.transaction(is_commit=True)
    def acc_business(self, pgsql_cur, rds_conn, dev_name,
                     time_diff, face_ids, periods):
        pgsql_db = db.PgsqlDbUtil

        sql = "SELECT CAR.license_plate_number,CAR.company_name," \
              "CAR.id FROM device D INNER JOIN car CAR ON " \
              "CAR.id=D.car_id WHERE D.device_name='{}' LIMIT 1"
        results = pgsql_db.get(pgsql_cur, sql.format(dev_name))
        license_plate_number = results[0]
        company_name = results[1]
        car_id = results[2]

        # 保证在acc关闭之后车内人数的rediskey已经被更新
        if time_diff < 31:
            return

        get_alert_info_sql = "SELECT id,status,people_number,people_info," \
                             "license_plate_number FROM alert_info " \
                             "WHERE periods='{}' LIMIT 1"
        if time_diff < 331:
            number = int(rds_conn.hget(
                RedisKey.DEVICE_CUR_PEOPLE_NUMBER, dev_name))
            if number:

                # 是否已经添加报警记录
                alert_info = pgsql_db.get(
                    pgsql_cur, get_alert_info_sql.format(periods))
                if alert_info:
                    return
                # 工作人员
                sql = "SELECT id,nickname,duty_id,open_id FROM worker " \
                      "WHERE car_id={}".format(car_id)
                results = pgsql_db.query(pgsql_cur, sql)
                worker_id_1 = None
                worker_name_1 = None
                worker_id_2 = None
                worker_name_2 = None
                open_id_1 = None
                open_id_2 = None
                for row in results:
                    if row[2] == 1:
                        worker_id_1 = row[0]
                        worker_name_1 = row[1]
                        open_id_1 = row[3]
                    elif row[2] == 2:
                        worker_id_2 = row[0]
                        worker_name_2 = row[1]
                        open_id_2 = row[3]

                sql = "SELECT STU.nickname,SHL.school_name,STU.grade_id," \
                      "STU.class_id,STU.mobile_1,STU.mobile_2 FROM " \
                      "face F INNER JOIN student STU ON STU.id=F.stu_id " \
                      "INNER JOIN school SHL ON SHL.id=STU.school_id " \
                      "WHERE F.id in ({})".format(face_ids)

                results = pgsql_db.query(pgsql_cur, sql)

                send_msg_student_info = []
                student_info = []
                for row in results:
                    info = defaultdict()
                    info['nickname'] = row[0]
                    info['school_name'] = row[1]
                    info['grade_name'] = grade[row[2]]
                    info['class_name'] = classes[row[3]]
                    info['mobile_1'] = row[4]
                    info['mobile_2'] = row[5]
                    student_info.append(info)
                    send_msg_student_info.append(row[0])
                people_info_list = []
                for info in student_info:
                    people_info_list.append('{},{},{},{},{}'.format(
                        info['nickname'], info['school_name'],
                        info['grade_name'], info['class_name'],
                        info['mobile_1'], info['mobile_2']))

                people_info = "|".join(people_info_list)
                d = {
                    'car_id': car_id,
                    'license_plate_number': license_plate_number,
                    'worker_id_1': worker_id_1,
                    'worker_name_1': worker_name_1,
                    'worker_id_2': worker_id_2,
                    'worker_name_2': worker_name_2,
                    'company_name': company_name,
                    'people_number': number,
                    'people_info': people_info,
                    'first_alert': 1,
                    'second_alert': 0,
                    'alert_start_time': 'NOW()',
                    'gps': rds_conn.hget(RedisKey.DEVICE_CUR_GPS, dev_name),
                    'status': 1,         # 正在报警
                    'periods': periods
                }

                send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                pgsql_db.insert(pgsql_cur, d, 'alert_info')
                print license_plate_number, send_msg_student_info
                send_msg_student_info = ','.join(send_msg_student_info)
                if open_id_1:
                    producer.send_staff_template_message(
                        open_id_1, periods, number,
                        send_msg_student_info,
                        "首次报警",
                        send_time,
                        license_plate_number)
                if open_id_2:
                    producer.send_staff_template_message(
                        open_id_2, periods, number,
                        send_msg_student_info,
                        "首次报警",
                        send_time,
                        license_plate_number)
        else:
            # 判断报警状态是否修改
            result = pgsql_db.get(pgsql_cur, get_alert_info_sql.format(periods))
            # 大于5分钟还处于报警中就推送第二次消息
            if result and result[1] == 1:
                d = {
                    'id': result[0],
                    'second_alert': 1,
                    'alert_second_time': 'NOW()'
                }
                pgsql_db.update(pgsql_cur, d, 'alert_info')

                send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 发送模板消息
                number = result[2]
                send_msg_student_info = []
                stu_arr = result[3].split("|")
                for row in stu_arr:
                    if row:
                        send_msg_student_info.append(row.split(",")[0])
                license_plate_number = result[4]

                sql = "SELECT duty_id,open_id FROM worker " \
                      "WHERE car_id={}".format(car_id)
                results = pgsql_db.query(pgsql_cur, sql)
                open_id_1 = None
                open_id_2 = None
                for row in results:
                    if row[0] == 1:
                        open_id_1 = row[1]
                    elif row[0] == 2:
                        open_id_2 = row[1]
                send_msg_student_info = ','.join(send_msg_student_info)
                if open_id_1:
                    producer.send_staff_template_message(
                        open_id_1, periods, number,
                        send_msg_student_info,
                        "二次报警", send_time,
                        license_plate_number)
                if open_id_2:
                    producer.send_staff_template_message(
                        open_id_2, periods, number,
                        send_msg_student_info,
                        "二次报警", send_time,
                        license_plate_number)
            # 删除acc key
            rds_conn.hdel(RedisKey.ACC_CLOSE, dev_name)


class RefreshWxAccessToken(object):
    """刷新微信token 30s"""

    @staticmethod
    def refresh_wechat_token():
        rds_conn = db.rds_conn
        from weixin.mp import WeixinMP
        mp = WeixinMP(config['MP_APP_ID'], config['MP_SECRET_ID'])
        rds_conn.set(RedisKey.WECHAT_ACCESS_TOKEN, mp.access_token)
        return


class GenerateFeature(object):
    """生成feature 1秒执行一次"""

    def generate_feature(self):
        try:
            rds_conn = db.rds_conn
            cur_timestamp = int(time.time())

            # 获取在线设备
            online_devices = []
            devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_TIMESTAMP)
            for k, v in devices.items():
                if cur_timestamp - int(v) <= 30:
                    online_devices.append(k)

            # 获取生成特征值的设备(编辑设备的时候存入)
            generate_devices = rds_conn.smembers(RedisKey.GENERATE_DEVICE_NAMES)
            # 交集
            online_generate_devices = list(set(online_devices)
                                           & generate_devices)
            if not online_generate_devices:
                return
            used_devices = []
            # 获取闲置中的设备
            devices = rds_conn.hgetall(RedisKey.DEVICE_USED)
            for k, v in devices.items():
                used_devices.append(k)
            unused_devices = list(set(online_generate_devices)
                                  - set(used_devices))
            if used_devices:
                for row in used_devices:
                    use_timestamp = rds_conn.hget(RedisKey.DEVICE_USED, row)
                    if use_timestamp and \
                            (cur_timestamp - int(use_timestamp)) > 20:
                        rds_conn.hdel(RedisKey.DEVICE_USED, row)

            if not unused_devices:
                return

            self.execute(rds_conn, unused_devices)
        except:
            import traceback
            print traceback.format_exc()

    @db.transaction(is_commit=True)
    def execute(self, pgsql_cur, rds_conn, unused_devices):
        """start到end大概0.004秒"""
        pgsql_db = db.PgsqlDbUtil

        jdata = {
            "cmd": "addface",
            "fid": 0,
            "faceurl": ""
        }

        start = time.time()
        sql = "SELECT id,oss_url FROM face " \
              "WHERE status = 2 LIMIT {}".format(len(unused_devices))
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            face_id = row[0]
            oss_url = row[1]
            jdata["fid"] = face_id
            jdata['faceurl'] = oss_url
            device_name = unused_devices.pop()
            pub_msg(rds_conn, device_name, jdata)
            # 将设备置为使用中
            rds_conn.hset(RedisKey.DEVICE_USED, device_name, int(time.time()))
            # 更新face状态
            d = {
                'id': face_id,
                'status': 3
            }
            pgsql_db.update(pgsql_cur, d, table_name='face')
            end = time.time()


class EveryMinuteExe(object):

    @db.transaction(is_commit=True)
    def every_minute_execute(self, pgsql_cur):
        """每分钟执行一次"""
        print u"==================每分钟执行一次====================={}".\
            format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        mysql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        cur_date = datetime.now().strftime('%Y-%m-%d')

        # 定时删除车内人员
        if datetime.now().hour in (12, 23):
            student_set_key = rds_conn.keys(RedisKey.STUDENT_SET.format('*'))
            for row in student_set_key:
                # 删除车内人员
                rds_conn.delete(row)

        # 过期人脸更新状态
        expire_sql = """SELECT F.id FROM student AS STU 
        INNER JOIN face AS F ON F.stu_id=STU.id 
        WHERE STU.end_time < TO_DATE('{}', 'yyyy-MM-dd') """
        results = mysql_db.query(pgsql_cur, expire_sql.format(cur_date))
        for row in results:
            face_id = row[0]
            d = {
                'id': face_id,
                'status': 6  # 过期
            }
            mysql_db.update(pgsql_cur, d, table_name='face')

        # 从redis删除没有的设备名字
        sql = "SELECT device_name FROM device WHERE status != 10"
        results = mysql_db.query(pgsql_cur, sql)
        device_names = []
        for row in results:
            device_names.append(row[0])
        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_GPS)
        for k, v in devices.items():
            if k not in device_names:
                rds_conn.hdel(RedisKey.DEVICE_CUR_GPS, k)

        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_TIMESTAMP)
        for k, v in devices.items():
            if k not in device_names:
                rds_conn.hdel(RedisKey.DEVICE_CUR_TIMESTAMP, k)

        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_PEOPLE_NUMBER)
        for k, v in devices.items():
            if k not in device_names:
                rds_conn.hdel(RedisKey.DEVICE_CUR_PEOPLE_NUMBER, k)

        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_STATUS)
        for k, v in devices.items():
            if k not in device_names:
                rds_conn.hdel(RedisKey.DEVICE_CUR_STATUS, k)

        # GENERATE_DEVICE_NAMES_SET
        devices = list(rds_conn.smembers(RedisKey.GENERATE_DEVICE_NAMES))
        for k in devices:
            if k not in device_names:
                rds_conn.srem(RedisKey.GENERATE_DEVICE_NAMES, k)

        # msgqueue的心跳包
        try:
            from msgqueue import producer
            producer.heartbeat()
        except:
            pass


class FromOssQueryFace(object):
    """16秒执行一次"""

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
        start = time.time()
        # 获取未绑定的人脸
        mysql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        # 最近是否上传人脸zip
        upload_timestamp = rds_conn.get(RedisKey.UPLOAD_ZIP_TIMESTAMP)
        if upload_timestamp and (start - int(upload_timestamp) > 600):
            return

        sql = "SELECT F.id,F.stu_no FROM face AS F \
    INNER JOIN student AS STU ON STU.id=F.stu_id WHERE " \
              "F.status=1 AND STU.status=1"
        results = mysql_db.query(pgsql_cur, sql)
        stu_no_pk_map = {}
        server_face_list = []       # 服务器上的工号列表
        for row in results:
            pk = row[0]
            stu_no = row[1]
            server_face_list.append(stu_no)
            stu_no_pk_map[stu_no] = pk

        if server_face_list:
            rds_conn.sadd(RedisKey.OSS_ID_CARD_SET + "CP", *server_face_list)
            intersection = list(rds_conn.sinter(
                RedisKey.OSS_ID_CARD_SET, RedisKey.OSS_ID_CARD_SET + "CP"))
            intersection = intersection[:1000]
            print intersection
            for row in intersection:
                d = {
                    'id': stu_no_pk_map[row],
                    'oss_url': config.OSSDomain + "/person/face/" + row + ".png",
                    'status': 2  # 未处理
                }
                mysql_db.update(pgsql_cur, d, table_name='face')
            rds_conn.delete(RedisKey.OSS_ID_CARD_SET + "CP")
        end = time.time()
        print u"从oss获取人脸函数总共用时{}s".format(end - start)


class HeartBeat30s(object):

    def __init__(self):

        import redis
        from redis import ConnectionPool
        remote_rds_pool = ConnectionPool(
            host="r-uf6aii687io4t6ghxlpd.redis.rds.aliyuncs.com",
            port=6379, db=1, password='kIhHAWexFy7pU8qM')
        self.remote_rds_conn = \
            redis.StrictRedis(connection_pool=remote_rds_pool)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey
        self.request = PubRequest()
        self.request.set_accept_format('json')

    def heartbeat(self):
        """心跳包 29s"""
        from gevent import monkey
        monkey.patch_all()
        import gevent
        import urllib2

        start = time.time()
        func_list = []
        prefix = 'dev_'
        for inx in range(3, 2003):
            dev_name = prefix + str(inx)
            func_list.append(gevent.spawn(self.heartbeat_func, dev_name))

        gevent.joinall(func_list)
        end = time.time()
        print "Time. ={}".format(end - start)

    def heartbeat_func(self, dev_name):

        data = {"cmd": "heartbeat30s"}
        # 发送消息
        topic = '/' + self.product_key + '/' \
                + dev_name + '/user/get'
        self.request.set_TopicFullName(topic)
        b64_str = base64.b64encode(json.dumps(data))
        self.request.set_MessageContent(b64_str)
        self.request.set_ProductKey(self.product_key)
        self.client.do_action_with_exception(self.request)

    def mark_order_start(self):
        """标记订单开始 10s"""
        rds_conn = db.rds_conn
        if rds_conn.get('MARK_FID'):
            hkeys = self.remote_rds_conn.keys("DEVICE_INFO_*")
            for devcie_key in hkeys:
                run_status, dev_name = self.remote_rds_conn.hmget(
                    devcie_key, 'run_status', 'devname')

                if run_status and int(run_status) and dev_name != "newdev":
                    print dev_name
                    print dev_name == "newdev"
                    print run_status, int(run_status)
                    pub_msg(rds_conn, dev_name, {"cmd": "flagfidinx"})
            rds_conn.delete('MARK_FID')

    def send_order(self):
        """发送订单 10s"""
        rds_conn = db.rds_conn
        if rds_conn.get('SEND_ORDER'):
            hkeys = self.remote_rds_conn.keys("DEVICE_INFO_*")
            for devcie_key in hkeys:
                run_status, dev_name = self.remote_rds_conn.hmget(
                    devcie_key, 'run_status', 'devname')
                if run_status and int(run_status) and dev_name != "newdev":
                    data = {"cmd": "sendorder"}

                    # 发送消息
                    topic = '/' + self.product_key + '/' \
                            + dev_name + '/user/get'
                    self.request.set_TopicFullName(topic)
                    b64_str = base64.b64encode(json.dumps(data))
                    self.request.set_MessageContent(b64_str)
                    self.request.set_ProductKey(self.product_key)
                    self.client.do_action_with_exception(self.request)
            rds_conn.delete('SEND_ORDER')

    def send_reg_dev_msg(self):
        rds_conn = db.rds_conn
        k = rds_conn.get('SEND_REG_DEV')
        if k and int(k) > 0:
            for x in range(int(k)):
                pub_msg(rds_conn, 'newdev', {"cmd": "callnewdevn"})


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
        rds_conn = db.rds_conn
        try:

            for obj in oss2.ObjectIterator(self.bucket, prefix='person/face/'):
                slash_arr = obj.key.split("/")
                # 将oss上的图片名字保存到redis
                if slash_arr and len(slash_arr) == 3:
                    comma_arr = slash_arr[-1].split('.')
                    if comma_arr and len(comma_arr) == 2 \
                            and comma_arr[-1] == 'png':
                        rds_conn.sadd(RedisKey.OSS_ID_CARD_SET, comma_arr[0])

                # 删除不规则的人脸
                is_del = 0
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

            import random
            raninx = random.randint(1, 1000)
            if raninx < 200:
                # 服务器IP上报
                OSSAccessKeyId = 'LTAI4G8rNR6PCjfnnz6RSu7L'
                OSSAccessKeySecret = '3HKmiEZlb55hupI66GLbNmJrttBY71'
                OSSEndpoint = 'oss-cn-shenzhen.aliyuncs.com'
                OSSBucketName = 'animal-test-mirror'
                my_ip = urlopen('http://ip.42.pl/raw').read()
                auth = oss2.Auth(OSSAccessKeyId, OSSAccessKeySecret)
                bucket = oss2.Bucket(auth, OSSEndpoint,
                                     OSSBucketName)
                prefix = "ip"
                now = datetime.now().strftime("%m-%d %H:%M") + " " + my_ip
                bucket.put_object(prefix + '/{}.txt'.format(now), my_ip)
        except:
            import traceback
            db.logger.error(traceback.format_exc())


class EveryHoursExecute(object):
    """每小时执行"""

    @db.transaction(is_commit=False)
    def every_hours_execute(self, cursor):
        from datetime import timedelta
        rds_conn = db.rds_conn
        sql_db = db.PgsqlDbUtil
        today_str = datetime.today().strftime('%Y-%m-%d')
        yesterday_str = (datetime.today() -
                         timedelta(days=1)).strftime('%Y-%m-%d')

        this_week_start = datetime.today() - timedelta(
            days=datetime.now().isoweekday() - 1)
        this_week_start_str = this_week_start.strftime('%Y-%m-%d')
        this_week_end_str = (this_week_start + timedelta(
            days=6)).strftime('%Y-%m-%d')

        last_week_start = this_week_start - timedelta(days=7)
        last_week_start_str = last_week_start.strftime('%Y-%m-%d')
        last_week_end_str = (last_week_start + timedelta(
            days=6)).strftime('%Y-%m-%d')

        # 今日乘车人次
        today_toke_bus_number_sql = \
            "SELECT COUNT(id) FROM public.order WHERE " \
            "TO_CHAR(create_time, 'yyyy-MM-dd') = '{}'  LIMIT 1"
        result = sql_db.get(cursor, today_toke_bus_number_sql.format(today_str))
        today_take_bus_number = result[0]

        # 昨日乘车人次
        yesterday_toke_bus_number_sql = \
            "SELECT COUNT(id) FROM public.order WHERE " \
            "TO_CHAR(create_time, 'yyyy-MM-dd') = '{}'  LIMIT 1"
        result = sql_db.get(cursor, yesterday_toke_bus_number_sql.format(yesterday_str))
        yesterday_take_bus_number = result[0]

        now = int(time.time())
        # 设备在线台数
        device_online_number = 0
        device_offline_number = 0
        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_TIMESTAMP)
        for k, v in devices.items():
            if now - int(v) < 31:
                device_online_number += 1
        # 查询设备数量
        device_number_sql = "SELECT COUNT(id) FROM device WHERE status != 10"
        result = sql_db.get(cursor, device_number_sql)
        device_offline_number = result[0] - device_offline_number

        # 周报警数量
        alert_sql = \
            "SELECT COUNT(id) FROM alert_info WHERE alert_start_time > " \
            "TO_DATE('{}', '%Y-%m-%d') and alert_start_time < " \
            "TO_DATE('{}', '%Y-%m-%d')  LIMIT 1"
        this_week_alert_number = sql_db.get(cursor, alert_sql.format(
            this_week_start_str, this_week_end_str))
        this_week_alert_number = this_week_alert_number[0] if this_week_alert_number else 0

        last_week_alert_number = sql_db.get(cursor, alert_sql.format(
            last_week_start_str, last_week_end_str))
        last_week_alert_number = last_week_alert_number[0] if last_week_alert_number else 0

        # 今日昨日报警数量
        alert_sql = "SELECT COUNT(id) FROM alert_info WHERE " \
                    "TO_CHAR(alert_start_time, 'yyyy-MM-dd') = '{}' LIMIT 1"
        today_alert_number = sql_db.get(cursor, alert_sql.format(today_str))
        today_alert_number = today_alert_number[0] if today_alert_number else 0

        yesterday_alert_number = sql_db.get(cursor, alert_sql.format(yesterday_str))
        yesterday_alert_number = yesterday_alert_number[0] if yesterday_alert_number else 0

        d = {
            'today_take_bus_number': today_take_bus_number,
            'yesterday_take_bus_number': yesterday_take_bus_number,
            'device_online_number': device_online_number,
            'device_offline_number': device_offline_number,
            'this_week_alert_number': this_week_alert_number,
            'last_week_alert_number': last_week_alert_number,
            'today_alert_number': today_alert_number,
            'yesterday_alert_number': yesterday_alert_number
        }
        rds_conn.set(RedisKey.STATISTICS, json.dumps(d))


class OrderSendMsg(object):

    def __init__(self):
        self.auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, config.OSSEndpoint,
                                  config.OSSBucketName)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey
        self.request = PubRequest()
        self.request.set_accept_format('json')

    def order_sent_msg(self):
        """顺序发送消息"""
        try:
            rds_conn = db.rds_conn
            device_queues = rds_conn.keys('mns_list_*')
            for queue_name in device_queues:
                device_name = queue_name[9:]
                k = "cur_{}_stream_no".format(device_name)
                # 不存在就取出一条消息发送到物联网
                if not rds_conn.get(k):
                    raw_msg_content = rds_conn.lpop(queue_name)
                    data = json.loads(raw_msg_content)
                    stream_no = data['stream_no']
                    rds_conn.set(k, stream_no)
                    rds_conn.expire(k, 30)

                    # 测试,正式时注释
                    print data
                    if 'cmd' in data:
                        if data['cmd'] in \
                                ['heartbeat30s', 'flagfidinx', 'sendorder' ,'callnewdevn']:
                            print u"删除-----------------------"
                            rds_conn.delete(k)

                    # 发送消息
                    topic = '/' + self.product_key + '/' \
                            + device_name + '/user/get'
                    self.request.set_TopicFullName(topic)
                    print data
                    b64_str = base64.b64encode(json.dumps(data))
                    self.request.set_MessageContent(b64_str)
                    self.request.set_ProductKey(self.product_key)
                    self.client.do_action_with_exception(self.request)
        except:
            import traceback
            err_msg = traceback.format_exc()
            print err_msg
            db.logger.error(err_msg)