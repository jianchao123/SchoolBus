# coding: utf-8
import os
import json
import time
import base64
import shutil
import struct
from datetime import datetime
from msgqueue.db import transaction, MysqlDbUtil, rds_conn
from msgqueue import config
from msgqueue import utils
from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest


class HeartBeatConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)

    def heartbeat_callback(self, ch, method, properties, body):
        print "------------heartbeat-------------deliver_tag={}".\
            format(method.delivery_tag)
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class UserConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.user_business = UserBusiness(self.logger)

    def user_callback(self, ch, method, properties, body):
        print method
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'batchadd':
            import_people_key = rds_conn.setnx('import_people', 1)
            if import_people_key:
                try:
                    self.user_business.batch_add_user(data)
                finally:
                    rds_conn.delete('import_people')
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class UserBusiness(object):
    """用户创建后的业务处理"""

    def __init__(self, logger):
        self.logger = logger

    @transaction(is_commit=True)
    def batch_add_user(self, mysql_cur, data):
        """批量添加用户"""
        # {
        #     "parent": {
        #         "child": []
        #     }
        # }
        mysql_db = MysqlDbUtil(mysql_cur)
        all_json = {}
        # 添加用户之前先添加部门
        for row in data:
            department_desc = row[3]
            arr = department_desc.split("-")
            parent_company_name = arr[0]
            child_company_name = arr[1]
            department_name = arr[2]

            if parent_company_name in all_json:
                parent_json = all_json[parent_company_name]
                if child_company_name in parent_json:
                    department_list = parent_json[child_company_name]
                    if department_name not in department_list:
                        department_list.append(department_name)
                else:
                    parent_json[child_company_name] = [department_name]
            else:
                all_json[parent_company_name] = {child_company_name: [department_name]}

        print all_json

        parent_sql = u"SELECT `id` FROM `enterprise` " \
                     u"WHERE `name`='{}' AND `level`=1 AND `status`=1"

        child_sql = u"SELECT `id` FROM `enterprise` " \
                    u"WHERE `name`='{}' AND `level`=2 AND `status`=1 " \
                    u"AND `parent_id`={}"

        department_sql = u"""SELECT D.`id` FROM `department` AS D 
INNER JOIN `enterprise` AS E2 ON E2.id=D.enterprise_id 
INNER JOIN `enterprise` AS E1 ON E1.id=E2.parent_id 
WHERE E1.`id`={} AND E2.`id`={} AND D.`name`='{}' 
AND E1.`status`=1 AND E2.`status`=1 AND D.`status`=1"""
        unique_sql = "SELECT `id` FROM `enterprise` WHERE `uniqueid`='{}' LIMIT 1"
        for parent_company_name in all_json:
            parent_companies = mysql_db.query(parent_sql.format(parent_company_name))
            # 总公司不存在
            if not parent_companies:
                cur_parent_uniqueid = "%.6f" % time.time()
                print cur_parent_uniqueid
                d = {
                    "`name`": parent_company_name.encode('utf8'),
                    "`level`": 1,
                    "`status`": 1,
                    "`uniqueid`": cur_parent_uniqueid
                }
                mysql_db.insert(d, table_name='`enterprise`')
                parent_company_id = mysql_db.get(
                    unique_sql.format(cur_parent_uniqueid))[0]
            else:
                # 存在,获取总公司id
                parent_company_id = parent_companies[0][0]

            parent_json = all_json[parent_company_name]
            for child_company_name in parent_json:
                print child_sql.format(
                    child_company_name, parent_company_id)
                child_companies = mysql_db.query(child_sql.format(
                    child_company_name, parent_company_id))
                # 子公司不存在
                if not child_companies:
                    cur_child_uniqueid = "%.6f" % time.time()
                    print cur_child_uniqueid
                    d = {
                        "`name`": child_company_name.encode('utf8'),
                        "`level`": 2,
                        "`parent_id`": parent_company_id,
                        "`status`": 1,
                        "`uniqueid`": cur_child_uniqueid

                    }
                    mysql_db.insert(d, table_name='`enterprise`')
                    child_company_id = mysql_db.get(
                        unique_sql.format(cur_child_uniqueid))[0]
                else:
                    # 存在,获取子公司id
                    child_company_id = child_companies[0][0]
                department_list = parent_json[child_company_name]
                for department_name in department_list:
                    departments = mysql_db.query(department_sql.format(
                        parent_company_id, child_company_id, department_name))

                    if not departments:
                        desc = parent_company_name + "-" + \
                               child_company_name + "-" + department_name
                        d = {
                            "`name`": department_name.encode('utf8'),
                            "`desc`": desc.encode('utf8'),
                            "`enterprise_id`": child_company_id,
                            "`status`": 1
                        }
                        mysql_db.insert(d, table_name='`department`')

        # 查询所有站点
        station_sql = 'SELECT `id`,`name`,`longitude`,`latitude` ' \
                      'FROM `station` WHERE `status`=1'
        results = mysql_db.query(station_sql)
        station_json = {}
        for row in results:
            station_json[row[1]] = [row[0], row[2], row[3]]

        get_face_sql = "SELECT `id`,`oss_url` FROM `face` WHERE `user_id`='{}'"
        user_role_id = mysql_db.get("SELECT `id` FROM `role` WHERE `code`='EMP' LIMIT 1")[0]
        user_exist_sql = "SELECT `id`,`status` FROM `user_profile` WHERE `emp_no`='{}'"
        get_user_sql = "SELECT `id` FROM `user_profile` WHERE `emp_no`='{}' LIMIT 1"
        get_department_sql = u"""SELECT D.`id` FROM `department` AS D
INNER JOIN `enterprise` AS E2 ON E2.id=D.enterprise_id
INNER JOIN `enterprise` AS E1 ON E1.id=E2.parent_id
WHERE E1.`name`='{}' AND E2.`name`='{}' AND D.`name`='{}'
AND E1.`status`=1 AND E2.`status`=1 AND D.`status`=1 LIMIT 1"""

        get_department_sql_by_userid = "SELECT `id` FROM `user_department_relation` WHERE `user_id`={} LIMIT 1"
        print data
        for row_data in data:
            emp_no = row_data[0]
            nickname = row_data[1]
            sex_name = row_data[2]
            department_name = row_data[3]
            mobile = row_data[4]
            id_card = row_data[5]
            station_name = row_data[6]
            deadline = row_data[7]

            department_arr = department_name.split('-')

            user_exist_results = mysql_db.query(
                user_exist_sql.format(emp_no))
            if user_exist_results:
                exist_user_id = user_exist_results[0][0]
                status = user_exist_results[0][1]

                print "----------batchadd-user already exists-----------{}".format(emp_no)
                if status == 10:
                    specified_gps = \
                        str(station_json[station_name][1]) + ',' + \
                        str(station_json[station_name][2])
                    d = {
                        '`id`': exist_user_id,
                        '`username`': emp_no,
                        '`emp_no`': emp_no,
                        '`nickname`': nickname.encode('utf-8'),
                        '`sex`': 1 if sex_name == u'男' else 2,
                        '`mobile`': mobile,
                        '`id_card`': id_card,
                        '`deadline`': deadline,
                        '`station_id`': station_json[station_name][0],
                        '`specified_gps`': specified_gps,
                        '`address`': station_name.encode('utf-8'),
                        '`is_internal_staff`': 1,
                        '`status`': 1,
                        '`create_time`': 'now()'
                    }
                    mysql_db.update(d, table_name='`user_profile`')
                    face_result = mysql_db.get(get_face_sql.format(exist_user_id))
                    fid = face_result[0]
                    oss_url = face_result[1]
                    face_data = {
                        '`id`': fid,
                        '`status`': -2,
                        '`nickname`': nickname.encode('utf-8'),
                        '`oss_url`': '',
                        '`update_time`': 'now()'
                    }
                    mysql_db.update(face_data, table_name='`face`')

                    # 关联部门
                    cur_get_department_sql = get_department_sql.format(
                        department_arr[0],
                        department_arr[1],
                        department_arr[2])

                    cur_department_id = mysql_db.get(cur_get_department_sql)[0]

                    user_department_relation_pk = mysql_db.get(
                        get_department_sql_by_userid.format(exist_user_id))[0]
                    d = {
                        '`id`': user_department_relation_pk,
                        '`user_id`': exist_user_id,
                        '`department_id`': cur_department_id
                    }
                    mysql_db.update(d, table_name='`user_department_relation`')
                    if oss_url:
                        utils.delete_oss_file(["people" + oss_url.split("people")[1]])
                elif status == 1:
                    print "========================="
                    specified_gps = \
                        str(station_json[station_name][1]) + ',' + \
                        str(station_json[station_name][2])
                    d = {
                        '`id`': exist_user_id,
                        '`username`': emp_no,
                        '`emp_no`': emp_no,
                        '`nickname`': nickname.encode('utf-8'),
                        '`sex`': 1 if sex_name == u'男' else 2,
                        '`mobile`': mobile,
                        '`id_card`': id_card,
                        '`deadline`': deadline,
                        '`station_id`': station_json[station_name][0],
                        '`specified_gps`': specified_gps,
                        '`address`': station_name.encode('utf-8'),
                        '`is_internal_staff`': 1,
                        '`status`': 1
                    }
                    mysql_db.update(d, table_name='`user_profile`')
                    face_result = mysql_db.get(get_face_sql.format(exist_user_id))
                    fid = face_result[0]
                    oss_url = face_result[1]

                    face_data = {
                        '`id`': fid,
                        '`status`': -2,
                        '`nickname`': nickname.encode('utf-8'),
                        '`oss_url`': '',
                        '`update_time`': 'now()'
                    }
                    mysql_db.update(face_data, table_name='`face`')

                    # 关联部门
                    cur_get_department_sql = get_department_sql.format(
                        department_arr[0],
                        department_arr[1],
                        department_arr[2])
                    print cur_get_department_sql
                    cur_department_id = mysql_db.get(cur_get_department_sql)[0]

                    user_department_relation_pk = mysql_db.get(
                        get_department_sql_by_userid.format(exist_user_id))[0]
                    d = {
                        '`id`': user_department_relation_pk,
                        '`user_id`': exist_user_id,
                        '`department_id`': cur_department_id
                    }
                    print d
                    mysql_db.update(d, table_name='`user_department_relation`')
                    if oss_url:
                        utils.delete_oss_file(["people" + oss_url.split("people")[1]])
            else:
                # 创建用户
                specified_gps = \
                    str(station_json[station_name][1]) + ',' + \
                    str(station_json[station_name][2])
                d = {
                    '`username`': emp_no,
                    '`emp_no`': emp_no,
                    '`nickname`': nickname.encode('utf-8'),
                    '`sex`': 1 if sex_name == u'男' else 2,
                    '`mobile`': mobile,
                    '`id_card`': id_card,
                    '`deadline`': deadline,
                    '`station_id`': station_json[station_name][0],
                    '`specified_gps`': specified_gps,
                    '`address`': station_name.encode('utf-8'),
                    '`is_internal_staff`': 1,
                    '`create_time`': 'now()',
                    '`status`': 1
                }
                mysql_db.insert(d, table_name='`user_profile`')

                # 创建人脸
                cur_user_id = mysql_db.get(get_user_sql.format(emp_no))[0]
                d = {
                    '`status`': -2,
                    '`nickname`': nickname.encode('utf-8'),
                    '`user_id`': cur_user_id,
                    '`emp_no`': emp_no,
                    '`update_time`': 'now()'
                }
                mysql_db.insert(d, table_name='`face`')

                # 添加角色
                d = {
                    '`user_id`': cur_user_id,
                    '`role_id`': user_role_id
                }
                mysql_db.insert(d, table_name='`user_role_relation`')

                # 关联部门
                cur_get_department_sql = get_department_sql.format(
                    department_arr[0],
                    department_arr[1],
                    department_arr[2])
                print cur_get_department_sql
                cur_department_id = mysql_db.get(cur_get_department_sql)[0]
                d = {
                    '`user_id`': cur_user_id,
                    '`department_id`': cur_department_id
                }
                mysql_db.insert(d, table_name='`user_department_relation`')
                print emp_no


class DeviceConsumer(object):
    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.device_business = DeviceBusiness(
            config.Productkey, config.MNSAccessKeyId,
            config.MNSAccessKeySecret, self.logger)

    def device_callback(self, ch, method, properties, body):
        print method
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'list':
            self.device_business.device_people_list_upgrade(data)
        if routing_suffix == 'update':
            pass
        if routing_suffix == 'add':
            self.device_business.device_add_people(data)
        if routing_suffix == 'delete':
            self.device_business.device_delete_people(data)
        if routing_suffix == 'updatechepai':
            self.device_business.update_chepai(data)
        if routing_suffix == 'listsave':
            self.device_business.device_people_list_save(data)
        if routing_suffix == 'getdevicepeopledata':
            self.device_business.send_get_people_data_msg(data)
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class DeviceBusiness(object):
    """设备业务"""

    tts = "https://wgxing-device.oss-cn-beijing." \
          "aliyuncs.com/people/video/qsc.aac"

    def __init__(self, product_key, mns_access_key_id,
                 mns_access_key_secret, logger):
        self.client = AcsClient(mns_access_key_id,
                                mns_access_key_secret, 'cn-shanghai')
        self.product_key = product_key
        self.logger = logger
        self.path = os.path.dirname(__file__) + '/temp'

    def _batch_add_people(self, device_name, url):
        """批量添加人员"""
        jdata = {
            "url": url,
            "cmd": "batchaddface"
        }
        print jdata
        print device_name
        self._pub_msg(device_name, jdata)

    def _publish_del_people_msg(self, device_name, fid):
        """从设备上删除人员"""
        jdata = {
            "cmd": "delface",
            "fid": int(fid)
        }
        self._pub_msg(device_name, jdata)

    def _publish_update_people_msg(self, device_name, fid, nickname, feature):
        """从设备上更新人员"""
        jdata = {
            "cmd": "updateface",
            "fid": int(fid),
            "fno": device_name,
            "name": nickname.encode('utf-8'),
            "feature": feature,
            "ttsurl": DeviceBusiness.tts,
            "group": 0,
            "faceurl": "",
            "cardno": ""
        }
        self._pub_msg(device_name, jdata)

    def _publish_add_people_msg(self, device_name, fid, feature, nickname):
        """添加人员"""

        jdata = {
            "cmd": "addface",
            "fid": int(fid),
            "fno": device_name,
            "name": nickname.encode('utf-8'),
            "feature": feature,
            "ttsurl": DeviceBusiness.tts,
            "group": 0,
            "faceurl": "",
            "go_station": "",
            "return_station": "",
            "school": "",
            "cardno": ""
        }
        self._pub_msg(device_name, jdata)

    def _set_workmode(self, device_name, workmode, chepai=None, cur_volume=None):
        """
        设置设备工作模式
        :param device_name:
        :param workmode:
        :return:
        """
        if workmode not in [0, 1, 3]:
            return -1
        if chepai in ['92880']:
            lcd_rotation = 1
        else:
            lcd_rotation = 0
        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": '',
            "workmode": workmode,
            "delayoff": 1,
            "leftdetect": 1,
            "jiange": 10,
            "cleartime": 40,
            "shxmode": 1,
            "volume": 6,
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "lcd_rotation": lcd_rotation,
            "noreg": 1
        }
        if chepai:
            jdata["chepai"] = chepai.encode('utf-8')
        if cur_volume and (-121 < int(cur_volume) < 7):
            jdata["volume"] = cur_volume
        print jdata
        return self._pub_msg(device_name, jdata)

    def _pub_msg(self, devname, jdata):
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

    @transaction(is_commit=True)
    def device_people_list_save(self, mysql_cur, data):
        print "======================device_people_list_save=============================="
        mysql_db = MysqlDbUtil(mysql_cur)
        people_list_str = data['people_list_str']
        device_name = data['device_name']
        server_face_ids = data['server_face_ids']

        people_raw_list = []
        fid_list = []
        people_list = people_list_str.split(",")
        for row in people_list:
            people_raw_list.append(row)
            data = base64.b64decode(row)
            length = len(data)
            offset = 0
            while offset < length:
                s = data[offset: offset + 16]
                ret_all = struct.unpack('<IiiI', s)
                fid = ret_all[0]
                fid_list.append(str(fid))
                offset += 16
        device_sql = "SELECT `id` FROM `device` WHERE `device_name`='{}'"
        device_id = mysql_db.get(device_sql.format(device_name))[0]

        people_data = []
        if fid_list:
            sql = "SELECT `id`,`nickname`,`emp_no` FROM `face` WHERE `id` IN (" \
                  + ",".join(fid_list) + ")"
            results = mysql_db.query(sql)
            for row in results:
                fid = str(row[0])
                nickname = row[1]
                emp_no = row[2]
                s = emp_no + "|" + nickname + "|1"
                people_data.append(s)

        not_updated_person_data = []
        if server_face_ids:
            qq = [str(row) for row in list(set(server_face_ids) - set(fid_list))]
            if qq:
                sql = "SELECT `id`,`nickname`,`emp_no` FROM `face` " \
                      "WHERE `id` IN ({})".format(",".join(qq))
                print sql
                results = mysql_db.query(sql)
                for row in results:
                    fid = str(row[0])
                    nickname = row[1]
                    emp_no = row[2]
                    s = emp_no + "|" + nickname + "|0"
                    not_updated_person_data.append(s)

        get_sql = 'SELECT `id` FROM `device_people_list` ' \
                  'WHERE `device_id`={} LIMIT 1'
        result = mysql_db.get(get_sql.format(device_id))
        print "-=-=-=-=-=========================="
        print result
        if result:
            pk = result[0]

            d = {
                '`id`': int(pk),
                '`device_people_list_raw`': ",".join(people_raw_list),
                '`total_number`': len(server_face_ids),
                '`already_upgrade_number`': len(fid_list),
                '`update_time`': 'now()',
                '`device_people`': ",".join(people_data),
                '`not_updated`': ",".join(not_updated_person_data)
            }
            mysql_db.update(d, table_name='`device_people_list`')
        else:

            d = {
                '`device_id`': device_id,
                '`device_people_list_raw`': ",".join(people_raw_list),
                '`total_number`': len(server_face_ids),
                '`already_upgrade_number`': len(fid_list),
                '`update_time`': 'now()',
                '`device_people`': ",".join(people_data),
                '`not_updated`': ",".join(not_updated_person_data)
            }
            mysql_db.insert(d, table_name='`device_people_list`')

    @transaction(is_commit=True)
    def device_people_list_upgrade(self, mysql_cur, data):
        """设备人员列表更新 处理器"""
        mysql_db = MysqlDbUtil(mysql_cur)
        print(">>>>> device_people_list_upgrade")
        self.logger.error("device_people_list_upgrade")
        add_list = data['add_list']     # fid
        del_list = data['del_list']     # fid
        update_list = data['update_list']   # fid
        device_name = data['device_name']

        feature_sql = 'SELECT `feature`,`nickname` ' \
                      'FROM `face` WHERE `id`={} LIMIT 1'

        # delete list
        if len(del_list) > 10:
            step = 0

            while True:
                temp_list = del_list[step: step + 250]
                if temp_list:
                    jdata = {"cmd": "batchdelface",
                             "fids": ",".join(temp_list)}
                    self._pub_msg(device_name, jdata)
                    step += 250
                else:
                    break
        else:
            for fid in del_list:
                self._publish_del_people_msg(device_name, fid)

        # update list
        if len(update_list) > 10:
            print "batch update---------"
            sql = "SELECT `id`,`feature`,`nickname` " \
                  "FROM `face` WHERE `id` in ({}) "
            results = mysql_db.query(sql.format(",".join(update_list)))
            self.batch_people_add(device_name, results)
        else:
            for fid in update_list:
                obj = mysql_db.get(feature_sql.format(int(fid)))
                if obj:
                    self._publish_update_people_msg(
                        device_name, fid, obj[1], obj[0])

        # add list
        if len(add_list) > 10:
            print "batch add----------"
            sql = "SELECT `id`,`feature`,`nickname` " \
                  "FROM `face` WHERE `id` in ({}) "
            results = mysql_db.query(sql.format(",".join(add_list)))
            self.batch_people_add(device_name, results)
        else:
            for fid in add_list:
                obj = mysql_db.get(feature_sql.format(fid))
                if obj:
                    self._publish_add_people_msg(
                        device_name, fid, obj[0], obj[1])

    def batch_people_add(self, device_name, results):
        """批量人员添加"""
        lines = []
        for row in results:
            line = str(row[0]) + "," + row[1] + "," + row[2] + "\n"
            lines.append(line.encode('utf8'))
        s = str(int(time.time()))
        fd = None
        file_path = os.path.join(self.path, s + '.txt')
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            fd = open(file_path, 'w')
            fd.writelines(lines)
        finally:
            if fd:
                fd.close()
                # os.remove(file_path)
        try:
            fd = open(file_path, 'r')
        finally:
            if fd:
                fd.close()
        oss_key = 'txts/' + s + '.txt'
        utils.upload_zip(oss_key, file_path)
        time.sleep(2)
        # 判断文件是否存在
        if utils.oss_file_exists(oss_key):
            self._batch_add_people(
                device_name, config.OSSDomain + "/" + oss_key)

    @transaction(is_commit=False)
    def device_add_people(self, mysql_cur, data):
        """添加人员到相关的设备"""
        mysql_db = MysqlDbUtil(mysql_cur)
        fid = data['fid']
        feature = data['feature']
        parent_enterprise_id = data['parent_enterprise_id']
        sql = 'SELECT `device_name` FROM `device` WHERE `status` = 6 ' \
              'AND `parent_enterprise_id` = {}'.format(parent_enterprise_id)
        results = mysql_db.query(sql)

        face_sql = 'SELECT `feature`,`nickname` ' \
                   'FROM `face` WHERE `id`={} LIMIT 1'
        face_obj = mysql_db.get(face_sql.format(fid))
        for row in results:
            device_name = row[0]
            self._publish_add_people_msg(device_name, fid, feature, face_obj[1])

    @transaction(is_commit=False)
    def device_delete_people(self, mysql_cur, data):
        """删除人员从相关的设备"""
        mysql_db = MysqlDbUtil(mysql_cur)
        fid = data['fid']
        parent_enterprise_id = data['parent_enterprise_id']
        sql = 'SELECT `device_name` FROM `device` WHERE `status` == 1 ' \
              'AND `parent_enterprise_id` = {}'.format(parent_enterprise_id)
        results = mysql_db.query(sql)
        for row in results:
            device_name = row[0]
            self._publish_del_people_msg(device_name, fid)

    def update_chepai(self, data):
        chepai = data['chepai']
        device_name = data['device_name']
        cur_volume = data['cur_volume']
        self._set_workmode(device_name, 0, chepai, cur_volume)

    def send_get_people_data_msg(self, data):
        """发送获取设备上人员数据的消息"""
        device_name = data['device_name']
        jdata = {
            "cmd": "devwhitelist",
            "pkt_inx": -1
        }
        self._pub_msg(device_name, jdata)


class ExportExcelConsumer(object):
    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.excel_business = ExportExcelBusiness(
            config.Productkey, config.MNSAccessKeyId,
            config.MNSAccessKeySecret, self.logger)

    def excel_callback(self, ch, method, properties, body):
        print method
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'order':
            self.excel_business.export_order_detail(data)
        if routing_suffix == 'empinfo':
            self.excel_business.people_info(data)
        if routing_suffix == 'empstatistics':
            self.excel_business.people_statistics(data)

        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class ExportExcelBusiness(object):

    def __init__(self, product_key, mns_access_key_id,
                 mns_access_key_secret, logger):
        self.client = AcsClient(mns_access_key_id,
                                mns_access_key_secret, 'cn-shanghai')
        self.product_key = product_key
        self.logger = logger
        self.path = os.path.dirname(__file__) + '/temp'

    @transaction(is_commit=True)
    def export_order_detail(self, mysql_cur, data):
        mysql_db = MysqlDbUtil(mysql_cur)

        parent_company_id = data['parent_company_id']
        child_company_id = data['child_company_id']
        department_id = data['department_id']
        year = data['year']
        month = data['month']
        task_id = data['task_id']

        setnx_key = rds_conn.setnx('export_order_detail', 1)
        if setnx_key:
            try:
                sql = 'SELECT `id` FROM `export_task` ' \
                      'WHERE `status`=1 AND `id`={} LIMIT 1'  # 待处理的
                obj = mysql_db.get(sql.format(task_id))
                if not obj:
                    return None  # 没有需要处理的
                sql = mysql_db.update({'`id`': task_id, '`status`': 2},
                                      table_name='`export_task`')  # 改为处理中
                self.logger.error(sql)
                time.sleep(1)
            finally:
                rds_conn.delete('export_order_detail')

        # 导出excel
        sql = """
        SELECT UP.`emp_no`,UP.`nickname`,UP.`deadline`,UP.`mobile`,D.`desc`,
        O.`scan_time`,S.`name`,O.`car_no`,O.`order_no` FROM `order` AS O 
INNER JOIN `user_profile` AS UP ON UP.`id`=O.`user_id` 
INNER JOIN `user_department_relation` AS UDR ON UDR.`user_id`=UP.`id` 
INNER JOIN `department` AS D ON D.`id`=UDR.`department_id` 
LEFT JOIN `station` AS S ON S.`id`=O.`station_id` 
WHERE O.`parent_company_id`={} {} AND YEAR(O.`scan_time`) = {} AND MONTH(O.`scan_time`) = {} 
LIMIT {} OFFSET {}
        """
        limit = 10000
        page = 1
        offset = (page - 1) * limit

        param_str = ''
        if child_company_id:
            param_str += ' AND O.`child_company_id`={} '.format(child_company_id)

        if child_company_id and department_id:
            param_str += ' AND O.`department_id`={} '.format(department_id)

        results = mysql_db.query(sql.format(
            parent_company_id, param_str, year, month, limit, offset))
        value_title = [u"订单id", u"工号", u"姓名", u"所属分组", u"手机号", u"乘坐时间",
                       u"实际乘坐地点", u"乘坐车牌号", u"有效期"]
        zip_name = u"乘坐记录(月报表){}-{}".format(year, month)
        excel_name = u"乘坐记录(月报表){}-{} 第{}部分.xls"
        sheet_name = u'数据{}条-{}条'
        zip_index = 0

        path = self.path + "/" + zip_name
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                os.remove(path + '.zip')
            except:
                pass

        os.makedirs(path)
        if not os.path.isdir(path):
            return None
        while results:
            if page % 10 == 1:
                zip_index += 1
                # 创建一个workbook
                workbook = utils.create_new_workbook()
                book_name_xls = path + "/" + excel_name.format(
                    year, month, zip_index)
            sheet_data = [value_title]
            for index, row in enumerate(results):
                valid_period = datetime.fromtimestamp(
                    row[2]).strftime('%Y-%m-%d %H:%M:%S')
                scan_time = row[5].strftime('%Y-%m-%d %H:%M:%S')
                sheet_data.append([row[8], row[0], row[1], row[4], row[3],
                                   scan_time, row[6], row[7], valid_period])

            utils.write_excel_xls(
                workbook,
                book_name_xls,
                sheet_name.format(offset + 1, offset + limit),
                sheet_data)
            # 下一页
            page += 1
            offset = (page - 1) * limit
            results = mysql_db.query(sql.format(
                parent_company_id, param_str,
                year, month, limit, offset))
        local_path = path + '.zip'
        utils.zip_dir(path, local_path)
        oss_key = 'zips/' + zip_name + ".zip"
        utils.upload_zip(oss_key, local_path)
        mysql_db.update({'`id`': task_id, '`status`': 3,
                         '`zip_url`': config.OSSDomain + "/" + oss_key},
                        table_name='`export_task`')
        # 删除文件
        shutil.rmtree(path)
        os.remove(path + ".zip")

    @transaction(is_commit=True)
    def people_info(self, mysql_cur, data):
        """
        人员信息
        """
        mysql_db = MysqlDbUtil(mysql_cur)

        parent_company_id = data['parent_company_id']
        child_company_id = data.get('child_company_id', None)
        department_id = data.get('department_id', None)
        admin_name = data['admin_name']
        task_id = data['task_id']

        setnx_key = rds_conn.setnx('export_people_statistics_data', 1)
        if setnx_key:
            try:
                sql = 'SELECT `id` FROM `export_task` ' \
                      'WHERE `status`=1 AND `id`={} LIMIT 1'  # 待处理的
                obj = mysql_db.get(sql.format(task_id))
                if not obj:
                    return None  # 没有需要处理的
                mysql_db.update({'`id`': task_id, '`status`': 2},
                                table_name='`export_task`')  # 改为处理中
                time.sleep(1)
            finally:
                rds_conn.delete('export_people_statistics_data')

        # 导出excel
        sql = """
            SELECT UP.`emp_no`,UP.`nickname`,D.`desc`,UP.`mobile`,UP.`id_card`,
          S.`name`,UP.`deadline`,UP.`create_time`,S1.`name` 
FROM `user_profile` AS UP 
INNER JOIN `user_department_relation` AS UDR ON UDR.`user_id`=UP.`id` 
INNER JOIN `department` AS D ON D.`id`=UDR.`department_id` 
INNER JOIN `enterprise` AS E2 ON E2.`id`=D.`enterprise_id` 
INNER JOIN `station` AS S ON S.`id`=UP.`station_id` 
WHERE E2.`parent_id`={}  AND UP.`status`=1 
            """
        sql = sql.format(parent_company_id)
        if child_company_id:
            sql += ' AND D.`enterprise_id`={} '.format(child_company_id)
        if child_company_id and department_id:
            sql += ' AND D.`id`={} '.format(department_id)

        results = mysql_db.query(sql)
        value_title = [u"工号", u"姓名", u"所属分组", u"手机号",
                       u"身份证号", u"乘坐地点1", u"乘坐地点2", u"有效期",
                       u"开户时间", u"操作人员"]
        excel_name = u"人员信息汇总.xls"
        sheet_name = u'人员信息汇总'

        path = self.path + "/" + excel_name
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
        sheet_data = [value_title]
        for index, row in enumerate(results):
            valid_period = datetime.fromtimestamp(row[6]).strftime('%Y-%m-%d %H:%M:%S')
            create_time = row[7].strftime('%Y-%m-%d %H:%M:%S')
            sheet_data.append([row[0], row[1], row[2], row[3], row[4],
                               row[5], row[8], valid_period,
                               create_time, admin_name])

        workbook = utils.create_new_workbook()
        utils.write_excel_xls(
            workbook,
            path,
            sheet_name,
            sheet_data)

        oss_key = 'zips/' + excel_name
        utils.upload_zip(oss_key, path)
        mysql_db.update({'`id`': task_id, '`status`': 3,
                         '`zip_url`': config.OSSDomain + "/" + oss_key},
                        table_name='`export_task`')
        # 删除文件
        os.remove(path)

    @transaction(is_commit=True)
    def people_statistics(self, mysql_cur, data):
        """
        人员统计
        """
        mysql_db = MysqlDbUtil(mysql_cur)

        parent_company_id = data['parent_company_id']
        child_company_id = data['child_company_id']
        department_id = data['department_id']
        year = data['year']
        month = data['month']
        task_id = data['task_id']

        setnx_key = rds_conn.setnx('export_people_statistics_data', 1)
        if setnx_key:
            try:
                sql = 'SELECT `id` FROM `export_task` ' \
                      'WHERE `status`=1 AND `id`={} LIMIT 1'  # 待处理的
                obj = mysql_db.get(sql.format(task_id))
                if not obj:
                    return None  # 没有需要处理的
                mysql_db.update({'`id`': task_id, '`status`': 2},
                                table_name='`export_task`')  # 改为处理中
                time.sleep(1)
            finally:
                rds_conn.delete('export_people_statistics_data')

        # 导出excel
        sql = \
        """
        SELECT UP.`emp_no`,UP.`nickname`,D.`desc`,UP.`mobile`,UP.`id_card`,(SELECT COUNT(`id`) FROM `order` WHERE `user_id`=UP.`id` AND YEAR(`scan_time`)={} AND MONTH(`scan_time`)={}) AS tt_count,UP.`deadline` 
FROM `user_profile` AS UP 
INNER JOIN `user_department_relation` AS UDR ON UDR.`user_id`=UP.`id` 
INNER JOIN `department` AS D ON D.`id`=UDR.`department_id` 
INNER JOIN `enterprise` AS E2 ON E2.`id`=D.`enterprise_id`  
INNER JOIN `station` AS S ON S.`id`=UP.`station_id` 
WHERE E2.`parent_id`={}  ORDER BY `tt_count` DESC
        """
        sql = sql.format(year, month, parent_company_id)
        if child_company_id:
            sql += ' AND E2.`id`={} '.format(child_company_id)
        if child_company_id and department_id:
            sql += ' AND D.`id`={} '.format(department_id)
        results = mysql_db.query(sql)
        value_title = [u"工号", u"姓名", u"所属分组", u"手机号", u"身份证号", u"乘车次数", u"有效期"]
        excel_name = u"人员统计.xls"
        sheet_name = u'人员统计'

        path = self.path + "/" + excel_name
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

        sheet_data = [value_title]
        for index, row in enumerate(results):
            valid_period = datetime.fromtimestamp(
                row[6]).strftime('%Y-%m-%d %H:%M:%S')
            sheet_data.append([row[0], row[1], row[2], row[3], row[4],
                               row[5], valid_period])

        workbook = utils.create_new_workbook()
        utils.write_excel_xls(
            workbook,
            path,
            sheet_name,
            sheet_data)

        oss_key = 'zips/' + excel_name
        utils.upload_zip(oss_key, path)
        mysql_db.update({'`id`': task_id, '`status`': 3,
                         '`zip_url`': config.OSSDomain + "/" + oss_key},
                        table_name='`export_task`')
        # 删除文件
        os.remove(path)
