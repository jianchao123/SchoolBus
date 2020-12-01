# coding:utf-8
"""
所有消息的定义在此文件定义
业务层调用 generate_create_company_msg  generate_create_user_msg
"""
import json
import pika

queue_conn = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost', heartbeat=0))
channel = queue_conn.channel()
channel.exchange_declare(exchange='user_exchange', exchange_type='topic')
channel.exchange_declare(exchange='device_exchange', exchange_type='topic')
channel.exchange_declare(exchange='excel_exchange', exchange_type='topic')


def _publish_msg(exchange, routing_key, message):
    """发布消息"""
    channel.basic_publish(exchange=exchange,
                          routing_key=routing_key,
                          body=message, mandatory=True)


def generate_create_user_msg(user_id):
    """生成创建用户的消息"""
    data = {
        "user_id": user_id
    }
    _publish_msg('user_exchange', 'user_created', json.dumps(data))


def get_device_people_data(device_name):
    """获取设备人员数据"""
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


def device_people_add_msg(fid, feature, parent_enterprise_id):
    """设备人员添加"""
    data = {
        "fid": fid,
        "feature": feature,
        "parent_enterprise_id": parent_enterprise_id
    }
    _publish_msg('device_exchange', 'device.add', json.dumps(data))


def device_people_delete_msg(fid, parent_enterprise_id):
    """设备人员删除"""
    data = {
        "fid": fid,
        "parent_enterprise_id": parent_enterprise_id
    }
    _publish_msg('device_exchange', 'device.delete', json.dumps(data))


def export_order_excel_msg(parent_company_id, child_company_id,
                           department_id, year, month, task_id):
    """导出订单excel消息"""
    data = {
        "parent_company_id": parent_company_id,
        "child_company_id": child_company_id,
        "department_id": department_id,
        "year": year,
        "month": month,
        "task_id": task_id
    }
    _publish_msg('excel_exchange', 'excel.order', json.dumps(data))


def export_people_info_msg(parent_company_id, child_company_id,
                           department_id, admin_name, task_id):
    """导出人员信息"""
    data = {
        "parent_company_id": parent_company_id,
        "child_company_id": child_company_id,
        "department_id": department_id,
        "admin_name": admin_name,
        "task_id": task_id
    }
    _publish_msg('excel_exchange', 'excel.empinfo', json.dumps(data))


def export_people_statistics_msg(parent_company_id, child_company_id,
                                 department_id, year, month, task_id):
    """导出人员统计数据"""
    data = {
        "parent_company_id": parent_company_id,
        "child_company_id": child_company_id,
        "department_id": department_id,
        "year": year,
        "month": month,
        "task_id": task_id
    }
    _publish_msg('excel_exchange', 'excel.empstatistics', json.dumps(data))


def update_chepai(device_name, chepai, cur_volume):
    """更新车牌"""
    data ={
        "chepai": chepai,
        "device_name": device_name,
        "cur_volume": cur_volume
    }
    _publish_msg('device_exchange', 'device.updatechepai', json.dumps(data))


def batch_add_user(data):
    """批量添加用户"""
    _publish_msg('user_exchange', 'user.batchadd', json.dumps(data))


def heartbeat():
    """msg心跳"""
    _publish_msg('heartbeat_exchange', 'heartbeat',
                 json.dumps({'heartbeat': 1}))


# 测试用户创建
if __name__ == "__main__":
    # generate_create_user_msg(12)
    device_people_update_msg([], [], ['440', '441', '442', '443', '444'],
                             'dev_1')
