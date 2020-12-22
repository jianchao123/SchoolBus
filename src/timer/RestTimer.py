# coding:utf-8
import time
import base64
import json
import oss2
from collections import defaultdict
from datetime import datetime, timedelta

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest

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
    """检查acc关闭 11秒间隔"""

    @db.transaction(is_commit=True)
    def check_acc_close(self, pgsql_cur):
        """检查acc close"""
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        acc_hash = rds_conn.hgetall(RedisKey.ACC_CLOSE)
        cur_timestamp = int(time.time())
        for dev_name, acc_timestamp in acc_hash.items():
            time_diff = cur_timestamp - acc_timestamp

            sql = "SELECT CAR.license_plate_number,CAR.company_name," \
                  "CAR.id FROM device D INNER JOIN car CAR ON " \
                  "CAR.id=D.car_id WHERE D.device_name='{}' LIMIT 1"
            results = pgsql_db.get(sql.format(dev_name))
            license_plate_number = results[0]
            company_name = results[1]
            car_id = results[2]

            self.post_wechat_msg(car_id, company_name, dev_name,
                                 license_plate_number, pgsql_cur, pgsql_db,
                                 rds_conn, time_diff)

    def post_wechat_msg(self, car_id, company_name, dev_name,
                        license_plate_number, pgsql_cur, pgsql_db, rds_conn,
                        time_diff):
        if time_diff < 35:
            return
        if time_diff < 300:
            number = int(rds_conn.hget(
                RedisKey.DEVICE_CUR_PEOPLE_NUMBER, dev_name))
            if number:
                # 工作人员
                sql = "SELECT id,nickname,duty_id FROM worker " \
                      "WHERE car_id={} LIMIT 1".format(car_id)
                results = pgsql_db.query(sql.format(dev_name))
                worker_id_1 = None
                worker_name_1 = None
                worker_id_2 = None
                worker_name_2 = None
                for row in results:
                    if row[2] == 1:
                        worker_id_1 = row[0]
                        worker_name_2 = row[1]
                    elif row[2] == 2:
                        worker_id_2 = row[0]
                        worker_name_2 = row[1]

                # 取出滞留人员
                fids = rds_conn.smembers(RedisKey.STUDENT_SET)
                fids = ','.join(list(fids))
                sql = "SELECT STU.nickname,SHL.school_name,STU.grade_id," \
                      "STU.class_id,STU.mobile_1,STU.mobile_2 FROM " \
                      "face F INNER JOIN student STU ON STU.id=F.stu_id " \
                      "INNER JOIN school SHL ON SHL.id=STU.school_id " \
                      "WHERE F.id in ({})".format(','.join(fids))
                results = pgsql_db.query(sql.format(fids))
                infos = []
                for row in results:
                    info = defaultdict()
                    info['nickname'] = row[0]
                    info['school_name'] = row[1]
                    info['grade_name'] = grade[row[2]]
                    info['class_name'] = classes[row[3]]
                    info['mobile_1'] = row[4]
                    info['mobile_2'] = row[5]
                    infos.append(info)
                people_info = ""
                for info in infos:
                    people_info += '{},{},{},{},{}|'.format(
                        info['nickname'], info['school_name'],
                        info['grade_name'], info['class_name'],
                        info['mobile_1'], info['mobile_2'])
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
                    'alert_start_time': 'now()',
                    'alert_location': '',
                    'gps': rds_conn.hget(RedisKey.DEVICE_CUR_GPS, dev_name),
                    'status': 1         # 正在报警
                }
                pgsql_db.insert(pgsql_cur, d, 'alert_info')
                # TODO 推送第一次公众号消息
        else:
            # 判断报警状态是否修改
            sql = "SELECT status FROM alert_info WHERE car_id={} " \
                  "ORDER BY id DESC LIMIT 1"
            result = pgsql_db.get(sql.format(car_id))
            # 大于5分钟还处于报警中就推送第二次消息
            if result and result[0] == 1:
                # TODO 推送第二次公众号消息
                d = {
                    'id': car_id,
                    'second_alert': 1,
                    'alert_second_time': 'now()'
                }
                pgsql_db.update(pgsql_cur, d, 'alert_info')
            # 大于5分钟直接删除Key
            rds_conn.hdel(RedisKey.ACC_CLOSE, dev_name)
            rds_conn.delete(RedisKey.STUDENT_SET.format(dev_name))


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
            unused_devices = list(set(online_generate_devices) - set(used_devices))
            print unused_devices
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
        print "-=-=-=-=-=-=-=-=-=-=-=-=-======================"
        print results
        for row in results:
            face_id = row[0]
            oss_url = row[1]
            jdata["fid"] = face_id
            jdata['faceurl'] = oss_url
            device_name = unused_devices.pop()
            pub_msg(rds_conn, device_name, jdata)
            # 将设备置为使用中
            rds_conn.hset(RedisKey.DEVICE_USED, device_name, 1)
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
            for row in intersection:
                d = {
                    'id': stu_no_pk_map[row],
                    'oss_url': config.OSSDomain + "/person/face/" + row + ".png",
                    'status': -1  # 未处理
                }
                mysql_db.update(pgsql_cur, d, table_name='face')
            rds_conn.delete(RedisKey.OSS_ID_CARD_SET + "CP")
        end = time.time()
        print u"从oss获取人脸函数总共用时{}s".format(end - start)


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
                            and comma_arr[-1] == 'jpg':
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
            "SELECT COUNT(id) FROM order WHERE " \
            "TO_CHAR(create_time, 'yyyy-MM-dd') = '{}'"
        result = sql_db.get(cursor, today_toke_bus_number_sql.format(today_str))
        today_take_bus_number = result[0]

        # 昨日乘车人次
        yesterday_toke_bus_number_sql = \
            "SELECT COUNT(id) FROM order WHERE " \
            "TO_CHAR(create_time, 'yyyy-MM-dd') = '{}'"
        result = sql_db.get(cursor, yesterday_toke_bus_number_sql.format(yesterday_str))
        yesterday_take_bus_number = result[0]

        now = int(time.time())
        # 设备在线台数
        device_online_number = 0
        device_offline_number = 0
        devices = rds_conn.hgetall(RedisKey.DEVICE_CUR_TIMESTAMP)
        for k, v in devices:
            if now - int(v) < 31:
                device_online_number += 1
        # 查询设备数量
        device_number_sql = "SELECT COUNT(id) ROM device WHERE status != 10"
        result = sql_db.get(cursor, device_number_sql)
        device_offline_number = result[0] - device_offline_number

        # 周报警数量
        alert_sql = \
            "SELECT COUNT(id) FROM alert_info WHERE alert_start_time > " \
            "TO_DATE('{}', '%Y-%m-%d') and alert_start_time < " \
            "TO_DATE('{}', '%Y-%m-%d')"
        this_week_alert_number = sql_db.get(alert_sql.format(
            this_week_start_str, this_week_end_str))
        last_week_alert_number = sql_db.get(alert_sql.format(
            last_week_start_str, last_week_end_str))

        # 今日昨日报警数量
        alert_sql = "SELECT COUNT(id) FROM alert_info WHERE " \
                    "TO_CHAR(alert_start_time, 'yyyy-MM-dd') = '{}'"
        today_alert_number = sql_db.get(alert_sql.format(today_str))
        yesterday_alert_number = sql_db.get(alert_sql.format(yesterday_str))

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
        rds_conn.hmset(RedisKey.STATISTICS, d)


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
                    self.request.set_TopicFullName(topic)

                    b64_str = base64.b64encode(json.dumps(data))
                    self.request.set_MessageContent(b64_str)
                    self.request.set_ProductKey(self.product_key)
                    self.client.do_action_with_exception(self.request)
        except:
            import traceback
            err_msg = traceback.format_exc()
            print err_msg
            db.logger.error(err_msg)