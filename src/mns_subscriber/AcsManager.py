# coding:utf-8
import os
import sys
import zlib
import time
import json
import base64
import struct
import inspect
from datetime import datetime
from collections import defaultdict

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest

from define import RedisKey, classes, grade
import db


filename = inspect.getframeinfo(inspect.currentframe()).filename
project_dir = os.path.dirname(os.path.realpath(filename))
project_dir = os.path.dirname(project_dir)
sys.path.append(project_dir)
from msgqueue import producer
import utils


class AcsManager(object):
    """注册设备"""

    def __init__(self, product_key, mns_access_key_id,
                 mns_access_key_secret, oss_domain,
                 oss_access_key_id, oss_key_secret):
        self.client = AcsClient(mns_access_key_id,
                                mns_access_key_secret, 'cn-shanghai')
        self.product_key = product_key
        self.oss_domain = oss_domain
        self.oss_access_key_id = oss_access_key_id
        self.oss_key_secret = oss_key_secret

    def _upgrade_version(self, device_name, mfr_name):
        """升级版本"""
        # 是否是深圳的设备
        if mfr_name == 'WUHAN':
            self._send_device_msg(device_name, RedisKey.WUHAN_UPGRADE_JSON)
        elif mfr_name == 'SHENZHEN':
            self._send_device_msg(device_name, RedisKey.SHENZHEN_UPGRADE_JSON)

    def _set_oss_info(self, device_name):
        """设置oss信息"""
        jdata = {
            "cmd": "ossinfo",
            "ossdomain": self.oss_domain,
            "osskeyid": self.oss_access_key_id,
            "osskeysecret": self.oss_key_secret[12:] + self.oss_key_secret[:12]
        }
        self._send_device_msg(device_name, jdata)

    # @staticmethod
    # def _pub_msg(devname, jdata):
    #     rds_conn = db.rds_conn
    #     k = rds_conn.get("stream_no_incr")
    #     if k:
    #         stream_no = rds_conn.incr("stream_no_incr")
    #     else:
    #         rds_conn.set("stream_no_incr", 1000000)
    #         stream_no = 1000000
    #
    #     jdata["stream_no"] = stream_no
    #     rds_conn.rpush("mns_list_" + devname, json.dumps(jdata, encoding="utf-8"))

    def _send_device_msg(self, devname, jdata):
        request = PubRequest()
        request.set_accept_format('json')

        topic = '/' + self.product_key + '/' + devname + '/user/get'
        request.set_TopicFullName(topic)

        message = json.dumps(jdata, encoding="utf-8")
        message = base64.b64encode(message)
        request.set_MessageContent(message)
        request.set_ProductKey(self.product_key)
        # request.set_Qos("Qos")

        response = self.client.do_action_with_exception(request)
        return json.loads(response)

    def _set_workmode(self, device_name, workmode, chepai,
                      cur_volume, person_limit):
        """
        设置设备工作模式 0车载 1通道闸口 3注册模式
        :param device_name:
        :param workmode:
        :param cur_volume:
        :return:
        """
        if workmode not in [0, 1, 3]:
            return -1
        if not cur_volume:
            cur_volume = 6

        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": chepai.encode('utf8'),
            "workmode": workmode,
            "delayoff": 7,
            "leftdetect": 2,
            "jiange": 10,
            "cleartime": 70,
            "shxmode": 0,
            "volume": int(cur_volume),
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "noreg": 0,
            "light_type": 0,
            "person_limit": int(person_limit)
        }
        return self._send_device_msg(device_name, jdata)

    @staticmethod
    def _jwd_swap(a):
        du = int(a / 100)

        fen = int(a - du * 100)
        miao = (a - du * 100 - fen) * 60
        return du + fen / 60.0 + miao / 3600.0

    @staticmethod
    def check_cur_stream_no(device_name, jdata):
        """检查当前stream_no"""
        if "stream_no" in jdata:
            from mns_subscriber import config
            #config.logger.error("------------stream_no----------------{}".format(str(jdata)))
            #print jdata
            rds_conn = db.rds_conn
            stream_no = jdata["stream_no"]
            k = "cur_{}_stream_no".format(device_name)
            rds_stream_no = rds_conn.get(k)
            if rds_stream_no and str(rds_stream_no) == str(stream_no):
                rds_conn.delete(k)

    @staticmethod
    def get_car_data(pgsql_db, pgsql_cur, redis_db, dev_name):
        """获取车辆信息
        什么时候删除缓存
        1.修改车辆
        2.修改设备
        """
        car_data = redis_db.hget(RedisKey.CACHE_CAR_DATA, dev_name)
        if not car_data:
            device_sql = """
                    SELECT dev.id,CAR.id,CAR.license_plate_number 
                    FROM device AS dev 
                    INNER JOIN car CAR ON CAR.id=dev.car_id 
                    WHERE dev.device_name='{}' LIMIT 1
                    """
            device_result = pgsql_db.get(pgsql_cur, device_sql.format(dev_name))
            cur_device_id = device_result[0]
            cur_car_id = device_result[1]
            license_plate_number = device_result[2]
            d = {'devid': cur_device_id,
                 'carid': cur_car_id,
                 'chepai': license_plate_number}
            redis_db.hset(RedisKey.CACHE_CAR_DATA, dev_name, json.dumps(d))
        else:
            d = json.loads(car_data)
        return d['devid'], d['carid'], d['chepai']

    @staticmethod
    def get_worker_data(pgsql_db, pgsql_cur, redis_db, cur_car_id):
        """
        什么时候删除缓存
        1.修改工作人员删除缓存
        """
        staff_data = redis_db.hget(RedisKey.CACHE_STAFF_DATA, str(cur_car_id))
        if not staff_data:
            worker_sql = 'SELECT duty_id,mobile,nickname ' \
                         'FROM worker WHERE car_id={}'
            driver_name = ""
            zgy_name = ""
            driver_mobile = ""
            zgy_mobile = ""
            worker_result = pgsql_db.query(
                pgsql_cur, worker_sql.format(cur_car_id))
            for row in worker_result:
                if row[0] == 1:
                    driver_name = row[2]
                    driver_mobile = row[1]
                else:
                    zgy_name = row[2]
                    zgy_mobile = row[1]
            d = {'driver_name': driver_name, 'zgy_name': zgy_name,
                 'driver_mobile': driver_mobile, 'zgy_mobile': zgy_mobile}
            redis_db.hset(RedisKey.CACHE_STAFF_DATA,
                          str(cur_car_id), json.dumps(d))
        else:
            d = json.loads(staff_data)
        return d['driver_name'], d['zgy_name'], \
               d['driver_mobile'], d['zgy_mobile']

    # @staticmethod
    # def _get_school_cache(pgsql_db, pgsql_cur, redis_db, school_id):
    #     school_name = \
    #         redis_db.hget(RedisKey.CACHE_SCHOOL_NAME_DATA, str(school_id))
    #     if not school_name:
    #         sql = "SELECT school_name FROM school " \
    #               "WHERE id={} LIMIT 1".format(school_id)
    #         school_name = pgsql_db.get(pgsql_cur, sql)[0]
    #         redis_db.hset(RedisKey.CACHE_SCHOOL_NAME_DATA,
    #                       str(school_id), school_name)
    #         return school_name
    #     else:
    #         return school_name

    @db.transaction(is_commit=True)
    def add_order(self, pgsql_cur, fid, gps_str, add_time, dev_name, cnt):
        """
        添加订单
        报警刷脸不需要,影响逻辑
        """

        redis_db = db.rds_conn
        # 因为消息队列的机制,数据可能重复,需要去重
        dup_key = str(fid) + str(add_time)
        if redis_db.sismember(RedisKey.REMOVE_DUP_ORDER_SET, dup_key):
            return
        redis_db.sadd(RedisKey.REMOVE_DUP_ORDER_SET, dup_key)
        pgsql_db = db.PgsqlDbUtil

        now = datetime.now()
        cur_hour = now.hour
        from mns_subscriber import config
        config.logger.error("------------cnt----------------{}".format(cnt))
        odd_even = cnt % 2
        # 是上车就入集合
        k = RedisKey.STUDENT_SET.format(dev_name)
        if odd_even % 2:
            redis_db.sadd(k, fid)
        else:
            redis_db.srem(k, fid)
            # 集合为空,删除acc
            if not redis_db.scard(k):
                redis_db.delete(RedisKey.ACC_CLOSE)
        if cur_hour <= 12:
            if odd_even:            # 上学上车
                order_type = 1
            elif not odd_even:      # 上学下车
                order_type = 2

        if cur_hour > 12:
            if odd_even:            # 放学上车
                order_type = 3
            elif not odd_even:      # 放学下车
                order_type = 4

        cur_device_id, cur_car_id, license_plate_number\
            = AcsManager.get_car_data(pgsql_db, pgsql_cur, redis_db, dev_name)

        driver_name, zgy_name, driver_mobile, zgy_mobile = \
            AcsManager.get_worker_data(
                pgsql_db, pgsql_cur, redis_db, cur_car_id)

        stu_sql = """
        SELECT stu.id, stu.stu_no, stu.nickname,shl.id,shl.school_name,
        stu.open_id_1,stu.open_id_2,stu.grade_id,stu.class_id FROM student stu 
        INNER JOIN face f ON f.stu_id=stu.id 
        INNER JOIN school shl ON shl.id=stu.school_id 
        WHERE f.id={} LIMIT 1
        """
        student_result = pgsql_db.get(pgsql_cur, stu_sql.format(fid))
        if not student_result:
            return
        stu_id = student_result[0]
        stu_no = student_result[1]
        stu_nickname = student_result[2]
        school_id = student_result[3]
        school_name = student_result[4]
        open_id_1 = student_result[5]
        open_id_2 = student_result[6]
        grade_id = student_result[7]
        class_id = student_result[8]

        # gps
        arr = gps_str.split(',')
        if arr[0] and arr[1]:
            longitude = AcsManager._jwd_swap(float(arr[0]))
            latitude = AcsManager._jwd_swap(float(arr[1]))
            longitude, latitude = utils.wgs84togcj02(
                float(longitude), float(latitude))
            gps_str = '{},{}'.format(longitude, latitude)
        else:
            gps_str = ''

        d = defaultdict()
        d['id'] = redis_db.incr(RedisKey.ORDER_ID_INCR)
        d['stu_no'] = stu_no
        d['stu_id'] = stu_id
        d['stu_name'] = stu_nickname
        d['school_id'] = school_id
        d['school_name'] = school_name
        d['order_type'] = order_type
        d['create_time'] = 'TO_TIMESTAMP({})'.format(add_time)
        d['up_location'] = ''
        d['gps'] = gps_str
        d['car_id'] = cur_car_id
        d['license_plate_number'] = license_plate_number
        d['device_id'] = cur_device_id
        d['fid'] = fid
        d['cur_timestamp'] = str(add_time)
        d['grade_name'] = grade[grade_id]
        d['class_name'] = classes[class_id]
        d['driver_name'] = driver_name
        d['zgy_name'] = zgy_name
        d['driver_mobile'] = driver_mobile
        d['zgy_mobile'] = zgy_mobile

        pgsql_db.insert(pgsql_cur, d, table_name='public.order')

        if order_type == 1:
            order_type_name = u"上学上车"
        elif order_type == 2:
            order_type_name = u"上学下车"
        elif order_type == 3:
            order_type_name = u"放学上车"
        else:
            order_type_name = u"放学下车"

        up_time = datetime.fromtimestamp(add_time)
        up_time_str = up_time.strftime('%Y-%m-%d %H:%M:%S')
        # 推送模板消息
        if open_id_1:
            producer.send_parents_template_message(
                open_id_1, d['id'], stu_nickname,
                order_type_name, up_time_str, license_plate_number, stu_no)
        if open_id_2:
            producer.send_parents_template_message(
                open_id_2, d['id'], stu_nickname,
                order_type_name, up_time_str, license_plate_number, stu_no)
        # 监控中心队列
        try:
            # 默认的
            if not gps_str:
                longitude = 0
                latitude = 0
            else:
                gps_arr = gps_str.split(",")
                longitude = int(float(gps_arr[0]) * (10**6))
                latitude = int(float(gps_arr[1]) * (10**6))

            state = 1 if order_type % 2 else 2
            face_time = int(add_time) * 1000

            d = {'version': '1.0', 'dataType': 2,
                 'data': [{'licensePlate': license_plate_number,
                           'plateColor': 'yellow',
                           'faceTime': face_time,
                           'state': state,
                           'flag': 0,
                           'sendTime': int(time.time() * 1000),
                           'longitude': longitude,
                           'latitude': latitude,
                           'studentName': stu_nickname,
                           'studentId': stu_no}]}
            redis_db.rpush(
                RedisKey.SC_ORDER_LIST, json.dumps(d, ensure_ascii=False))
        except:
            import traceback
            print traceback.format_exc()
            print gps_str

    @staticmethod
    def _get_created():
        import pytz
        tz = pytz.timezone('UTC')
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    def add_redis_queue(self, device_name, data, pkt_cnt):
        """
        添加到redis queue
        pkt_cnt == 0表示设备上没有人员信息，但是设备也会回传一个消息
        """
        rds_conn = db.rds_conn
        if not pkt_cnt:
            self.check_people_list([], device_name)
        else:
            pkt_inx_key = '{}_pkt_inx'.format(device_name)
            raw_queue_key = "person_raw_" + device_name
            tt = rds_conn.incr(pkt_inx_key)
            if data:
                rds_conn.rpush(raw_queue_key, json.dumps(data))
            if int(tt) == int(pkt_cnt):
                people_list = []
                raw_data = rds_conn.lpop(raw_queue_key)
                while raw_data:
                    people_list.append(raw_data)
                    raw_data = rds_conn.lpop(raw_queue_key)
                # 删除计数key
                rds_conn.delete(pkt_inx_key)
                # 删除stream_no key,因为devwhitelist指令没有返回stream_no
                rds_conn.delete("cur_{}_stream_no".format(device_name))
                self.check_people_list(people_list, device_name)

    @db.transaction(is_commit=True)
    def check_people_list(self, pgsql_cur, people_list, device_name):
        """
        检查人员列表
        (单设备检查人员是否需要更新)
        :return:
        """
        rds_conn = db.rds_conn
        pgsql_db = db.PgsqlDbUtil
        fid_dict = {}
        for row in people_list:
            data = base64.b64decode(row)
            length = len(data)
            offset = 0
            while offset < length:
                s = data[offset: offset + 16]
                ret_all = struct.unpack('<IiiI', s)
                fid = ret_all[0]
                feature_crc = ret_all[2]
                fid_dict[str(fid)] = feature_crc
                offset += 16
        print "--------------fid_dict--------------------"
        print fid_dict
        mfr_sql = "SELECT mfr_id FROM device WHERE device_name = '{}' LIMIT 1"
        mfr_pk = pgsql_db.get(pgsql_cur, mfr_sql.format(device_name))[0]

        sql = """
        SELECT f.id, ft.feature_crc,F.nickname FROM face AS F 
INNER JOIN feature AS ft ON ft.face_id=F.id 
INNER JOIN student AS stu ON stu.id=F.stu_id 
WHERE F.status=4 AND stu.status=1 AND stu.car_id={} AND ft.mfr_id={} 
        """
        device_sql = "SELECT car_id,device_type FROM device " \
                     "WHERE device_name = '{}' LIMIT 1"
        device_object = pgsql_db.get(pgsql_cur, device_sql.format(device_name))
        dev_car_id = device_object[0]
        device_type = device_object[1]

        if dev_car_id:
            device_fid_set = set(fid_dict.keys())
            results = pgsql_db.query(pgsql_cur, sql.format(dev_car_id, mfr_pk))
            face_ids = [str(row[0]) for row in results]

            add_list = list(set(face_ids) - set(device_fid_set))

            del_list = list(set(device_fid_set) - set(face_ids))

            intersection_list = list(set(face_ids) & set(device_fid_set))

            # 需要更新的feature
            update_list = []
            for row in results:
                pk = row[0]
                feature_crc = row[1]
                if str(pk) in fid_dict and str(pk) in intersection_list:
                    if feature_crc != fid_dict[str(pk)]:
                        update_list.append(str(pk))

            if rds_conn.get(RedisKey.QUERY_DEVICE_PEOPLE):
                # 保存设备上的人员到数据库
                rds_conn.delete(RedisKey.QUERY_DEVICE_PEOPLE)
                producer.device_people_list_save(
                    ",".join(people_list), face_ids, device_name)
            else:
                # 更新设备上的人员
                producer.device_people_update_msg(
                    add_list, del_list, update_list, device_name)
            print add_list, del_list, update_list
        else:
            # 刷脸设备
            if device_type == 1:
                # 清空设备所有人脸
                producer.delete_all_face(device_name)
                # 提示
                producer.update_chepai(device_name, "没有绑定车辆", 6, 0, 20)
            elif device_type == 2:
                # 清空设备所有人脸
                producer.delete_all_face(device_name)
                # 提示
                producer.update_chepai(device_name, "生成特征值专用", 6, 3, 20)

    @db.transaction(is_commit=True)
    def create_device(self, pgsql_cur, mac, shd_devid):
        """
        创建设备
        """
        from mns_subscriber import config
        rds_conn = db.rds_conn
        pgsql_db = db.PgsqlDbUtil
        config.logger.info('create device {} {}'.format(shd_devid, mac))
        # 创建设备只能顺序执行,无需使用自旋锁
        setnx_key = rds_conn.setnx('create_device', 1)
        if setnx_key:
            try:
                machine_sql = "SELECT id FROM machine WHERE mac='{}' LIMIT 1"
                dev_sql = "SELECT id FROM device WHERE mac='{}' LIMIT 1"

                obj = pgsql_db.get(pgsql_cur, dev_sql.format(mac))
                if obj:
                    return None

                sql = 'SELECT id,device_name FROM device ' \
                      'ORDER BY id DESC LIMIT 1'
                obj = pgsql_db.get(pgsql_cur, sql)
                if not obj:
                    dev_name = 'dev_1'
                else:
                    arr = obj[1].split('_')
                    prefix = arr[0]
                    suffix = arr[1]
                    dev_name = prefix + '_' + str(int(suffix) + 1)

                # 创建设备
                request = RegisterDeviceRequest()
                request.set_accept_format('json')

                request.set_ProductKey(self.product_key)
                request.set_DeviceName(dev_name)
                response = self.client.do_action_with_exception(request)
                response = json.loads(response)
                if not response['Success']:
                    config.logger.info('api create fail {}'.format(mac))
                    return None
                # 添加记录
                d = {
                    'device_name': response['Data']['DeviceName'],
                    'status': 1,
                    'mac': mac,
                    'product_key': response['Data']['ProductKey'],
                    'device_secret': response['Data']['DeviceSecret'],
                    'sound_volume': 6,
                    'license_plate_number': ''
                }
                pgsql_db.insert(pgsql_cur, d, table_name='device')

                # 发布消息注册
                msg = {
                    "cmd": "devid",
                    "devname": response['Data']['DeviceName'],
                    "productkey": response['Data']['ProductKey'],
                    "devsecret": response['Data']['DeviceSecret'],
                    "devicetype": 0,
                    "time": int(time.time()),
                    'dev_mac': mac
                }
                retd = self._send_device_msg('newdev', msg)
                config.logger.error(retd)
                rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, dev_name, 1)
                rds_conn.rpush('DEVICE_NAME_QUEUE', dev_name)

                # 存在是SHENZHEN 不存在是WUHAN
                obj = pgsql_db.get(
                    pgsql_cur, machine_sql.format(mac))
                if obj:
                    # 2是SHENZHEN
                    rds_conn.hset(RedisKey.MFR_DEVICE_HASH, dev_name,
                                  'SHENZHEN')
                else:
                    # 1是WUHAN
                    rds_conn.hset(RedisKey.MFR_DEVICE_HASH, dev_name, 'WUHAN')

            finally:
                rds_conn.delete('create_device')
        return None

    def _set_device_work_mode(self, dev_name, license_plate_number,
                              cur_volume, workmode, person_limit):
        """设置设备工作模式
        0车载 1通道闸口 3注册模式
        """
        self._set_workmode(dev_name, workmode, license_plate_number,
                           cur_volume, person_limit)

    @db.transaction(is_commit=False)
    def _init_people(self, pgsql_cur, people_list, device_name):
        pgsql_db = db.PgsqlDbUtil
        fid_dict = {}
        for row in people_list:
            data = base64.b64decode(row)
            length = len(data)
            offset = 0
            while offset < length:
                s = data[offset: offset + 16]
                ret_all = struct.unpack('<IiiI', s)
                fid = ret_all[0]
                feature_crc = ret_all[2]
                fid_dict[str(fid)] = feature_crc
                offset += 16

        sql = """
        SELECT f.id, f.feature_crc FROM face AS F
        INNER JOIN student AS stu ON stu.id=F.stu_id 
        WHERE F.status = 4 AND stu.status = 1 AND stu.car_id={} 
        """
        device_sql = "SELECT car_id FROM device " \
                     "WHERE device_name = '{}' LIMIT 1"
        dev_car_id = pgsql_db.get(pgsql_cur, device_sql.format(device_name))[0]
        if dev_car_id:
            device_fid_set = set(fid_dict.keys())
            results = pgsql_db.query(pgsql_cur, sql.format(dev_car_id))
            face_ids = [str(row[0]) for row in results]

            add_list = list(set(face_ids) - set(device_fid_set))

            # 放到消息队列
            producer.device_people_update_msg(
                add_list, [], [], device_name)

    def check_version(self, device_name, cur_version, dev_time):
        """检查版本号"""
        from mns_subscriber import config
        #config.logger.info('----current version{}----'.format(cur_version))
        rds_conn = db.rds_conn
        all_heartbeat_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rds_conn.hset(RedisKey.ALL_HEARTBEAT_HASH, device_name, all_heartbeat_val)

        mfr_name = RedisKey.get_device_mfr_name(rds_conn, device_name)
        version_k = mfr_name + '_VERSION_NO'
        if cur_version < getattr(RedisKey, version_k):
            #obj = rds_conn.hget(RedisKey.MFR_DEVICE_HASH, device_name)
            #if obj:
            self._upgrade_version(device_name, mfr_name)

    @db.transaction(is_commit=True)
    def _update_device(self, pgsql_cur, data):
        pgsql_db = db.PgsqlDbUtil
        pgsql_db.update(pgsql_cur, data, table_name='device')

    @db.transaction(is_commit=False)
    def _get_device_info_data(self, pgsql_cur, device_name):
        pgsql_db = db.PgsqlDbUtil

        sql = "SELECT id,status,version_no,sound_volume," \
              "license_plate_number,device_type,person_limit" \
              " FROM device WHERE device_name='{}' LIMIT 1"
        device = pgsql_db.get(pgsql_cur, sql.format(device_name))
        return device[0], device[1], device[2], device[3], \
               device[4], device[5], device[6]

    def init_device_params(self, cur_version, device_name,
                           dev_time, shd_devid, gps):
        """
        初始化设备参数
        """
        rds_conn = db.rds_conn

        device_status = rds_conn.hget(
            RedisKey.DEVICE_CUR_STATUS, device_name)
        # 如果没有找到这个设备直接消费掉消息
        if not device_status:
            return -10

        d = {}

        # 5表示已初始化人员
        if device_status and int(device_status) == 5:
            return 0
        pk, status, version_no, sound_volume, license_plate_number, \
            device_type, person_limit = \
            self._get_device_info_data(device_name)

        # '已创建虚拟设备'状态
        if status in [1, 2, 3, 4, 5]:
            d['device_iid'] = shd_devid

        # 设备为生成特征值设备
        if device_type == 2:
            license_plate_number = u'生成特征值专用'
            workmode = 3    # 注册模式
        else:   # device_type == 1:
            workmode = 0    # 车载模式
        # '已关联车辆'状态
        if status == 2:
            d['status'] = 3   # 已设置工作模式
            print u"设置工作模式"
            person_limit = int(person_limit) if person_limit else 40
            self._set_device_work_mode(
                device_name, license_plate_number, sound_volume,
                workmode, person_limit)
            rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, device_name, 3)
        elif status == 3:       # 已设置工作模式
            d['status'] = 4     # 设置oss信息
            print u"设置oss信息"
            self._set_oss_info(device_name)
            rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, device_name, 4)
        elif status == 4:       # 设置oss信息
            d['status'] = 5     # 初始人员
            d['device_iid'] = shd_devid
            print u"初始化人员"

            rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, device_name, 5)
            self._init_people([], device_name)

        if d:
            d['id'] = pk
            self._update_device(d)

    @db.transaction(is_commit=False)
    def _get_sound_vol_by_name(self, pgsql_cur, dev_name):
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT sound_volume,car_id,device_type " \
              "FROM device WHERE device_name='{}' LIMIT 1"
        chepai_sql = "SELECT license_plate_number FROM car WHERE id={} LIMIT 1"
        result = pgsql_db.get(pgsql_cur, sql.format(dev_name))
        car_id = result[1]
        if car_id:
            chepai = pgsql_db.get(pgsql_cur, chepai_sql.format(car_id))[0]
        else:
            chepai = ""
        return result[0], chepai, result[2]

    def device_incar_person_number(self, dev_name, cnt):
        """车内人员数"""
        rds_conn = db.rds_conn
        cur_status = rds_conn.hget(RedisKey.DEVICE_CUR_STATUS, dev_name)
        if cur_status and int(cur_status) == 5:
            rds_conn.hset(RedisKey.DEVICE_CUR_PEOPLE_NUMBER, dev_name, cnt)

    def device_rebooted_setting_open_time(self, device_name, gps, ret):
        """设备重启设备开机时间"""
        rds_conn = db.rds_conn
        # 设置设备时间戳和gps
        device_timestamp = rds_conn.hget(
            RedisKey.DEVICE_CUR_TIMESTAMP, device_name)

        # 长时间关机
        if device_timestamp and \
                int(time.time()) - int(device_timestamp) > 60 * 5 and \
                (not ret):
            producer.dev_while_list(device_name)
            pk, status, version_no, sound_volume, license_plate_number, \
                device_type, person_limit = self._get_device_info_data(device_name)
            d = defaultdict()
            d['id'] = pk
            d['open_time'] = 'TO_TIMESTAMP({})'.format(int(time.time()))
            self._update_device(d)

            # 更新设备信息
            sound_vol, license_plate_number, device_type \
                = self._get_sound_vol_by_name(device_name)
            workmode = 0 if device_type == 1 else 3
            sound_vol = int(sound_vol) if sound_vol else 100
            person_limit = int(person_limit) if person_limit else 40
            producer.update_chepai(device_name, license_plate_number,
                                   sound_vol, workmode, person_limit)
            # 设置oss set
            producer.device_oss_info(device_name)

        rds_conn.hset(RedisKey.DEVICE_CUR_TIMESTAMP, device_name,
                      int(time.time()))
        if gps == ",":
            gps_str = ""
        else:
            arr = gps.split(",")
            if arr[0] and arr[1]:
                longitude = AcsManager._jwd_swap(float(arr[0]))
                latitude = AcsManager._jwd_swap(float(arr[1]))
                longitude, latitude = utils.wgs84togcj02(
                    float(longitude), float(latitude))
                gps_str = '{},{}'.format(longitude, latitude)
            else:
                gps_str = '116.290435,40.032377'
        rds_conn.hset(RedisKey.DEVICE_CUR_GPS, device_name, gps_str)

    @db.transaction(is_commit=True)
    def save_imei(self, pgsql_cur, device_name, imei):
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT id FROM device WHERE device_name='{}' LIMIT 1"
        obj = pgsql_db.get(pgsql_cur, sql.format(device_name))
        if obj:
            d = {
                'id': obj[0],
                'imei': imei
            }
            pgsql_db.update(pgsql_cur, d, table_name='device')

    @db.transaction(is_commit=True)
    def save_feature(self, pgsql_cur, device_name, fid, feature):
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        d = defaultdict()
        mfr_id = pgsql_db.get(
            pgsql_cur, "SELECT mfr_id FROM device WHERE "
                       "device_name='{}' LIMIT 1".format(device_name))[0]
        sql = "SELECT id,face_id FROM feature " \
              "WHERE mfr_id={} AND face_id={} LIMIT 1"
        print sql.format(mfr_id, fid)
        feature_obj = pgsql_db.get(pgsql_cur, sql.format(mfr_id, fid))
        feature_id = feature_obj[0]
        face_id = feature_obj[1]
        if feature:

            d['id'] = feature_id
            d['feature'] = feature
            d['feature_crc'] = zlib.crc32(base64.b64decode(feature))
            d['status'] = 3     # 生成成功
        else:
            d['id'] = feature_id
            d['status'] = 4     # 生成失败
        pgsql_db.update(pgsql_cur, d, table_name='feature')
        # if not feature:
        #     data = {
        #         'id': face_id,
        #         'status': 5  # 预期数据准备失败
        #     }
        #     pgsql_db.update(pgsql_cur, data, table_name='face')
        # 将设备从使用中删除
        rds_conn.hdel(RedisKey.DEVICE_USED, device_name)

    def acc_close(self, device_name, add_time):
        """
        acc关闭
        向redis存入一条acc关闭的数据
        """
        rds_conn = db.rds_conn
        # 取出滞留人员
        face_ids = rds_conn.smembers(RedisKey.STUDENT_SET.format(device_name))
        face_ids = [str(row) for row in list(face_ids)]

        today = datetime.now()
        today_str = today.strftime('%Y%m%d%H%M%S')
        suffix = 'AM'
        if today.hour > 12:
            suffix = 'PM'

        # 每次acc熄火唯一key
        periods = "{}-{}-{}".format(today_str, device_name, suffix)
        value = str(add_time) + "|" + ",".join(face_ids) + "|" + periods
        rds_conn.hset(RedisKey.ACC_CLOSE, device_name, value)

    def acc_open(self, device_name):
        """
        acc开启
        """
        rds_conn = db.rds_conn
        rds_conn.hset(RedisKey.ACC_OPEN_TIME,
                      device_name, int(time.time()))

    def clear_setting(self, dev_name, seconds):
        """清除关于这台设备的一些设置"""
        rds_conn = db.rds_conn

        # 学生相关的清除
        if seconds < 20:
            rds_conn.delete(RedisKey.STUDENT_SET.format(dev_name))
            producer.clear_device_person_count(dev_name)