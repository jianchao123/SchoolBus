# coding: utf-8
import os
import json
import time
import base64
import shutil
import struct
from datetime import datetime
from msgqueue.db import transaction, PgsqlDbUtil, rds_conn, wx_mp
from msgqueue import config
from msgqueue import utils
from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
from define import grade, classes, gender, duty


class HeartBeatConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)

    def heartbeat_callback(self, ch, method, properties, body):
        print "------------heartbeat-------------deliver_tag={}".\
            format(method.delivery_tag)
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class InsertUpdateConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.business = InsertUpdateBusiness(self.logger)

    def insert_update_callback(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        # if routing_suffix == 'workerinsert':
        #     # 更新工作人员关联车辆的信息
        #     self.business.car_field_update(data)
        # if routing_suffix == 'workerupdate':
        #     # 更新工作人员关联车辆的信息
        #     self.business.car_field_update(data)
        if routing_suffix == 'carupdate':
            # 更新关联到该车辆的学生信息
            self.business.student_field_update(data)
        if routing_suffix == 'oplog':
            self.business.operation_log(data)
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class InsertUpdateBusiness(object):

    def __init__(self, logger):
        self.logger = logger

    # @transaction(is_commit=True)
    # def car_field_update(self, pgsql_cur, data):
    #     from collections import defaultdict
    #     pgsql_db = PgsqlDbUtil
    #     print data
    #     worker_id = data['worker_id']
    #     car_id = data['car_id']
    #     nickname = data['nickname']
    #     duty_id = data['duty_id']
    #     duty_name = data['duty_name']
    #     empty = data['empty']
    #
    #     d = defaultdict()
    #     d['id'] = car_id
    #     if empty:
    #         if empty == 1:
    #             d['worker_1_id'] = 'NULL'
    #             d['worker_1_nickname'] = 'NULL'
    #             d['worker_1_duty_name'] = 'NULL'
    #         elif empty == 2:
    #             d['worker_2_id'] = 'NULL'
    #             d['worker_2_nickname'] = 'NULL'
    #             d['worker_2_duty_name'] = 'NULL'
    #     else:
    #         # 驾驶员
    #         if duty_id == 1:
    #             d['worker_1_id'] = worker_id
    #             d['worker_1_nickname'] = nickname
    #             d['worker_1_duty_name'] = duty_name
    #         elif duty_id == 2:
    #             d['worker_2_id'] = worker_id
    #             d['worker_2_nickname'] = nickname
    #             d['worker_2_duty_name'] = duty_name
    #
    #     print d
    #     if d:
    #         pgsql_db.update(pgsql_cur, d, 'car')

    @transaction(is_commit=True)
    def student_field_update(self, pgsql_cur, data):
        pgsql_db = PgsqlDbUtil
        car_id = data['id']
        license_plate_number = data['license_plate_number']
        sql = "SELECT id FROM student WHERE car_id={}"
        results = pgsql_db.query(pgsql_cur, sql.format(car_id))
        for row in results:
            stu_id = row[0]
            d = {
                'id': stu_id,
                'license_plate_number': license_plate_number
            }
            pgsql_db.update(pgsql_cur, d, 'student')

    @transaction(is_commit=True)
    def operation_log(self, pgsql_cur, data):
        """操作日志"""
        pgsql_db = PgsqlDbUtil
        print data
        user_id = data['user_id']
        func_name = data['func_name']
        func_param = data['func_param']
        sql = "SELECT username FROM admin_user WHERE id={} LIMIT 1"
        username = pgsql_db.get(pgsql_cur, sql.format(user_id))[0]
        if len(func_param) > 250:
            func_param = func_param[:250]
        d = {
            'username': username,
            'func_name': func_name,
            'func_param': func_param,
            'create_time': 'now()'
        }

        pgsql_db.insert(pgsql_cur, d, table_name='operation_log')


class StudentConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.student_business = StudentBusiness(self.logger)

    def student_callback(self, ch, method, properties, body):
        print "-----------------12321312"
        try:
            data = json.loads(body.decode('utf-8'))
            arr = method.routing_key.split(".")
            routing_suffix = arr[-1]
            if routing_suffix == 'batchaddstudent':
                self.student_business.batch_add_student(data)
            if routing_suffix == 'batchaddworker':
                self.student_business.batch_add_worker(data)
            if routing_suffix == 'batchaddcar':
                self.student_business.batch_add_car(data)
            if routing_suffix == 'batchaddschool':
                self.student_business.batch_add_school(data)
            if routing_suffix == 'updatenickname':
                self.student_business.create_video(data)
            if routing_suffix == 'bulkupdateface':
                self.student_business.bulk_update_face(data)
            if routing_suffix == 'bulkupdate':
                self.student_business.bulk_update_student(data)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)


class StudentBusiness(object):

    def __init__(self, logger):
        self.logger = logger

    @transaction(is_commit=True)
    def create_video(self, pgsql_cur, data):
        """更新学生的名字并创建语音"""
        pgsql_db = PgsqlDbUtil
        face_id = data['face_id']
        stu_no = data['stu_no']
        nickname = data['nickname']
        from msgqueue import utils
        oss_key = 'audio/' + stu_no + '.aac'
        utils.aip_word_to_audio(nickname, oss_key)
        url = 'http://' + config.OSSDomain + '/' + oss_key
        data = {
            'id': face_id,
            'aac_url': url
        }
        pgsql_db.update(pgsql_cur, data, table_name='face')
        print "============================="

    @transaction(is_commit=True)
    def bulk_update_student(self, pgsql_cur, data):
        """批量更新"""
        pgsql_db = PgsqlDbUtil
        stu_sql = "SELECT id,mobile_1,mobile_2 FROM student " \
                  "WHERE stu_no='{}' LIMIT 1"
        face_sql = "SELECT id,status FROM face WHERE stu_id={}"
        audio_sql = "SELECT id FROM audio WHERE face_id={}"
        for row in data:
            stu_no = row[0]
            nickname = row[1]
            gender_id = row[2]
            parents1_name = row[3]
            parents1_mobile = row[4]
            parents2_name = row[5]
            parents2_mobile = row[6]
            address = row[7]
            remarks = row[8]
            school_id = row[9]
            grade_id = row[10]
            classes_id = row[11]
            end_time = row[12]
            car_id = row[13]
            license_plate_number = row[14]

            parents1_mobile = str(int(float(parents1_mobile)))
            if parents2_mobile:
                parents2_mobile = str(int(float(parents2_mobile)))

            student = pgsql_db.get(pgsql_cur, stu_sql.format(stu_no))
            d = {
                'nickname': nickname,
                'gender': gender_id,
                'parents_1': parents1_name,
                'mobile_1': parents1_mobile,
                'parents_2': parents2_name if parents2_name else 'NULL',
                'mobile_2': parents2_mobile if parents2_mobile else 'NULL',
                'address': address,
                'remarks': remarks if remarks else 'NULL',
                'school_id': school_id,
                'grade_id': grade_id,
                'class_id': classes_id,
                'end_time': "TO_DATE('{}', 'yyyy-MM-dd')".format(end_time),
                'car_id': car_id,
                'license_plate_number': license_plate_number
            }

            if student:
                student_pk = student[0]

                d['id'] = student_pk
                # student[1] mobile_1 student[2] mobile_2
                if student[1] and student[1] != parents1_mobile:
                    d['open_id_1'] = 'NULL'
                if student[2] and student[2] != parents2_mobile:
                    d['open_id_2'] = 'NULL'
                # 家长1手机号为空直接不更新
                if not parents1_mobile:
                    continue
                if not parents2_mobile:
                    d['open_id_2'] = 'NULL'
                pgsql_db.update(pgsql_cur, d, 'student')

                # 其他的数据全部更新一遍
                face_object = pgsql_db.get(pgsql_cur, face_sql.format(student_pk))
                face_pk = face_object[0]
                face_status = face_object[1]

                audio_object = pgsql_db.get(pgsql_cur, audio_sql.format(face_pk))
                # 音频记录
                audio_d = {
                    'id': audio_object[0],
                    'status': 1,
                    'nickname': nickname
                }
                pgsql_db.update(pgsql_cur, audio_d, table_name='audio')
                # 人脸
                face_d = {
                    'id': face_pk,
                    'nickname': nickname,
                    'update_time': 'now()',
                    'end_timestamp': int(time.mktime(
                        datetime.strptime(end_time, '%Y-%m-%d').timetuple())),
                    'school_id': school_id
                }
                if face_status in (3, 4, 5):
                    face_d['status'] = 2    # 等待处理
                pgsql_db.update(pgsql_cur, face_d, 'face')

    @transaction(is_commit=True)
    def batch_add_student(self, pgsql_cur, data):
        """批量添加学生
        身份证号,姓名,性别id,家长1姓名,家长1手机号,家长2姓名,家长2手机号,家庭地址,备注,学校id,年级id,班级id,截止时间,车辆id
        """
        pgsql_db = PgsqlDbUtil

        stu_sql = "SELECT id,mobile_1,mobile_2 FROM student " \
                  "WHERE stu_no='{}' LIMIT 1"
        # 查询所有厂商的sql
        mfr_sql = "SELECT id FROM manufacturer WHERE status=1"  # 启用中的
        # 根据stu_id和school_id查询face_id
        query_facepk_sql = "SELECT id FROM face WHERE stu_id={} AND " \
                           "school_id={} LIMIT 1"
        for row in data:
            stu_no = row[0]
            nickname = row[1]
            gender_id = row[2]
            parents1_name = row[3]
            parents1_mobile = row[4]
            parents2_name = row[5]
            parents2_mobile = row[6]
            address = row[7]
            remarks = row[8]
            school_id = row[9]
            grade_id = row[10]
            classes_id = row[11]
            end_time = row[12]
            car_id = row[13]
            license_plate_number = row[14]

            parents1_mobile = str(int(float(parents1_mobile)))
            if parents2_mobile:
                parents2_mobile = str(int(float(parents2_mobile)))

            student = pgsql_db.get(pgsql_cur, stu_sql.format(stu_no))
            d = {
                'stu_no': stu_no,
                'nickname': nickname,
                'gender': gender_id,
                'parents_1': parents1_name,
                'mobile_1': parents1_mobile,
                'parents_2': parents2_name if parents2_name else 'NULL',
                'mobile_2': parents2_mobile if parents2_mobile else 'NULL',
                'address': address,
                'remarks': remarks if remarks else 'NULL',
                'school_id': school_id,
                'grade_id': grade_id,
                'class_id': classes_id,
                'end_time': "TO_DATE('{}', 'yyyy-MM-dd')".format(end_time),
                'car_id': car_id,
                'license_plate_number': license_plate_number
            }

            if student:
                # d['id'] = student[0]
                # if student[1] and student[1] != parents1_mobile:
                #     d['open_id_1'] = 'NULL'
                # if student[2] and student[2] != parents2_mobile:
                #     d['open_id_2'] = 'NULL'
                # pgsql_db.update(pgsql_cur, d, 'student')
                pass
            else:
                d['create_time'] = 'now()'
                d['status'] = 1
                pgsql_db.insert(pgsql_cur, d, 'student')
                stu = pgsql_db.get(pgsql_cur, stu_sql.format(stu_no))
                student_pk = stu[0]
                face_d = {
                    'status': 1,  # 没有人脸
                    'nickname': nickname,
                    'stu_no': stu_no,
                    'update_time': 'now()',
                    'end_timestamp': int(time.mktime(
                        datetime.strptime(end_time, '%Y-%m-%d').timetuple())),
                    'stu_id': student_pk,
                    'school_id': school_id
                }
                pgsql_db.insert(pgsql_cur, face_d, 'face')
                current_face_pk = pgsql_db.get(
                    pgsql_cur, query_facepk_sql.format(student_pk, school_id))[0]

                # 音频记录
                audio_d = {
                    'stu_no': stu_no,
                    'status': 1,
                    'face_id': current_face_pk,
                    'nickname': nickname
                }
                pgsql_db.insert(pgsql_cur, audio_d, table_name='audio')

                # 查询所有厂商
                mfrset = pgsql_db.query(pgsql_cur, mfr_sql)
                for mfr_row in mfrset:
                    mfr_pk = mfr_row[0]
                    feature_d = {
                        'mfr_id': mfr_pk,
                        'face_id': current_face_pk,
                        'status': -1    # 未绑定人脸
                    }
                    pgsql_db.insert(pgsql_cur, feature_d, table_name='feature')

        rds_conn.delete('batch_add_student')

    @transaction(is_commit=True)
    def batch_add_worker(self, pgsql_cur, data):
        """
        批量添加工作者
        """
        pgsql_db = PgsqlDbUtil
        worker_sql = "SELECT id,mobile FROM worker WHERE emp_no='{}' LIMIT 1"
        for row in data:
            emp_no = row[0]
            nickname = row[1]
            gender_id = row[2]
            mobile = row[3]
            remarks = row[4]
            company_name = row[5]
            department_name = row[6]
            duty_id = row[7]
            car_id = row[8]
            license_plate_number = row[9]

            worker = pgsql_db.get(pgsql_cur, worker_sql.format(emp_no))
            if emp_no.isdigit():
                emp_no = str(int(float(emp_no)))
            if type(emp_no) == float:
                emp_no = str(int(emp_no))
            mobile = str(int(float(mobile)))
            d = {
                'emp_no': emp_no,
                'nickname': nickname,
                'gender': gender_id,
                'mobile': mobile,
                'remarks': remarks,
                'company_name': company_name,
                'department_name': department_name,
                'duty_id': duty_id,
                'car_id': car_id,
                'license_plate_number': license_plate_number,
                'status': 1
            }

            if worker:
                d['id'] = worker[0]
                if worker[1] and worker[1] != mobile:
                    d['open_id'] = 'NULL'
                pgsql_db.update(pgsql_cur, d, 'worker')
            else:
                pgsql_db.insert(pgsql_cur, d, 'worker')
                # 查询
                new_worker = pgsql_db.get(pgsql_cur, worker_sql.format(emp_no))

        rds_conn.delete('batch_add_worker')

    @transaction(is_commit=True)
    def batch_add_car(self, pgsql_cur, data):
        """批量添加车辆
        """
        pgsql_db = PgsqlDbUtil
        car_sql = "SELECT id,capacity,company_name FROM car " \
                  "WHERE license_plate_number='{}' AND status = 1 LIMIT 1"
        for row in data:
            license_plate_number = row[0]
            capacity = row[1]
            company_name = row[2]

            car = pgsql_db.get(pgsql_cur, car_sql.format(license_plate_number))
            if car:
                d = {
                    'id': car[0],
                    'license_plate_number': license_plate_number,
                    'capacity': capacity,
                    'company_name': company_name
                }
                pgsql_db.update(pgsql_cur, d, 'car')
            else:

                d = {
                    'code': datetime.now().strftime('%Y%m%d%H%M%S%f'),
                    'license_plate_number': license_plate_number,
                    'capacity': capacity,
                    'device_iid': '',
                    'company_name': company_name,
                    'status': 1
                }
                pgsql_db.insert(pgsql_cur, d, 'car')
        rds_conn.delete('batch_add_car')

    @transaction(is_commit=True)
    def batch_add_school(self, pgsql_cur, data):
        """批量添加学校"""
        pgsql_db = PgsqlDbUtil
        sql = "SELECT id FROM school WHERE school_name='{}' LIMIT 1"
        for row in data:
            school_name = row[0]
            school = pgsql_db.get(pgsql_cur, sql.format(school_name))
            if not school:
                d = {
                    'school_name': school_name,
                    'status': 1
                }
                pgsql_db.insert(pgsql_cur, d, 'school')
        rds_conn.delete('batch_add_school')

    @transaction(is_commit=True)
    def bulk_update_face(self, pgsql_cur, data):
        """批量更新人脸"""
        pgsql_db = PgsqlDbUtil
        zip_url = data['zip_url']

        face_sql = "SELECT id FROM face WHERE stu_no='{}' " \
                   "AND status in (4,5) LIMIT 1"
        feature_sql = "SELECT id FROM feature WHERE face_id={}"
        name_list = utils.zip_name_list(zip_url, config.project_dir)
        for face_name in name_list:
            arr = face_name.split('.')
            print face_name
            if len(arr) == 2:
                stu_no = arr[0]
                face = pgsql_db.get(pgsql_cur, face_sql.format(stu_no))
                if face:
                    face_id = face[0]
                    features = pgsql_db.query(pgsql_cur,
                                              feature_sql.format(face_id))
                    oss_url_str = 'http://' + config.OSSDomain + "/person/face/" + face_name
                    print oss_url_str
                    for feature_row in features:
                        feature_d = {
                            'id': feature_row[0],
                            'oss_url': oss_url_str,
                            'status': 1     # 等待处理
                        }
                        pgsql_db.update(pgsql_cur, feature_d, table_name='feature')

                    face_d = {
                        'id': face_id,
                        'oss_url': oss_url_str,
                        'status': 2  # 未处理
                    }
                    pgsql_db.update(pgsql_cur, face_d, table_name='face')


class DeviceConsumer(object):
    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.device_business = DeviceBusiness(
            config.Productkey, config.MNSAccessKeyId,
            config.MNSAccessKeySecret, self.logger)

    def device_callback(self, ch, method, properties, body):
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'list':
            self.device_business.device_people_list_upgrade(data)
        if routing_suffix == 'listsave':
            self.device_business.device_people_list_save(data)
        if routing_suffix == 'getdevicepeopledata':
            self.device_business.send_get_people_data_msg(data)
        if routing_suffix == 'updatechepai':
            self.device_business.update_chepai(data)
        if routing_suffix == 'devwhitelist':
            self.device_business.dev_white_list_msg(data)
        if routing_suffix == 'clearcnt':
            self.device_business.clear_count(data)
        if routing_suffix == 'delallface':
            self.device_business.delete_all_face(data)
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class DeviceBusiness(object):
    """设备业务"""

    tts = "https://cdbus-dev.oss-cn-shanghai." \
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
        self._pub_msg(device_name, jdata)

    def _publish_del_people_msg(self, device_name, fid):
        """从设备上删除人员"""
        jdata = {
            "cmd": "delface",
            "fid": int(fid)
        }
        self._pub_msg(device_name, jdata)

    def _publish_update_people_msg(self, device_name, fid, nickname,
                                   feature, aac_url):
        """从设备上更新人员"""
        jdata = {
            "cmd": "updateface",
            "fid": int(fid),
            "fno": device_name,
            "name": nickname,
            "feature": feature,
            "ttsurl": aac_url,
            "group": 0,
            "faceurl": "",
            "cardno": ""
        }
        self._pub_msg(device_name, jdata)

    def _publish_add_people_msg(self, device_name, fid, feature, nickname, aac_url):
        """添加人员"""

        jdata = {
            "cmd": "addface",
            "fid": int(fid),
            "fno": device_name,
            "name": nickname,
            "feature": feature,
            "ttsurl": aac_url,
            "group": 0,
            "faceurl": "",
            "go_station": "",
            "return_station": "",
            "school": "",
            "cardno": ""
        }

        self._pub_msg(device_name, jdata)

    def _publish_dev_white_list(self, device_name):
        jdata = {
            "cmd": "devwhitelist",
            "pkt_inx": -1
        }
        self._pub_msg(device_name, jdata)

    def _pub_msg(self, devname, jdata):
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

    def _set_workmode(self, device_name, workmode, chepai, cur_volume, person_limit):
        """
        设置设备工作模式 0车载 1通道闸口 3注册模式
        :param device_name:
        :param workmode:
        :return:
        """
        if workmode not in [0, 1, 3]:
            return -1
        if not cur_volume:
            cur_volume = 100
        cur_volume = cur_volume - 94
        if not chepai:
            return
        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": chepai.encode('utf-8'),
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
            'person_limit': person_limit
        }

        return self._pub_msg(device_name, jdata)

    def dev_white_list_msg(self, data):
        dev_name = data['dev_name']

        try:
            rds_conn.delete("{}_pkt_inx".format(dev_name))
            rds_conn.delete("person_raw_{}".format(dev_name))
        except:
            pass
        self._publish_dev_white_list(dev_name)

    def update_chepai(self, data):
        chepai = data['chepai']
        device_name = data['device_name']
        cur_volume = data['cur_volume']
        workmode = data['workmode']
        person_limit = data['person_limit']
        self._set_workmode(device_name, int(workmode), chepai, cur_volume, person_limit)

    @transaction(is_commit=True)
    def device_people_list_save(self, pgsql_cur, data):
        """保存设备上的信息到数据库"""
        print "=================device_people_list_save====================="
        pgsql_db = PgsqlDbUtil
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
        device_sql = "SELECT id FROM device WHERE device_name='{}' LIMIT 1"
        device = pgsql_db.get(pgsql_cur, device_sql.format(device_name))
        device_id = device[0]

        sql = "SELECT id,info_str FROM device_face_info " \
              "WHERE device_id={} LIMIT 1"
        result = pgsql_db.get(pgsql_cur, sql.format(device_id))
        if result:
            d = {
                'id': result[0],
                'info_str': ",".join(fid_list),
                'update_timestamp': '{}'.format(int(time.time()))
            }
            pgsql_db.update(pgsql_cur, d, 'device_face_info')
        else:
            d = {
                'device_id': device_id,
                'info_str': ",".join(fid_list),
                'update_timestamp': '{}'.format(int(time.time()))
            }
            pgsql_db.insert(pgsql_cur, d, 'device_face_info')

    @transaction(is_commit=False)
    def device_people_list_upgrade(self, pgsql_cur, data):
        """设备人员更新"""
        pgsql_db = PgsqlDbUtil
        print(">>>>> device_people_list_upgrade")
        self.logger.error("device_people_list_upgrade")
        add_list = data['add_list']         # fid
        del_list = data['del_list']         # fid
        update_list = data['update_list']   # fid
        device_name = data['device_name']

        # del list
        if len(del_list) < 60:
            print 'del_list', del_list
            for fid in del_list:
                self._publish_del_people_msg(device_name, fid)

        mfr_sql = "SELECT mfr_id FROM device WHERE device_name = '{}' LIMIT 1"
        mfr_pk = pgsql_db.get(pgsql_cur, mfr_sql.format(device_name))[0]

        feature_sql = "SELECT f.feature,au.nickname,au.aac_url FROM " \
                      "(SELECT feature FROM feature WHERE face_id={} AND " \
                      "mfr_id={}) AS f ,(SELECT nickname,aac_url FROM audio " \
                      "WHERE face_id={}) AS au"
        # update list
        if len(update_list) < 60:
            for fid in update_list:
                obj = pgsql_db.get(
                    pgsql_cur, feature_sql.format(int(fid), mfr_pk, int(fid)))
                print obj
                if obj:
                    print obj
                    self._publish_update_people_msg(
                        device_name, fid, obj[1], obj[0], obj[2])

        # add list
        if len(add_list) < 60:
            for fid in add_list:
                obj = pgsql_db.get(
                    pgsql_cur, feature_sql.format(fid, mfr_pk, fid))
                if obj:
                    print obj
                    self._publish_add_people_msg(
                        device_name, fid, obj[0], obj[1], obj[2])

    def send_get_people_data_msg(self, data):
        """发送获取设备上人员数据的消息"""
        device_name = data['device_name']
        jdata = {
            "cmd": "devwhitelist",
            "pkt_inx": -1
        }
        self._pub_msg(device_name, jdata)

    def clear_count(self, data):
        """清空车内人数"""
        device_name = data['device_name']
        jdata = {
            "cmd": "clearcnt",
            "value": 0
        }
        self._pub_msg(device_name, jdata)

    def delete_all_face(self, data):
        """清空车内人数"""
        device_name = data['device_name']
        jdata = {
            "cmd": "delallface"
        }
        self._pub_msg(device_name, jdata)


class ExportExcelConsumer(object):
    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.excel_business = ExportExcelBusiness(
            config.Productkey, config.MNSAccessKeyId,
            config.MNSAccessKeySecret, self.logger)

    def excel_callback(self, ch, method, properties, body):

        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'exportorder':
            self.excel_business.export_order(data)
        if routing_suffix == 'exportalertinfo':
            self.excel_business.export_alert_record(data)

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
    def export_order(self, pgsql_cur, data):
        pgsql_db = PgsqlDbUtil

        school_id = data.get('school_id', None)
        car_id = data.get('car_id', None)
        order_type = data.get('order_type', None)
        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)
        task_id = data['task_id']

        sql = """
        SELECT O.stu_no,O.stu_name,O.school_name,O.order_type,O.create_time,
        O.license_plate_number,O.gps FROM public.order O 
        WHERE 1=1 {}  ORDER BY O.id DESC 
        LIMIT {} OFFSET {}
        """
        limit = 10000
        page = 1
        offset = (page - 1) * limit

        param_str = ''
        if school_id:
            param_str += ' AND O.school_id={} '.format(school_id)
        if car_id:
            param_str += ' AND O.car_id={} '.format(car_id)
        if order_type:
            param_str += ' AND O.order_type={} '.format(order_type)
        if start_date and end_date:
            param_str += \
                "AND O.create_time between TO_DATE('{}','YYYY-MM-DD') and " \
                "TO_DATE('{}','YYYY-MM-DD')".format(start_date, end_date)

        results = pgsql_db.query(pgsql_cur, sql.format(param_str, limit, offset))
        value_title = [u'身份证号', u'学生姓名', u'学校', u'乘车记录类型',
                       u'乘车时间', u'乘坐车辆', u'gps位置']
        zip_name = u"乘坐记录{}-{}".format(start_date, end_date)
        excel_name = u"乘坐记录第{}部分.xls"
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
                book_name_xls = path + "/" + excel_name.format(zip_index)
            sheet_data = [value_title]
            for index, row in enumerate(results):
                order_type = row[3]
                if order_type == 1:
                    order_type_str = u"上学上车"
                elif order_type == 2:
                    order_type_str = u"上学下车"
                elif order_type == 3:
                    order_type_str = u"放学上车"
                else:
                    order_type_str = u"放学下车"
                create_time_str = row[4].strftime('%Y-%m-%d %H:%M:%S')

                sheet_data.append(
                    [row[0], row[1].decode('utf8'), row[2].decode('utf8'),
                     order_type_str, create_time_str, row[5].decode('utf8'),
                     row[6]])

            utils.write_excel_xls(
                workbook,
                book_name_xls,
                sheet_name.format(offset + 1, offset + limit),
                sheet_data)
            # 下一页
            page += 1
            offset = (page - 1) * limit
            results = pgsql_db.query(
                pgsql_cur, sql.format(param_str, limit, offset))
        local_path = path + '.zip'
        utils.zip_dir(path, local_path)
        oss_key = 'zips/' + zip_name + ".zip"
        utils.upload_zip(oss_key, local_path)
        
        d = {'id': task_id, 'status': 2,
             'zip_url': 'http://' + config.OSSDomain + "/" + oss_key}
        pgsql_db.update(pgsql_cur, d, table_name='export_task')
        # 删除文件
        shutil.rmtree(path)
        os.remove(path + ".zip")

    @transaction(is_commit=True)
    def export_alert_record(self, pgsql_cur, data):
        """
        报警信息
        """
        pgsql_db = PgsqlDbUtil

        status = data.get('status', None)
        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)
        alert_info_type = data.get('alert_info_type', None)
        car_id = data.get('car_id', None)
        task_id = data['task_id']

        sql = """
        SELECT license_plate_number,worker_name_1,worker_name_2,company_name,
        people_number,people_info,alert_start_time,alert_second_time,
        status,gps,cancel_worker_name,cancel_time,cancel_reason
         FROM alert_info WHERE 1=1 
            """
        if status:
            sql += " AND status={}".format(status)
        if alert_info_type:
            alert_info_type = int(alert_info_type)
            if alert_info_type == 1:
                sql += " AND first_alert=1 AND second_alert=0"
            elif alert_info_type == 2:
                sql += " AND second_alert=1"
        if car_id:
            sql += " AND car_id={}".format(car_id)
        if start_date and end_date:
            sql += " AND alert_start_time BETWEEN TO_DATE('{}','YYYY-MM-DD') " \
                   "and TO_DATE('{}','YYYY-MM-DD')".format(start_date, end_date)
        sql += ' ORDER BY id DESC '
        results = pgsql_db.query(pgsql_cur, sql)
        value_title = [u'车牌', u'驾驶员', u'照管员', u'校车公司名字', u'遗漏人数',
                       u'遗漏学生', u'一次报警时间',u'二次报警时间', u'状态',
                       u'gps位置', u'解除人员', u'解除时间', u'解除理由']
        excel_name = u"报警记录.xls"
        sheet_name = u'报警记录'

        path = self.path + "/" + excel_name
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
        sheet_data = [value_title]
        for index, row in enumerate(results):
            alert_second_time = row[7].strftime('%Y-%m-%d %H:%M:%S')\
                if row[7] else ''
            alert_status = u'正在报警' if row[8] == 1 else u'已解除'
            cancel_worker_name = row[10].decode('utf-8') if row[10] else ''
            cancel_time = row[11].strftime('%Y-%m-%d %H:%M:%S')\
                if row[11] else ''
            cancel_reason = row[12].decode('utf-8') if row[12] else ''
            sheet_data.append(
                [row[0].decode('utf-8'), row[1].decode('utf-8'),
                 row[2].decode('utf-8'), row[3].decode('utf-8'), row[4],
                 row[5].decode('utf-8'), row[6].strftime('%Y-%m-%d %H:%M:%S'),
                 alert_second_time, alert_status,
                 row[9], cancel_worker_name,
                 cancel_time,
                 cancel_reason])

        workbook = utils.create_new_workbook()
        utils.write_excel_xls(
            workbook,
            path,
            sheet_name,
            sheet_data)

        oss_key = 'zips/' + excel_name
        utils.upload_zip(oss_key, path)
        d = {'id': task_id, 'status': 2,
             'zip_url': 'http://' + config.OSSDomain + "/" + oss_key}
        pgsql_db.update(pgsql_cur, d, table_name='export_task')
        # 删除文件
        os.remove(path)


class MpMsgConsumer(object):
    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.business = MpMsgBusiness(self.logger)

    def callback(self, ch, method, properties, body):

        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]

        if routing_suffix == 'parents':
            self.business.parents_mp_msg(data)
        if routing_suffix == 'staff':
            self.business.staff_mp_msg(data)

        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class MpMsgBusiness(object):

    def __init__(self, logger):
        self.logger = logger

    def parents_mp_msg(self, data):
        """家长消息"""
        open_id = data['open_id']
        order_id = data['order_id']
        nickname = data['nickname']
        order_type_name = data['order_type_name']
        up_time = data['up_time']
        license_plate_number = data['license_plate_number']

        d = {
            "first": {
                "value": "乘车刷脸成功提醒！",
                "color": "#173177"
            },
            "keyword1": {
                "value": nickname,
                "color": "#173177"
            },
            "keyword2": {
                "value": order_type_name,
                "color": "#173177"
            },
            "keyword3": {
                "value": up_time,
                "color": "#173177"
            },
            "keyword4": {
                "value": license_plate_number,
                "color": "#173177"
            },
            "remark": {
                "value": "点击详情,查看更多！",
                "color": "#173177"
            }
        }
        try:
            wx_mp.template_send(
                config.MP_PARENTS_TEMPLATE_ID, open_id, d,
                url=config.MP_PARENTS_REDIRECT_URL.format(order_id))
        except:
            import traceback
            self.logger.error(traceback.format_exc())

    def staff_mp_msg(self, data):
        """工作人员模板消息"""
        open_id = data['open_id']
        periods = data['periods']
        number = data['number']
        student_info = data['student_info']
        alert_type = data['alert_type']
        time = data['time']
        license_plate_number = data['license_plate_number']

        d = {
            "first": {
                "value": "您好,有学生遗漏在车内,请检查车厢！",
                "color": "#173177"
            },
            "keyword1": {
                "value": number,
                "color": "#173177"
            },
            "keyword2": {
                "value": student_info,
                "color": "#173177"
            },
            "keyword3": {
                "value": alert_type,
                "color": "#173177"
            },
            "keyword4": {
                "value": time,
                "color": "#173177"
            },
            "keyword5": {
                "value": license_plate_number,
                "color": "#173177"
            },
            "remark": {
                "value": "请检查车厢,确认无遗漏学生方可点击详情,解除警报！",
                "color": "#FF0000"
            }
        }
        wx_mp.template_send(
            config.MP_STAFF_TEMP_ID, open_id, d,
            url=config.MP_STAFF_REDIRECT_URL.format(periods))