# coding: utf-8
import os
import json
import time
import base64
import shutil
import struct
from datetime import datetime
from msgqueue.db import transaction, PgsqlDbUtil, rds_conn
from msgqueue import config
from msgqueue import utils
from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
from define import grade, classes, gender, duty
import producer


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
        print method
        data = json.loads(body.decode('utf-8'))
        arr = method.routing_key.split(".")
        routing_suffix = arr[-1]
        if routing_suffix == 'workerinsert':
            self.business.car_field_update(data)
        if routing_suffix == 'workerupdate':
            self.business.car_field_update(data)

        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class InsertUpdateBusiness(object):

    def __init__(self, logger):
        self.logger = logger

    @transaction(is_commit=True)
    def car_field_update(self, pgsql_cur, data):
        from collections import defaultdict
        pgsql_db = PgsqlDbUtil
        worker_id = data['worker_id']
        car_id = data['car_id']
        nickname = data['nickname']
        duty_id = data['duty_id']
        duty_name = data['duty_name']
        d = defaultdict()
        d['id'] = car_id
        if duty_id == 1:
            d['worker_1_id'] = worker_id
            d['worker_1_nickname'] = nickname
            d['worker_1_duty_name'] = duty_name
        elif duty_id == 2:
            d['worker_2_id'] = worker_id
            d['worker_2_nickname'] = nickname
            d['worker_2_duty_name'] = duty_name
        pgsql_db.insert(pgsql_cur, d, 'car')


class StudentConsumer(object):

    def __init__(self):
        self.logger = utils.get_logger(config.log_path)
        self.student_business = StudentBusiness(self.logger)

    def student_callback(self, ch, method, properties, body):
        print method
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
        # 消息确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


class StudentBusiness(object):

    def __init__(self, logger):
        self.logger = logger

    @transaction(is_commit=True)
    def batch_add_student(self, pgsql_cur, data):
        """批量添加学生
        身份证号,姓名,性别id,家长1姓名,家长1手机号,家长2姓名,家长2手机号,家庭地址,备注,学校id,年级id,班级id,截止时间,车辆id
        """
        pgsql_db = PgsqlDbUtil

        stu_sql = "SELECT id FROM student WHERE stu_no='{}' LIMIT 1"
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

            student = pgsql_db.get(stu_sql.format(stu_no))
            d = {
                'stu_no': stu_no,
                'nickname': nickname,
                'gender': gender_id,
                'parents_1': parents1_name,
                'mobile_1': parents1_mobile,
                'parents_2': parents2_name,
                'mobile_2': parents2_mobile,
                'address': address,
                'remarks': remarks,
                'school_id': school_id,
                'grade_id': grade_id,
                'class_id': classes_id,
                'end_time': "to_date('{}', 'yyyy-MM-dd')".format(end_time),
                'car_id': car_id,
                'license_plate_number': license_plate_number
            }

            if student:
                d['id'] = student[0]
                pgsql_db.update(pgsql_cur, d, 'student')

            else:
                d['create_time'] = 'now()'
                d['status'] = 1
                pgsql_db.insert(pgsql_cur, d, 'student')
                stu = pgsql_db.get(stu_sql)
                face_d = {
                    'oss_url': '',
                    'status': 1,  # 没有人脸
                    'feature': '',
                    'nickname': nickname,
                    'stu_no': stu_no,
                    'feature_crc': '',
                    'update_time': 'now()',
                    'acc_url': '',
                    'end_timestamp': '',
                    'stu_id': stu[0]
                }
                pgsql_db.insert(pgsql_cur, face_d, 'face')

    @transaction(is_commit=True)
    def batch_add_worker(self, pgsql_cur, data):
        """
        批量添加工作者
        """
        pgsql_db = PgsqlDbUtil
        worker_sql = "SELECT id FROM worker WHERE emp_no='{}' LIMIT 1"
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

            worker = pgsql_db.get(worker_sql.format(emp_no))
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
                'license_plate_number': license_plate_number
            }

            if worker:
                d['id'] = worker[0]
                pgsql_db.update(pgsql_cur, d, 'worker')
                producer.worker_insert(worker.id, car_id, nickname,
                                       duty_id, duty[duty_id])
            else:
                pgsql_db.insert(pgsql_cur, d, 'worker')
                producer.worker_update(worker.id, car_id, nickname,
                                       duty_id, duty[duty_id])

    @transaction(is_commit=True)
    def batch_add_car(self, pgsql_cur, data):
        """批量添加车辆
        """
        pgsql_db = PgsqlDbUtil
        car_sql = "SELECT id FROM car WHERE license_plate_number='{}' LIMIT 1"
        for row in data:
            license_plate_number = row['license_plate_number']
            capacity = row['capacity']
            company_name = row['company_name']

            car_sql = car_sql.format(license_plate_number)
            car = pgsql_db.get(car_sql)
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
                    'worker_str': '',
                    'company_name': company_name
                }
                pgsql_db.insert(pgsql_cur, d, 'car')

    @transaction(is_commit=True)
    def batch_add_school(self, pgsql_cur, data):
        """批量添加学校"""
        pgsql_db = PgsqlDbUtil
        sql = "SELECT id FROM school WHERE school_name='{}' LIMIT 1"
        for row in data:
            school_name = row['school_name']
            school = pgsql_db.get(pgsql_cur, sql.format(school_name))
            if not school:
                d = {
                    'school_name': school_name
                }
                pgsql_db.insert(pgsql_cur, d, 'school')


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
        if routing_suffix == 'listsave':
            self.device_business.device_people_list_save(data)
        if routing_suffix == 'getdevicepeopledata':
            self.device_business.send_get_people_data_msg(data)
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
        device_sql = "SELECT id FROM device WHERE device_name='{}'"
        device_id = pgsql_db.get(device_sql.format(device_name))[0]

        people_data = []
        if fid_list:
            sql = "SELECT id,nickname,emp_no FROM face WHERE id IN (" \
                  + ",".join(fid_list) + ")"
            results = pgsql_db.query(pgsql_cur, sql)
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
                sql = "SELECT id,nickname,emp_no FROM face " \
                      "WHERE id IN ({})".format(",".join(qq))
                print sql
                results = pgsql_db.query(pgsql_cur, sql)
                for row in results:
                    fid = str(row[0])
                    nickname = row[1]
                    emp_no = row[2]
                    s = emp_no + "|" + nickname + "|0"
                    not_updated_person_data.append(s)

        get_sql = 'SELECT id FROM device_people_list ' \
                  'WHERE device_id={} LIMIT 1'
        result = pgsql_db.get(pgsql_cur, get_sql.format(device_id))
        print "-=-=-=-=-=========================="
        print result
        if result:
            pk = result[0]

            d = {
                'id': int(pk),
                'device_people_list_raw': ",".join(people_raw_list),
                'total_number': len(server_face_ids),
                'already_upgrade_number': len(fid_list),
                'update_time': 'now()',
                'device_people': ",".join(people_data),
                'not_updated': ",".join(not_updated_person_data)
            }
            pgsql_db.update(pgsql_cur, d, table_name='device_people_list')
        else:

            d = {
                'device_id': device_id,
                'device_people_list_raw': ",".join(people_raw_list),
                'total_number': len(server_face_ids),
                'already_upgrade_number': len(fid_list),
                'update_time': 'now()',
                'device_people': ",".join(people_data),
                'not_updated': ",".join(not_updated_person_data)
            }
            pgsql_db.insert(pgsql_cur, d, table_name='device_people_list')

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
            for fid in del_list:
                self._publish_del_people_msg(device_name, fid)

        sql = "SELECT feature,nickname " \
              "FROM face WHERE id in ({}) "
        # update list
        if len(update_list) < 60:
            for fid in update_list:
                obj = pgsql_db.get(pgsql_cur, sql.format(int(fid)))
                if obj:
                    self._publish_update_people_msg(
                        device_name, fid, obj[1], obj[0])

        # add list
        if len(add_list) < 60:
            for fid in add_list:
                obj = pgsql_db.get(sql.format(fid))
                if obj:
                    self._publish_add_people_msg(
                        device_name, fid, obj[0], obj[1])

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
        SELECT stu_no,stu_name,school_name,order_type,create_time,
        license_plate_number,up_location FROM order O 
        INNER JOIN school SHL ON SHL.id=O.school_id 
        WHERE 1=1 {} 
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
                "AND O.create_time between to_date('{}','YYYY-MM-DD') and " \
                "to_date('{}','YYYY-MM-DD')".format(start_date, end_date)

        results = pgsql_db.query(pgsql_cur, sql.format(param_str, limit, offset))
        value_title = [u'学生编号', u'学生姓名' u'学校', u'乘车记录类型', 
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
                sheet_data.append([row[0], row[1], row[2], order_type_str, 
                                   create_time_str, row[5], row[6]])

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
             'zip_url': config.OSSDomain + "/" + oss_key}
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
        status,gps,cancel_info FROM alert_info WHERE 1=1 
            """
        if status:
            sql += " AND status={}".format(status)
        if alert_info_type:
            if alert_info_type == 1:
                sql += " AND first_alert=1"
            elif alert_info_type == 2:
                sql += " AND second_alert=1"
        if car_id:
            sql += " AND car_id={}".format(car_id)
        if start_date and end_date:
            sql += " AND alert_start_time BETWEEN to_date('{}','YYYY-MM-DD') " \
                   "and to_date('{}','YYYY-MM-DD')".format(start_date, end_date)

        results = pgsql_db.query(pgsql_cur, sql)
        value_title = [u'车牌', u'驾驶员', u'照管员', u'校车公司名字', u'遗漏人数',
                       u'遗漏学生', u'一次报警时间',u'二次报警时间', u'状态',
                       u'gps位置', u'解除人员', u'解除时间', u'移除理由']
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
            arr = row[10].split(',')
            sheet_data.append([row[0], row[1], row[2], row[3], row[4], row[5],
                               row[6], row[7], row[8], row[9], arr[0],
                               arr[1], arr[2]])

        workbook = utils.create_new_workbook()
        utils.write_excel_xls(
            workbook,
            path,
            sheet_name,
            sheet_data)

        oss_key = 'zips/' + excel_name
        utils.upload_zip(oss_key, path)
        d = {'id': task_id, 'status': 3, 'zip_url': config.OSSDomain + "/" + oss_key}
        pgsql_db.update(pgsql_cur, d, table_name='export_task')
        # 删除文件
        os.remove(path)