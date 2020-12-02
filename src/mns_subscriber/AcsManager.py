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

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
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
        jdata = {'url': 'https://img.pinganxiaoche.com/apps/1600666302.yaffs2', 'crc': -282402801, 'cmd': 'update', 'version': 232, 'size': 4756736}

        self._pub_create_device_msg(device_name, jdata)

    def _set_oss_info(self, device_name):
        """设置oss信息"""
        jdata = {
            "cmd": "ossinfo",
            "ossdomain": self.oss_domain.replace('https://', ''),
            "osskeyid": self.oss_access_key_id,
            "osskeysecret": self.oss_key_secret[12:] + self.oss_key_secret[:12]
        }
        self._pub_create_device_msg(device_name, jdata)

        time.sleep(1)
        jdata = {
            "cmd": "set_audiotype",
            "value": 1
        }
        self._pub_create_device_msg(device_name, jdata)

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

    def _pub_create_device_msg(self, devname, jdata):
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

    def _set_notts(self, device_name):
        jdata = {
            "cmd": "set_notts",
            "value": 1
        }
        return self._pub_create_device_msg(device_name, jdata)

    def _set_workmode(self, device_name, workmode, chepai, cur_volume):
        """
        设置设备工作模式
        :param device_name:
        :param workmode:
        :param cur_volume:
        :return:
        """
        if workmode not in [0, 1, 3]:
            return -1
        if not cur_volume:
            cur_volume = 10
        if chepai in ['92880']:
            lcd_rotation = 1
        else:
            lcd_rotation = 0
        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": chepai.encode('utf8'),
            "workmode": workmode,
            "delayoff": 1,
            "leftdetect": 1,
            "jiange": 10,
            "cleartime": 40,
            "shxmode": 1,
            "volume": int(cur_volume),
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "lcd_rotation": lcd_rotation,
            "noreg": 1
        }
        return self._pub_create_device_msg(device_name, jdata)

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
    def device_open(self, pgsql_cur, device_name, lastTime):
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT `id`,`status`,`version`,`car_no`," \
              "`modify_status_timestamp`,`cur_volume` FROM `device` " \
              "WHERE `device_name`='{}'"
        devices = pgsql_db.query(pgsql_cur, sql.format(device_name))
        if devices:
            device = devices[0]
            if device:
                car_no = device[3]
                cur_volume = device[4]
                lastTime = datetime.strptime(lastTime, "%Y-%m-%d %H:%M:%S.%f").strftime(
                    "%Y-%m-%d %H:%M:%S")
                d = {
                    '`id`': device[0],
                    '`open_time`': "STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s')"
                                   "".format(lastTime),
                    '`is_open`': 1
                }
                pgsql_db.update(pgsql_cur, d, table_name='`device`')
                self._set_device_work_mode(
                    device_name, car_no, cur_volume)

    @db.transaction(is_commit=True)
    def device_close(self, pgsql_cur, device_name, lastTime):
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        sql = "SELECT `id`,`open_time` FROM `device` " \
              "WHERE `device_name`='{}'"
        devices = pgsql_db.query(pgsql_cur, sql.format(device_name))
        if devices:
            device = devices[0]
            if device:
                pk = device[0]
                open_time = device[1]
                last_time = datetime.strptime(lastTime, "%Y-%m-%d %H:%M:%S.%f")
                # 关机时间小于开机时间,说明这个关机时间是无效的
                if last_time < open_time:
                    return
                d = {
                    '`id`': pk,
                    '`is_open`': 0
                }
                pgsql_db.update(pgsql_cur, d, table_name='`device`')

    @db.transaction(is_commit=True)
    def update_device_last_time(self, pgsql_cur, device_name,
                                devtime, gps_str, device_iid):
        """
        更新设备最后在线时间
        :return:
        """
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn

        sql = "SELECT `id`,`last_time` FROM `device` " \
              "WHERE `device_name`='{}' LIMIT 1"
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
                        '`id`': pk,
                        '`last_time`': 'now()'
                    }
                    pgsql_db.update(pgsql_cur, d, table_name='`device`')
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
                '`id`': pk,
                '`last_time`': 'now()',
                '`cur_gps`': cur_gps,
                '`device_iid`': device_iid
            }
            pgsql_db.update(pgsql_cur, d, table_name='device')

    @db.transaction(is_commit=True)
    def add_order(self, pgsql_cur, fid, gps_str, add_time, dev_name):
        """
        添加订单
        """
        redis_db = db.rds_conn
        pgsql_db = db.PgsqlDbUtil
        arr = gps_str.split(',')
        longitude = arr[0]
        latitude = arr[1]

        user_sql = "SELECT UP.`id`,UP.`nickname`,UP.`emp_no`," \
                   "UP.`is_internal_staff`,UP.`station_id`," \
                   "UP.`mobile`,UP.`deadline` " \
                   "FROM `user_profile` AS UP " \
                   "INNER JOIN `face` " \
                   "AS F ON F.`user_id`=UP.`id` WHERE F.`id`={} LIMIT 1"
        user = pgsql_db.get(pgsql_cur, user_sql.format(fid))
        print "-------------------add_order-------------------"
        print user
        if not user:
            return
        d = {}

        t_d = {}
        min_station_id = None
        min_station_distance = None
        # 实际上车站点
        if longitude and latitude:
            try:
                longitude = AcsManager._jwd_swap(float(longitude))
                latitude = AcsManager._jwd_swap(float(latitude))
                longitude, latitude = utils.gcj_02_to_gorde_gpd(
                    str(longitude), str(latitude))

                d['`longitude`'] = decimal.Decimal(str(longitude))
                d['`latitude`'] = decimal.Decimal(str(latitude))

                sql = 'SELECT S.`id`,S.`longitude`,S.`latitude`,S.`name` ' \
                      'FROM `station` AS S WHERE S.`status`=1 '
                results = pgsql_db.query(pgsql_cur, sql)

                for row in results:
                    t_d[str(row[0])] = dict(station_id=row[0],
                                            longitude=row[1],
                                            latitude=row[2],
                                            name=row[3])
                    # 计算站点id
                    redis_db.geoadd('moment_key', float(row[1]),
                                    float(row[2]), str(row[0]))
                radius = redis_db.georadius('moment_key', longitude,
                                            latitude,
                                            100, unit="m", withdist=True)
                if radius:
                    min_station_id = int(radius[0][0])
                    min_station_distance = radius[0][1]
                redis_db.delete('moment_key')
            except:
                import traceback
                print traceback.format_exc()
        user_pk = user[0]
        nickname = user[1]
        emp_no = user[2]
        is_internal_staff = user[3]

        special_station_sql = 'SELECT `station_id` FROM `special_station`'
        special_results = pgsql_db.query(pgsql_cur, special_station_sql)
        special_ids = [row[0] for row in special_results]
        target_station_ids = list(set(special_ids) - set([user[4]]))    # 异常站点集合
        print target_station_ids
        mobile = user[5]
        deadline = user[6]

        desc_sql = """
        SELECT E1.`id` as parent_company_id, E2.`id` as child_company_id, D.`id` as department_id, CONCAT(E1.`name`,'-',E2.`name`,'-',D.`name`) AS DES  FROM `department` as D 
INNER JOIN `enterprise` AS E2 ON E2.id=D.`enterprise_id` 
INNER JOIN `enterprise` AS E1 ON E1.id=E2.`parent_id` 
INNER JOIN `user_department_relation` as UDR ON UDR.`department_id`=D.`id` 
WHERE UDR.`user_id` = {}
        """
        result = pgsql_db.get(pgsql_cur, desc_sql.format(user_pk))
        parent_company_id = result[0]
        child_company_id = result[1]
        department_id = result[2]
        desc = result[3]

        order_no = datetime.now().strftime('%Y%m%d%H%M%S%f')

        scan_time = "STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s')".format(
            datetime.fromtimestamp(add_time).strftime('%Y-%m-%d %H:%M:%S'))

        d['`order_no`'] = order_no
        d['`user_id`'] = int(user_pk)
        d['`status`'] = 1
        d['`scan_timestamp`'] = int(add_time)
        d['`scan_time`'] = scan_time
        d['`is_internal_staff`'] = int(is_internal_staff)
        d['`parent_company_id`'] = parent_company_id
        d['`child_company_id`'] = child_company_id
        d['`department_id`'] = department_id
        d['`passenger_name`'] = nickname.encode('utf-8')
        d['`emp_no`'] = emp_no
        d['`desc`'] = desc
        if min_station_id:
            station_info = t_d[str(min_station_id)]
            station_id = station_info['station_id']
            d['`station_id`'] = station_id
            d['`station_name`'] = station_info['name']
            d['`is_except`'] = \
                1 if station_id in target_station_ids else 0
            d['`distance`'] = int(min_station_distance) if min_station_distance > 1 else 1
        else:
            d['`is_except`'] = 0

        d['`face_url`'] = self.oss_domain + '/snap_{}_{}.jpg'.format(
            fid, add_time)
        device_sql = "SELECT `car_no` FROM `device` " \
                     "WHERE `device_name`='{}' LIMIT 1"
        car_no = pgsql_db.get(pgsql_cur, device_sql.format(dev_name))[0]
        d['`car_no`'] = car_no.encode('utf8') if car_no else ""
        d['`mobile`'] = mobile
        d['`deadline`'] = "STR_TO_DATE('{}', '%Y-%m-%d %H:%i:%s')".format(
                datetime.fromtimestamp(deadline).strftime('%Y-%m-%d %H:%M:%S'))
        pgsql_db.insert(pgsql_cur, d, table_name='`order`')

    def add_redis_queue(self, device_name, data, pkt_cnt):
        """添加到redis queue"""
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
        SELECT `id`,`feature_crc` FROM `face` WHERE `user_id` in (
            SELECT UP.`id` FROM `user_profile` AS UP 
            INNER JOIN `user_department_relation` AS UDR ON UDR.`user_id`=UP.`id` 
            INNER JOIN `department` as D ON D.`id`=UDR.`department_id` 
						INNER JOIN `enterprise` AS E2 ON E2.`id`=D.`enterprise_id` 
						INNER JOIN `enterprise` AS E1 ON E1.`id`=E2.`parent_id` 
            INNER JOIN `user_role_relation` AS URR ON URR.`user_id`=UP.`id` 
            INNER JOIN `role` AS R ON R.`id`=URR.`role_id` 
            WHERE E1.`id` IN (SELECT `parent_enterprise_id` FROM `device` 
            WHERE `device_name`='{}') AND R.`code`='EMP' AND UP.`status`=1 
        ) AND `status`=1 AND `feature` IS NOT NULL
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

        # "查询设备人员" key
        if rds_conn.get('query_device_people'):
            rds_conn.delete('query_device_people')
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

                dev_sql = "SELECT `id` FROM `device` WHERE `mac`='{}' LIMIT 1"

                obj = pgsql_db.get(pgsql_cur, dev_sql.format(mac))
                if obj:
                    return None

                sql = 'SELECT `id`,`device_name` FROM `device` ' \
                      'ORDER BY `id` DESC LIMIT 1'
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
                    return None
                # 添加记录
                d = {
                    'device_name': response['Data']['DeviceName'],
                    'status': 1,
                    'mac': mac,
                    'product_key': response['Data']['ProductKey'],
                    'device_secret': response['Data']['DeviceSecret'],
                    'last_time': 'now()'
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
                self._pub_create_device_msg('newdev', msg)
            finally:
                rds_conn.delete('create_device')
        return None

    def _set_device_work_mode(self, dev_name, car_no, cur_volume):
        """设置设备工作模式"""
        # 设置为通道模式
        self._set_workmode(dev_name, 0, car_no, cur_volume)

    @staticmethod
    def _init_people(people_list, device_name, pgsql_db, pgsql_cur):
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
        SELECT `id`,`feature_crc` FROM `face` WHERE `user_id` in (
            SELECT UP.`id` FROM `user_profile` AS UP 
            INNER JOIN `user_department_relation` AS UDR ON UDR.`user_id`=UP.`id` 
            INNER JOIN `department` as D ON D.`id`=UDR.`department_id` 
						INNER JOIN `enterprise` AS E2 ON E2.`id`=D.`enterprise_id` 
						INNER JOIN `enterprise` AS E1 ON E1.`id`=E2.`parent_id` 
            INNER JOIN `user_role_relation` AS URR ON URR.`user_id`=UP.`id` 
            INNER JOIN `role` AS R ON R.`id`=URR.`role_id` 
            WHERE E1.`id` IN (SELECT `parent_enterprise_id` FROM `device` 
            WHERE `device_name`='{}') AND R.`code`='EMP' AND UP.`status`=1 
        ) AND `status`=1 AND `feature` IS NOT NULL
        """
        device_fid_set = set(fid_dict.keys())
        results = pgsql_db.query(pgsql_cur, sql.format(device_name))
        face_ids = [str(row[0]) for row in results]

        add_list = list(set(face_ids) - set(device_fid_set))

        # 放到消息队列
        producer.device_people_update_msg(
            add_list, [], [], device_name)

    @db.transaction(is_commit=True)
    def check_version(self, pgsql_cur, device_name, cur_version, dev_time):
        """检查版本号"""
        pgsql_db = db.PgsqlDbUtil
        rds_conn = db.rds_conn
        cur_time = datetime.now()
        # 当前时间和设备时间相差40s以上就不需要检查版本号
        dev_time_timestamp = datetime.fromtimestamp(int(dev_time))
        if (cur_time - dev_time_timestamp) > timedelta(seconds=40):
            return

        if cur_version < 232:
            self._upgrade_version(device_name)
        elif cur_version >= 232:
            device_cur_status = "DEVICE_CUR_STATUS"
            device_status = rds_conn.hget(device_cur_status, device_name)
            # 6表示已初始化人员
            if device_status and int(device_status) == 6:
                return
            sql = "SELECT `id`,`status`,`version`,`car_no`," \
                  "`modify_status_timestamp`,`cur_volume` FROM `device` " \
                  "WHERE `device_name`='{}'"
            devices = pgsql_db.query(pgsql_cur, sql.format(device_name))
            if devices:
                device = devices[0]
                pk = device[0]
                status = device[1]
                version = device[2]
                car_no = device[3]
                modify_status_timestamp = device[4]
                cur_volume = device[5]
                d = {}
                if status == 1:
                    #print u"1.设备还没有关联企业"
                    return
                elif status == 2:   # 状态为2,接下来设置模式
                    d['`status`'] = 3   # 已设置模式
                    self._set_device_work_mode(
                        device_name, car_no, cur_volume)
                    #print u"3.设置模式"
                elif status == 3 and modify_status_timestamp < \
                        long(dev_time):   # 状态为3,接下来设置播报
                    d['`status`'] = 4   # 已设置播报
                    self._set_notts(device_name)
                    #print u"4.设置播报"
                elif status == 4 and modify_status_timestamp < \
                        long(dev_time):   # 状态为4,接下来设置oss
                    d['`status`'] = 5   # 已设置oss
                    self._set_oss_info(device_name)
                    #print u"5.设置oss"
                elif status == 5 and modify_status_timestamp < \
                        long(dev_time): # 状态为5,初始化人员
                    d['`status`'] = 6   # 已初始化人员
                    rds_conn.hset(device_cur_status, device_name, 6)
                    AcsManager._init_people([], device_name, pgsql_db, pgsql_cur)
                    #print u"6.初始化人员"
                elif status == 6 and \
                        not device_status:
                    rds_conn.hset(device_cur_status, device_name, 6)

                # 版本为空或者小于232
                if not device[2] or int(device[2]) < 232:
                    d['`version`'] = cur_version
                if d:
                    d['`id`'] = pk
                    d['`modify_status_timestamp`'] = int(dev_time)
                    pgsql_db.update(pgsql_cur, d, table_name='`device`')

    @db.transaction(is_commit=True)
    def save_imei(self, pgsql_cur, device_name, imei):
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT `id` FROM `device` WHERE `device_name`='{}' LIMIT 1"
        obj = pgsql_db.get(pgsql_cur, sql.format(device_name))
        if obj:
            d = {
                '`id`': obj[0],
                '`imei`': imei
            }
            pgsql_db.update(pgsql_cur, d, table_name='`device`')