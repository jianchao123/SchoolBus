# coding:utf-8
import os
import sys
import time
import json
import base64
import struct
import inspect
from zlib import crc32
import decimal
from datetime import timedelta
from datetime import datetime
from aliyunsdkcore import client
from collections import defaultdict

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest

from define import RedisKey
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

    def _upgrade_version(self, device_name):
        """升级版本"""
        self._send_device_msg(device_name, RedisKey.UPGRADE_JSON)

    def _set_oss_info(self, device_name):
        """设置oss信息"""
        jdata = {
            "cmd": "ossinfo",
            "ossdomain": self.oss_domain.replace('https://', ''),
            "osskeyid": self.oss_access_key_id,
            "osskeysecret": self.oss_key_secret[12:] + self.oss_key_secret[:12]
        }
        self._send_device_msg(device_name, jdata)

    @staticmethod
    def _pub_msg(devname, jdata):
        rds_conn = db.rds_conn
        k = rds_conn.get("stream_no_incr")
        if k:
            stream_no = rds_conn.incr("stream_no_incr")
        else:
            rds_conn.set("stream_no_incr", 1000000)
            stream_no = 1000000

        jdata["stream_no"] = stream_no
        rds_conn.rpush("mns_list_" + devname, json.dumps(jdata, encoding="utf-8"))

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

    def _set_workmode(self, device_name, workmode, chepai, cur_volume):
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
            "delayoff": 10,
            "leftdetect": 5,
            "jiange": 10,
            "cleartime": 2628000,
            "shxmode": 0,
            "volume": int(cur_volume),
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "noreg": 1,
            "light_type": 0
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
            rds_conn = db.rds_conn
            stream_no = jdata["stream_no"]
            k = "cur_{}_stream_no".format(device_name)
            rds_stream_no = rds_conn.get(k)
            if rds_stream_no and str(rds_stream_no) == str(stream_no):
                rds_conn.delete(k)

    @db.transaction(is_commit=True)
    def update_device_last_time(self, pgsql_cur, device_name,
                                devtime, gps_str, device_iid):
        """
        更新设备最后在线时间
        :return:
        """
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        sql = "SELECT id,last_time FROM device " \
              "WHERE device_name='{}' LIMIT 1"
        obj = pgsql_db.get(pgsql_cur, sql.format(device_name))
        pk = obj[0]
        last_time = obj[1]
        cur_time = datetime.now()
        dev_time = datetime.fromtimestamp(int(devtime))
        if (cur_time - dev_time) > timedelta(seconds=40):
            return
        # 如果有6小时设备没在线了,就检查该设备的人员是否需要更新
        if last_time + timedelta(minutes=5) < cur_time:
            ret = rds_conn.setnx('sync_device_key', 1)
            if ret:
                try:
                    d = {
                        'id': pk,
                        'last_time': 'now()'
                    }
                    pgsql_db.update(pgsql_cur, d, table_name='device')
                    jdata = {
                        "cmd": "devwhitelist",
                        "pkt_inx": -1
                    }
                    # 发送消息之前先清除一次redis key
                    try:
                        rds_conn.delete("{}_pkt_inx".format(device_name))
                        rds_conn.delete("person_raw_{}".format(device_name))
                    except:
                        pass
                    AcsManager._pub_msg(device_name, jdata)
                except:
                    import traceback
                    print traceback.format_exc()
                finally:
                    time.sleep(1)
                    rds_conn.delete('sync_device_key')
        else:
            arr = gps_str.split(',')
            longitude = arr[0]
            latitude = arr[1]
            cur_gps = ""
            if longitude and latitude:
                longitude = AcsManager._jwd_swap(float(longitude))
                latitude = AcsManager._jwd_swap(float(latitude))
                longitude, latitude = utils.gcj_02_to_gorde_gpd(
                    str(longitude), str(latitude))
                cur_gps = str(longitude) + "," + str(latitude)

            d = {
                'id': pk,
                'last_time': 'now()',
                'cur_gps': cur_gps,
                'device_iid': device_iid
            }
            pgsql_db.update(pgsql_cur, d, table_name='device')

    @db.transaction(is_commit=True)
    def add_order(self, pgsql_cur, fid, gps_str, add_time, dev_name, cnt):
        """
        添加订单
        """
        redis_db = db.rds_conn
        pgsql_db = db.PgsqlDbUtil

        now = datetime.now()
        cur_hour = now.hour
        odd_even = cnt % 2
        # 是上车就入集合
        k = RedisKey.STUDENT_SET.format(dev_name)
        if odd_even % 2:
            redis_db.sadd(k, fid)
        else:
            redis_db.srem(k, fid)

        if cur_hour < 12 and odd_even:          # 上学上车
            order_type = 1
        elif cur_hour < 12 and not odd_even:    # 上学下车
            order_type = 2
        elif cur_hour > 12 and odd_even:        # 放学上车
            order_type = 3
        else:                                   # 放学下车
            order_type = 4

        device_sql = """
        SELECT dev.id,CAR.id,CAR.license_plate_number FROM device AS dev 
        INNER JOIN car CAR ON CAR.id=dev.car_id 
        WHERE dev.device_name='{}' LIMIT 1
        """
        device_result = pgsql_db.get(pgsql_cur, device_sql.format(dev_name))
        cur_device_id = device_result[0]
        cur_car_id = device_result[1]
        license_plate_number = device_result[2]

        stu_sql = """
        SELECT stu.id, stu.stu_no, stu.nickname,shl.id,shl.school_name FROM student stu 
        INNER JOIN face f ON f.stu_id=stu.id 
        INNER JOIN school shl ON shl.id=stu.school_id 
        WHERE f.id={} LIMIT 1
        """
        student_result = pgsql_db.get(pgsql_cur, stu_sql.format(fid))
        print student_result
        if not student_result:
            return
        stu_id = student_result[0]
        stu_no = student_result[1]
        stu_nickname = student_result[2]
        school_id = student_result[3]
        school_name = student_result[4]

        # gps
        arr = gps_str.split(',')
        longitude = AcsManager._jwd_swap(float(arr[0]))
        latitude = AcsManager._jwd_swap(float(arr[1]))
        longitude, latitude = utils.gcj_02_to_gorde_gpd(
            str(longitude), str(latitude))
        gps_str = '{},{}'.format(longitude, latitude)

        d = defaultdict()
        d['id'] = redis_db.incr(RedisKey.ORDER_ID_INCR)
        d['stu_no'] = stu_no
        d['stu_id'] = stu_id
        d['stu_name'] = stu_nickname
        d['school_id'] = school_id
        d['school_name'] = school_name
        d['order_type'] = order_type
        d['create_time'] = 'to_timestamp({})'.format(add_time)
        d['up_location'] = ''
        d['gps'] = gps_str
        d['car_id'] = cur_car_id
        d['license_plate_number'] = license_plate_number
        d['device_id'] = cur_device_id
        pgsql_db.insert(pgsql_cur, d, table_name='order')

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

        sql = """
        SELECT f.id, f.feature_crc FROM face AS F
        INNER JOIN student AS stu ON stu.id=F.stu_id 
        INNER JOIN car AS CR ON CR.id=stu.car_id 
        WHERE CR.id in (
          SELECT D.car_id FROM device AS D WHERE D.device_name = '{}'
        ) AND F.status = 4 AND stu.status = 1
        """
        device_fid_set = set(fid_dict.keys())
        results = pgsql_db.query(pgsql_cur, sql.format(device_name))
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

    @db.transaction(is_commit=True)
    def create_device(self, pgsql_cur, mac):
        """
        创建设备
        """
        rds_conn = db.rds_conn
        pgsql_db = db.PgsqlDbUtil
        # 创建设备只能顺序执行,无需使用自旋锁
        setnx_key = rds_conn.setnx('create_device', 1)
        if setnx_key:
            try:

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
                print response
                if not response['Success']:
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
                    "time": int(time.time())
                }
                self._send_device_msg('newdev', msg)
                rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, dev_name, 1)
            finally:
                rds_conn.delete('create_device')
        return None

    def _set_device_work_mode(self, dev_name, license_plate_number, cur_volume, workmode):
        """设置设备工作模式
        0车载 1通道闸口 3注册模式
        """
        self._set_workmode(dev_name, workmode, license_plate_number, cur_volume)

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
        INNER JOIN car AS CR ON CR.id=stu.car_id 
        WHERE CR.id in (
          SELECT D.car_id FROM device AS D WHERE D.device_name = '{}'
        ) AND F.status = 4 AND stu.status = 1
        """
        device_fid_set = set(fid_dict.keys())
        results = pgsql_db.query(pgsql_cur, sql.format(device_name))
        face_ids = [str(row[0]) for row in results]

        add_list = list(set(face_ids) - set(device_fid_set))

        # 放到消息队列
        producer.device_people_update_msg(
            add_list, [], [], device_name)

    def check_version(self, device_name, cur_version, dev_time):
        """检查版本号"""
        if cur_version < RedisKey.APPOINT_VERSION_NO:
            self._upgrade_version(device_name)

    @db.transaction(is_commit=True)
    def _update_device(self, pgsql_cur, data):
        pgsql_db = db.PgsqlDbUtil
        pgsql_db.update(pgsql_cur, data, table_name='device')

    @db.transaction(is_commit=False)
    def _get_device_info_data(self, pgsql_cur, device_name):
        pgsql_db = db.PgsqlDbUtil

        sql = "SELECT id,status,version_no,sound_volume," \
              "license_plate_number,device_type" \
              " FROM device WHERE device_name='{}' LIMIT 1"
        device = pgsql_db.get(pgsql_cur, sql.format(device_name))
        print device
        return device[0], device[1], device[2], device[3], device[4], device[5]

    def init_device_params(self, cur_version, device_name, dev_time, shd_devid):
        """
        初始化设备参数
        """
        rds_conn = db.rds_conn

        if cur_version == RedisKey.APPOINT_VERSION_NO:

            device_status = rds_conn.hget(
                RedisKey.DEVICE_CUR_STATUS, device_name)
            # 如果没有找到这个设备直接消费掉消息
            if not device_status:
                return -10
            # 5表示已初始化人员
            if device_status and int(device_status) == 5:
                return 0
            pk, status, version_no, sound_volume, license_plate_number, \
                device_type = self._get_device_info_data(device_name)

            # 设备为生成特征值设备
            if device_type == 2:
                license_plate_number = u'生成特征值专用'
                workmode = 3
            elif device_type == 1:
                workmode = 0
            print "---------------------"
            print status, type(status)
            d = {}
            # 已关联车辆
            if status == 2:
                d['status'] = 3   # 设置工作模式
                print u"设置工作模式"
                self._set_device_work_mode(
                    device_name, license_plate_number, sound_volume, workmode)
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
                try:
                    rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, device_name, 5)
                    self._init_people([], device_name)
                    rds_conn.hset(RedisKey.DEVICE_CUR_STATUS, device_name, 5)
                except:
                    import traceback
                    print traceback.format_exc()
            if d:
                d['id'] = pk
                self._update_device(d)

    @db.transaction(is_commit=False)
    def _get_sound_vol_by_name(self, pgsql_cur, dev_name):
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT sound_volume,license_plate_number " \
              "FROM device WHERE device_name='{}' LIMIT 1"
        result = pgsql_db.get(pgsql_cur, sql.format(dev_name))
        return result[0], result[1]

    def device_cur_timestamp(self, dev_name, dev_time, cnt, gps):
        """设备初始化完成之后才能写入时间戳"""
        rds_conn = db.rds_conn
        cur_status = rds_conn.hget(RedisKey.DEVICE_CUR_STATUS, dev_name)
        if cur_status and cur_status == 5:
            # 判断设备是否刚开机
            old_timestamp = rds_conn.hget(
                RedisKey.DEVICE_CUR_TIMESTAMP, dev_name)
            if int(time.time()) - int(old_timestamp) > 30:
                sound_vol, license_plate_number\
                    = self._get_sound_vol_by_name(dev_name)
                producer.update_chepai(dev_name, license_plate_number, sound_vol)

            rds_conn.hset(RedisKey.DEVICE_CUR_TIMESTAMP, dev_name, dev_time)
            rds_conn.hset(RedisKey.DEVICE_CUR_PEOPLE_NUMBER, cnt)
            rds_conn.hset(RedisKey.DEVICE_CUR_GPS, dev_name, gps)

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
        d['id'] = fid
        if feature:
            # aac_url不为空则修改状态
            sql = "SELECT id FROM face WHERE id={} " \
                  "AND aac_url IS NOT NULL"
            results = pgsql_db.get(sql.format(fid))
            if results:
                d['status'] = 4
            d['feature'] = feature
        else:
            d['status'] = 5
        pgsql_db.update(pgsql_cur, d, table_name='face')
        # 将设备从使用中删除
        rds_conn.hdel(RedisKey.DEVICE_USED, device_name)

    def acc_close(self, device_name):
        """
        acc关闭
        向redis存入一条acc关闭的数据
        """
        rds_conn = db.rds_conn
        # TODO 日志是否有devtime
        rds_conn.hset(RedisKey.ACC_CLOSE, device_name, int(time.time()))
        # 将STUDENT_SET设置过期时间100s
        rds_conn.expire(RedisKey.STUDENT_SET.format(device_name), 100)
