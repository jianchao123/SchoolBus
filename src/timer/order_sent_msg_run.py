# coding:utf-8
"""
发设备顺序发送消息
"""
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

project_src_dir = os.path.dirname(os.path.realpath(__file__))
project_src_dir = os.path.dirname(project_src_dir)
sys.path.insert(0, project_src_dir)

import time
import base64
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
from timer import db
from timer import config

client = AcsClient(config.MNSAccessKeyId,
                   config.MNSAccessKeySecret, 'cn-shanghai')
product_key = config.Productkey
request = PubRequest()
request.set_Qos(0)
request.set_accept_format('json')


def order_sent_msg():
    """顺序发送消息"""
    while True:
        try:
            rds_conn = db.rds_conn
            device_name_queue = rds_conn.lrange('DEVICE_NAME_QUEUE', 0, -1)
            for device_name in device_name_queue:
                k = "cur_{}_stream_no".format(device_name)
                # 不存在就取出一条消息发送到物联网
                if not rds_conn.get(k):
                    queue_name = 'mns_list_' + device_name
                    raw_msg_content = rds_conn.lpop(queue_name)
                    if raw_msg_content:
                        data = json.loads(raw_msg_content)
                        stream_no = data['stream_no']
                        rds_conn.set(k, stream_no)
                        rds_conn.expire(k, 30)

                        # 测试使用,需要删除
                        #rds_conn.delete(k)

                        # 发送消息
                        topic = '/' + product_key + '/' \
                                + device_name + '/user/get'
                        request.set_TopicFullName(topic)

                        b64_str = base64.b64encode(json.dumps(data))
                        request.set_MessageContent(b64_str)
                        request.set_ProductKey(product_key)

                        client.do_action_with_exception(request)
        except:
            import traceback
            err_msg = traceback.format_exc()
            print err_msg
            db.logger.error(err_msg)
        time.sleep(1)


if __name__ == "__main__":
    order_sent_msg()