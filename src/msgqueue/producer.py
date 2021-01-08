# coding:utf-8
"""
所有消息的定义在此文件定义
业务层调用 generate_create_company_msg  generate_create_user_msg
"""
import json
import pika
from collections import defaultdict

conn = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost', heartbeat=0))
channel = conn.channel()
channel.exchange_declare(exchange='student_exchange', exchange_type='topic')
channel.exchange_declare(exchange='device_exchange', exchange_type='topic')
channel.exchange_declare(exchange='excel_exchange', exchange_type='topic')
channel.exchange_declare(exchange='mpmsg_exchange', exchange_type='topic')


def _publish_msg(exchange, routing_key, message):
    """发布消息"""
    channel.basic_publish(exchange=exchange,
                          routing_key=routing_key,
                          body=message, mandatory=True)


def get_device_people_data(device_name):
    """获取设备人员数据
    service调用发送
    """
    data = {
        'device_name': device_name
    }
    _publish_msg('device_exchange', 'device.getdevicepeopledata', json.dumps(data))


def device_people_list_save(people_list_str, server_face_ids, device_name):
    """设备人员数据保存到db
    :param people_list_str 逗号分割的人员数据base64编码字符串
    :param server_face_ids 服务器上该设备应该更新的人员fid
    :param device_name 设备名字
    """
    data = {
        'people_list_str': people_list_str,
        'server_face_ids': server_face_ids,
        'device_name': device_name
    }
    _publish_msg('device_exchange', 'device.listsave', json.dumps(data))


def device_people_update_msg(add_list, del_list, update_list, device_name):
    """设备人员列表更新"""
    data = {
        "add_list": add_list,
        "del_list": del_list,
        "update_list": update_list,
        "device_name": device_name
    }
    _publish_msg('device_exchange', 'device.list', json.dumps(data))


def export_order_excel_msg(school_id, car_id, order_type,
                           start_date, end_date, task_id):
    """导出订单excel消息"""
    data = {
        "school_id": school_id,
        "car_id": car_id,
        "order_type": order_type,
        "start_date": start_date,
        "end_date": end_date,
        "task_id": task_id
    }
    _publish_msg('excel_exchange', 'excel.exportorder', json.dumps(data))


def export_alert_info_msg(status, start_date, end_date,
                          alert_info_type, car_id, task_id):
    """导出报警消息"""
    data = {
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'alert_info_type': alert_info_type,
        'car_id': car_id,
        'task_id': task_id,
    }
    _publish_msg('excel_exchange', 'excel.exportalertinfo', json.dumps(data))


def batch_add_student(data):
    """批量添加学生"""
    _publish_msg('student_exchange', 'student.batchaddstudent',
                 json.dumps(data))


def batch_add_worker(data):
    """批量添加工作者"""
    _publish_msg('student_exchange', 'student.batchaddworker',
                 json.dumps(data))


def batch_add_car(data):
    """批量添加车辆"""
    _publish_msg('student_exchange', 'student.batchaddcar',
                 json.dumps(data))


def batch_add_school(data):
    """批量添加学校"""
    _publish_msg('student_exchange', 'student.batchaddschool',
                 json.dumps(data))


def heartbeat():
    """msg心跳"""
    _publish_msg('heartbeat_exchange', 'heartbeat',
                 json.dumps({'heartbeat': 1}))


# def worker_insert(worker_id, car_id, nickname, duty_id, duty_name):
#     d = {
#         'worker_id': worker_id,
#         'car_id': car_id,
#         'nickname': nickname,
#         'duty_id': duty_id,
#         'duty_name': duty_name
#     }
#     _publish_msg('cascade_exchange', 'cascade.workerinsert', json.dumps(d))
#
#
# def worker_update(worker_id, car_id, nickname, duty_id, duty_name, empty=0):
#     d = {
#         'worker_id': worker_id,
#         'car_id': car_id,
#         'nickname': nickname,
#         'duty_id': duty_id,
#         'duty_name': duty_name,
#         'empty': empty
#     }
#     _publish_msg('cascade_exchange', 'cascade.workerupdate', json.dumps(d))


def car_update(car_id, license_plate_number):
    d = {
        'id': car_id,
        'license_plate_number': license_plate_number
    }
    _publish_msg('cascade_exchange', 'cascade.carupdate', json.dumps(d))


def update_chepai(device_name, chepai, cur_volume, workmode, person_limit):
    """更新车牌"""
    data = {
        "chepai": chepai,
        "device_name": device_name,
        "cur_volume": cur_volume,
        "workmode": workmode,
        "person_limit": person_limit
    }
    _publish_msg('device_exchange', 'device.updatechepai', json.dumps(data))


def dev_while_list(device_name):
    data = {
        'dev_name': device_name
    }
    _publish_msg('device_exchange', 'device.devwhitelist', json.dumps(data))


def send_parents_template_message(
        open_id, order_id, nickname, order_type_name,
        up_time, license_plate_number):
    """发送家长模板消息"""
    data = defaultdict()
    data['open_id'] = open_id
    data['order_id'] = order_id
    data['nickname'] = nickname
    data['order_type_name'] = order_type_name
    data['up_time'] = up_time
    data['license_plate_number'] = license_plate_number
    _publish_msg('mpmsg_exchange', 'mpmsg.parents', json.dumps(data))


def send_staff_template_message(
        open_id, periods, number, student_info,
        alert_type, time, license_plate_number):
    """发送工作人员模板消息"""
    data = defaultdict()
    data['open_id'] = open_id
    data['periods'] = periods
    data['number'] = number
    data['student_info'] = student_info
    data['alert_type'] = alert_type
    data['time'] = time
    data['license_plate_number'] = license_plate_number
    _publish_msg('mpmsg_exchange', 'mpmsg.staff', json.dumps(data))


def clear_device_person_count(device_name):
    """清空设备车内人数"""
    data = {'device_name': device_name}
    _publish_msg('device_exchange', 'device.clearcnt', json.dumps(data))


# 测试用户创建
if __name__ == "__main__":
    # generate_create_student_msg(12)
    device_people_update_msg([], [], ['440', '441', '442', '443', '444'],
                             'dev_1')
