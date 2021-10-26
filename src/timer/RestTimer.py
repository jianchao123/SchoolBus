# coding:utf-8
import time
import base64
import json
import oss2
import random
import requests
import hashlib
import string
from collections import defaultdict
from datetime import datetime, timedelta
from urllib2 import urlopen

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
from msgqueue import producer

from timer import db
from define import RedisKey
from define import grade, classes
from utils import aip_word_to_audio, oss_file_exists
import config


def pub_msg(rds_conn, devname, jdata):
    #print u"-----------加入顺序发送消息的队列--------"
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

        # 等待生成中
        sql = "SELECT id,stu_no,nickname,face_id " \
              "FROM audio WHERE status=1 LIMIT 27"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:

            oss_key = 'audio/' + row[1] + '.aac'
            try:
                aip_word_to_audio(row[2], oss_key)
                aac_url_str = "http://" + config.OSSDomain + '/' + oss_key
                d = {
                    'id': row[0],
                    'aac_url': aac_url_str,
                    'status': 3     # 生成成功
                }
                pgsql_db.update(pgsql_cur, d, table_name='audio')
            except:
                d = {
                    'id': row[0],
                    'status': 4  # 生成失败
                }
                pgsql_db.update(pgsql_cur, d, table_name='audio')

        end = time.time()
        #print u"{}个aac总共用时{}s".format(len(results), end - begin)


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
            if face_ids:
                self.acc_business(rds_conn, dev_name, time_diff, face_ids, periods)
            else:
                # 若没有人滞留,删除acc key
                rds_conn.hdel(RedisKey.ACC_CLOSE, dev_name)

    @db.transaction(is_commit=True)
    def acc_business(self, pgsql_cur, rds_conn, dev_name,
                     time_diff, face_ids, periods):
        pgsql_db = db.PgsqlDbUtil

        # TODO 缓存
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
            device_cur_person_number = rds_conn.hget(
                RedisKey.DEVICE_CUR_PEOPLE_NUMBER, dev_name)
            if not device_cur_person_number:
                rds_conn.hdel(RedisKey.ACC_CLOSE, dev_name)
                return
            #number = int(device_cur_person_number)
            number = len(face_ids.split(","))
            if number:

                # 是否已经添加报警记录
                alert_info = pgsql_db.get(
                    pgsql_cur, get_alert_info_sql.format(periods))
                if alert_info:
                    return

                # TODO 设备启动时缓存工作人员信息
                # 工作人员
                sql = "SELECT id,nickname,duty_id,open_id FROM worker " \
                      "WHERE car_id={}".format(car_id)
                results = pgsql_db.query(pgsql_cur, sql)
                worker_id_1 = None
                worker_name_1 = ""
                worker_id_2 = None
                worker_name_2 = ""
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
                      "STU.class_id,STU.mobile_1,STU.mobile_2,STU.id FROM " \
                      "face F INNER JOIN student STU ON STU.id=F.stu_id " \
                      "INNER JOIN school SHL ON SHL.id=STU.school_id " \
                      "WHERE F.id in ({})".format(face_ids)
                results = pgsql_db.query(pgsql_cur, sql)
                stu_id_list = []

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
                    stu_id_list.append(str(row[6]))
                people_info_list = []
                for info in student_info:
                    people_info_list.append('{},{},{},{},{}'.format(
                        info['nickname'], info['school_name'],
                        info['grade_name'], info['class_name'],
                        info['mobile_1'], info['mobile_2']))

                people_info = "|".join(people_info_list)

                current_gps = rds_conn.hget(RedisKey.DEVICE_CUR_GPS, dev_name)
                if not current_gps:
                    current_gps = ''
                d = {
                    'car_id': car_id,
                    'license_plate_number': license_plate_number,
                    'company_name': company_name,
                    'people_number': number,
                    'people_info': people_info,
                    'first_alert': 1,
                    'second_alert': 0,
                    'alert_start_time': 'NOW()',
                    'gps': current_gps[:30],
                    'status': 1,         # 正在报警
                    'periods': periods,
                    'stu_ids': ','.join(stu_id_list)
                }
                if worker_id_1:
                    d['worker_id_1'] = worker_id_1
                    d['worker_name_1'] = worker_name_1
                if worker_id_2:
                    d['worker_id_2'] = worker_id_2
                    d['worker_name_2'] = worker_name_2
                print d
                send_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                pgsql_db.insert(pgsql_cur, d, 'alert_info')
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

                # TODO 设备启动时缓存工作人员信息
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


class DeviceMfrList(object):
    """将设备按照厂商分开存储到redis"""

    @db.transaction(is_commit=True)
    def device_mfr_list(self, pgsql_cur):
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        sql = "SELECT id,mfr_id,device_name FROM device " \
              "WHERE device_type = 2 AND status != 10"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            device_name = row[2]
            mfr_id = row[1]
            rds_conn.hset(RedisKey.MFR_GENERATE_DEVICE_HASH, device_name, str(mfr_id))


class GenerateFeature(object):
    """生成feature 2秒执行一次"""

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
        print "------------unused_devices-----------------"
        print unused_devices

        mfr_dict = {}
        for dev_name, mfr_id in rds_conn.hgetall(RedisKey.MFR_GENERATE_DEVICE_HASH).items():
            mfr_pk = str(mfr_id)
            if mfr_pk in mfr_dict:
                mfr_dict[mfr_pk].append(dev_name)
            else:
                mfr_dict[mfr_pk] = [dev_name]

        # 将未使用的设备按照厂商分开
        for mfr_id, device_name_list in mfr_dict.items():

            invalid_devices = list(set(device_name_list) & set(unused_devices))
            unused_devices = list(set(unused_devices) - set(invalid_devices))

            # 等待生成状态中
            sql = "SELECT face_id,oss_url,id FROM feature " \
                  "WHERE status = 1 AND mfr_id={} LIMIT {}" \
                  "".format(int(mfr_id), len(invalid_devices))
            results = pgsql_db.query(pgsql_cur, sql)
            for row in results:
                face_id = row[0]
                oss_url = row[1]
                pk = row[2]
                # 判断oss文件是否存在
                if oss_url and \
                        oss_file_exists('person' + oss_url.split("person")[-1]):

                    jdata["fid"] = face_id
                    jdata['faceurl'] = oss_url
                    device_name = invalid_devices.pop()
                    pub_msg(rds_conn, device_name, jdata)
                    # 将设备置为使用中
                    rds_conn.hset(RedisKey.DEVICE_USED, device_name, int(time.time()))
                    # 更新feature状态
                    d = {
                        'id': pk,
                        'status': 2     # 生成中
                    }
                    pgsql_db.update(pgsql_cur, d, table_name='feature')


class FaceGenerateIsfinish(object):
    """检测学生人脸特征码和语音是否生成完成
    1.根据feature和audio状态决定face状态
    2.将feature feature_crc aac_url放到face表

    """

    @db.transaction(is_commit=True)
    def face_generate_is_finish(self, sql_cur):
        sql_db = db.PgsqlDbUtil

        # face处理中的状态
        mfr_sql = "SELECT count(id) FROM manufacturer WHERE status=1 LIMIT 1"
        face_sql = "SELECT id FROM face WHERE status in (2,3) LIMIT 50"
        feature_sql = "SELECT status FROM feature WHERE face_id={}"
        audio_sql = "SELECT status,aac_url FROM audio WHERE face_id={} LIMIT 1"
        mfr_cnt = int(sql_db.get(sql_cur, mfr_sql)[0])
        results = sql_db.query(sql_cur, face_sql)
        for row in results:
            pk = row[0]
            # 查询feature audio表
            feature_set = sql_db.query(sql_cur, feature_sql.format(pk))
            audio_row = sql_db.get(sql_cur, audio_sql.format(pk))
            feature_success_cnt = 0
            # 是否生成成功
            for feature_row in feature_set:
                # 所有feature都是成功状态
                if feature_row[0] == 3:
                    feature_success_cnt += 1
            if feature_success_cnt == mfr_cnt and audio_row[0] == 3:
                data = {
                    'id': pk,
                    'status': 4    # 处理完成
                }
                sql_db.update(sql_cur, data, table_name='face')

            # 是否生成失败
            status_fail_cnt = 0
            status_sum = 0
            for feature_row in feature_set:
                # 失败状态
                if feature_row[0] == 4:
                    status_fail_cnt += 1
                if feature_row[0] in [3, 4]:
                    status_sum += 1
            db.logger.error("status_fail_cnt={},type={}.status_sum={},type={}".format(status_fail_cnt, type(status_fail_cnt), status_sum, type(status_sum)))
            if (status_fail_cnt and status_sum == mfr_cnt) or audio_row[0] == 4:
                data = {
                    'id': pk,
                    'status': 5    # 失败
                }
                sql_db.update(sql_cur, data, table_name='face')


class EveryMinuteExe(object):

    @db.transaction(is_commit=True)
    def every_minute_execute(self, pgsql_cur):
        """每分钟执行一次"""
        mysql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        cur_date = datetime.now().strftime('%Y-%m-%d')

        # 超过70分钟清除student_set
        timestatmp_d = rds_conn.hgetall(RedisKey.DEVICE_CUR_TIMESTAMP)
        for dev_name, dev_timestamp in timestatmp_d.items():
            if int(time.time()) > (int(dev_timestamp) + 60*70):
                print "clear student set"
                rds_conn.delete(RedisKey.STUDENT_SET.format(dev_name))

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

        start = time.time()
        # 获取未绑定的人脸
        mysql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        # 最近是否上传人脸zip
        upload_timestamp = rds_conn.get(RedisKey.UPLOAD_ZIP_TIMESTAMP)
        if upload_timestamp and (start - int(upload_timestamp) > 600):
            return

        feature_sql = "SELECT id FROM feature WHERE face_id={}"

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

            for stuno in intersection:
                oss_url_str = 'http://' + config.OSSDomain + "/person/face/" + stuno + ".png"
                d = {
                    'id': stu_no_pk_map[stuno],
                    'oss_url': oss_url_str,
                    'status': 2  # 未处理
                }
                mysql_db.update(pgsql_cur, d, table_name='face')

                # 将oss_url放到feature
                feature_set = mysql_db.query(
                    pgsql_cur, feature_sql.format(stu_no_pk_map[stuno]))
                for feature_row in feature_set:
                    feature_pk = feature_row[0]
                    feature_d = {
                        'id': feature_pk,
                        'oss_url': oss_url_str,
                        'status': 1
                    }
                    mysql_db.update(pgsql_cur, feature_d, table_name='feature')

            rds_conn.delete(RedisKey.OSS_ID_CARD_SET + "CP")
        end = time.time()
        #print u"从oss获取人脸函数总共用时{}s".format(end - start)


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
        rds_conn = db.rds_conn
        if not rds_conn.get("HEART_BEAT"):
            return
        start = time.time()
        func_list = []
        prefix = 'dev_'
        for inx in range(3, 2003):
            dev_name = prefix + str(inx)
            run_status = self.remote_rds_conn.hget('DEVICE_INFO_' + dev_name, 'run_status')
            if run_status and int(run_status) and dev_name != "newdev":
                #func_list.append(gevent.spawn(self.heartbeat_func, dev_name))
                self.heartbeat_func(dev_name)

        #gevent.joinall(func_list)
        end = time.time()
        #print "Time. ={}".format(end - start)

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
        self.bucket = oss2.Bucket(self.auth, config.OSSEndpointInternal, config.OSSBucketName)

        self.client = AcsClient(config.MNSAccessKeyId,
                                config.MNSAccessKeySecret, 'cn-shanghai')
        self.product_key = config.Productkey

    @db.transaction(is_commit=False)
    def every_few_minutes_execute(self, pgsql_cur):
        """
        每五分钟执行一次 删除不规则人脸
        :return:
        """
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        try:
            # 厂商设备分类
            sql = 'SELECT device_name,mfr_id FROM device WHERE status!=10'
            results = pgsql_db.query(pgsql_cur, sql)
            for row in results:
                device_name = row[0]
                mfr_id = row[1]
                if mfr_id == 1:
                    rds_conn.hset(
                        RedisKey.MFR_DEVICE_HASH, device_name, 'WUHAN')
                elif mfr_id == 2:
                    rds_conn.hset(
                        RedisKey.MFR_DEVICE_HASH, device_name, 'SHENZHEN')

            # 从oss拉取图片名字存到redis
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
                    if comma_arr and comma_arr[-1] in ['JPG', 'jpg', 'JPEG', 'jpeg']:
                        is_del = 1
                if is_del:
                    self.bucket.delete_object(obj.key)
            if config.env == "PRO":
                try:
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
                    pass
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
            "to_timestamp('{}', 'yyyy-MM-dd hh24:mi:ss') and alert_start_time < " \
            "to_timestamp('{}', 'yyyy-MM-dd hh24:mi:ss')  LIMIT 1"
        this_week_alert_number = sql_db.get(cursor, alert_sql.format(
            this_week_start_str + ' 00:00:00', this_week_end_str + ' 23:59:59'))
        this_week_alert_number = this_week_alert_number[0] if this_week_alert_number else 0

        last_week_alert_number = sql_db.get(cursor, alert_sql.format(
            last_week_start_str + ' 00:00:00', last_week_end_str + ' 23:59:59'))
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


class UploadAlarmData(object):
    """上传报警数据到监控中心"""

    access_key_id = "hnxccs8865"
    access_key_secret = "3422af52-9905-4965-b678-18c0a99fc106"
    access_token = "76D1B5030005F6474A3230013A7B9884"

    @staticmethod
    def _get_created():
        import pytz
        now = datetime.now()
        return now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    @db.transaction(is_commit=True)
    def upload_alarm_data(self, cursor):

        rds_conn = db.rds_conn
        sql_db = db.PgsqlDbUtil

        sc_alarm_last_id = rds_conn.get(RedisKey.SC_ALARM_LAST_ID)
        if not sc_alarm_last_id:
            sc_alarm_last_id = 0
        else:
            sc_alarm_last_id = int(sc_alarm_last_id)

        stu_sql = "SELECT stu_no,nickname FROM student WHERE id in ({})"

        sql = "SELECT license_plate_number,alert_start_time,status," \
              "people_number,stu_ids,cancel_worker_name,cancel_reason,id,gps " \
              "FROM alert_info WHERE id > {} AND " \
              "alert_start_time::timestamp(0) + '10 min' < now()" \
              " ORDER BY id ASC LIMIT 1"
        results = sql_db.query(cursor, sql.format(sc_alarm_last_id))
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Content-Length': 0,
            'Content-MD5': '',
            'Authorization': 'WSSE profile="UsernamePwd"',
            'X-WSSE': 'UsernamePwd Username="{}", '
                      'PasswordDigest="{}",Nonce="{}",Created="{}"'

        }
        nonce = ''.join(random.sample(string.ascii_letters + string.digits, 16))
        send_time = int(time.time() * 1000)
        create_timestamp = UploadAlarmData._get_created()
        created = UploadAlarmData._get_created()

        #print "----------------sc alarm---------------"
        #print results

        alarm_list = []
        if results:
            for row in results:
                license_plate_number = row[0]
                alert_start_time = row[1]
                status = row[2]
                people_number = row[3]
                stu_ids = row[4]
                cancel_worker_name = row[5]
                cancel_reason = row[6]
                pk = row[7]
                gps_str = row[8]

                # 默认的
                if not gps_str or gps_str == "116.290435,40.032377":
                    longitude = 0
                    latitude = 0
                else:
                    gps_arr = gps_str.split(",")
                    longitude = int(float(gps_arr[0]) * (10 ** 6))
                    latitude = int(float(gps_arr[1]) * (10 ** 6))

                alert_start_time = int(time.mktime(alert_start_time.timetuple())) * 1000
                alarm_status = 1 if status == 1 else 0
                stu_results = sql_db.query(cursor, stu_sql.format(stu_ids))
                stu_info_list = []
                for stu in stu_results:
                    stu_info_list.append(
                        {'studentName': stu[1], 'studentId': stu[0]})

                alarm_list.append({'licensePlate': license_plate_number,
                                   'plateColor': '黄',
                                   'alarmTime': alert_start_time,
                                   'alarmType': 2,
                                   'alarmStatus': alarm_status,
                                   'studentCount': people_number,
                                   'studentInfo': stu_info_list,
                                   'alarmOffName': cancel_worker_name,
                                   'alarmOffReason': cancel_reason,
                                   'flag': 0,
                                   'sendTime': send_time,
                                   'longitude': longitude,
                                   'latitude': latitude})
            data_dict = {"version": "1.0", "dataType": 1, "data": alarm_list}
            data = json.dumps(data_dict, ensure_ascii=False)
            db.logger.error(data) # 用print 打印会少一个studentInfo
            headers['Content-Length'] = str(len(data))
            m = hashlib.md5()
            m.update(data)
            content_md5 = base64.b64encode(bin(int(m.hexdigest(), 16))[2:])
            headers['Content-MD5'] = content_md5

            password_digest = \
                nonce + str(create_timestamp) + \
                UploadAlarmData.access_key_secret + content_md5
            password_digest = \
                base64.b64encode(
                    hashlib.sha1(password_digest.encode('utf8')).hexdigest())
            headers['X-WSSE'] = \
                headers['X-WSSE'].format(
                    UploadAlarmData.access_key_id, password_digest, nonce, created)
            headers['ACCESS_TOKEN'] = UploadAlarmData.access_token

            res = requests.post(config.SC_URL, data, headers=headers)
            #print res.content
            if res.status_code == 200:
                # 上传成功修改redis  key
                #print "----------------------xwsse-------------------------"
                #print headers
                #print res.content
                rds_conn.set(RedisKey.SC_ALARM_LAST_ID, results[-1][7])


class EveryDayOneClock(object):

    def everyday_one_clock(self):
        """
        每日一点执行
        """
        rds_conn = db.rds_conn
        rds_conn.delete(RedisKey.REMOVE_DUP_ORDER_SET)