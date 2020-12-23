# coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import json
import base64
from mns.account import Account
from AcsManager import AcsManager
import config
from utils import get_logger
from define import RedisKey


class ReceiveMessage(object):

    def __init__(self, product_key, mns_access_key_id,
                 mns_access_key_secret, mns_endpoint):
        self.product_key = product_key
        self.mns_access_key_id = mns_access_key_id
        self.mns_access_key_secret = mns_access_key_secret
        self.mns_endpoint = mns_endpoint
        print self.mns_access_key_secret
        print self.mns_access_key_id

        token = ""

        # 初始化 my_account, my_queue
        self.my_account = Account(mns_endpoint, mns_access_key_id,
                                  mns_access_key_secret, token)
        self.queue_name = "aliyun-iot-" + product_key
        self.my_queue = self.my_account.get_queue(self.queue_name)
        self.my_queue.set_encoding(True)
        self.wait_seconds = 3

    def msg_handler(self, acs_manager, logger):
        recv_msg = self.my_queue.receive_message(self.wait_seconds)
        body = json.loads(recv_msg.message_body)
        dev_name = body['topic'].split('/')[2]
        jdata = json.loads(base64.b64decode(body["payload"]))
        # if 'status' in jdata:
        #     if jdata['status'] == "online":
        #         acs_manager.device_open(jdata['deviceName'], jdata['lastTime'])
        #     if jdata['status'] == "offline":
        #         acs_manager.device_close(jdata['deviceName'], jdata['lastTime'])

        acs_manager.check_cur_stream_no(dev_name, jdata)
        print json.dumps(jdata)

        if 'cmd' in jdata:
            cmd = jdata['cmd']
            if cmd == 'syndata':
                dev_name = jdata['devid']
                if dev_name == 'newdev':
                    logger.info(u'注册新设备')
                    acs_manager.create_device(jdata['mac'])

                else:
                    acs_manager.check_version(
                        dev_name, jdata['version'], jdata['devtime'])
                    if jdata['version'] == RedisKey.APPOINT_VERSION_NO:
                        ret = acs_manager.init_device_params(
                            jdata['version'], dev_name, jdata['devtime'],
                            jdata['shd_devid'], jdata['gps'])
                        acs_manager.device_rebooted_setting_open_time(
                            dev_name, jdata['gps'])
                        # 非0直接跳过,0表示已经初始化完成,因为低版本jdata没有cnt
                        if not ret:
                            acs_manager.device_rebooted_setting_params(
                                dev_name, jdata['devtime'], jdata['cnt'])

            elif cmd == 'devwhitelist2':
                logger.info(u"人员列表")
                print u"人员列表"
                acs_manager.add_redis_queue(
                    dev_name, jdata['data'], jdata['pkt_cnt'])

            elif cmd == 'addface':
                # 生成特征值返回的信息
                if 'feature_type' in jdata:
                    acs_manager.save_feature(
                        dev_name, jdata['fid'], jdata['feature'])
                    if jdata['feature']:
                        logger.info(u'生成特征值成功{}'.format(jdata['fid']))
                    else:
                        logger.info(u"生成特征值失败{}".format(jdata['fid']))
            elif cmd == 'updateface':
                pass
            elif cmd == 'delface':
                pass
            elif cmd == 'record':
                if jdata['fid'] == -1:
                    logger.info(u"日志信息")
                    log_id = int(jdata['gps'].split('|')[0])
                    # acc关闭
                    if log_id == 3:
                        AcsManager.acc_close(dev_name)
                else:
                    logger.info(u"添加订单")
                    acs_manager.add_order(jdata['fid'],
                                          jdata['gps'],
                                          jdata['addtime'],
                                          dev_name,
                                          jdata['cnt'])
            elif cmd == 'syndevinfo':
                print u'4g模块\sim卡信息'
                acs_manager.save_imei(dev_name, jdata['imei'])
            elif cmd == 'update':
                if jdata['status'] == 'success':
                    logger.info(u"升级成功")
                else:
                    logger.info(u"升级失败")
            elif cmd == 'batchaddface':
                logger.info(u"批量注册人脸")
            elif cmd == 'batchdelface':
                print u"批量删除人脸"
                print jdata
            elif cmd == 'syndata_ext':
                print u"syndata_ext"
                print jdata

        # 删除消息
        try:
            self.my_queue.delete_message(recv_msg.receipt_handle)
            print("Delete Message Succeed!  ReceiptHandle:%s" % recv_msg.receipt_handle)
        except Exception as e:
            print("Delete Message Fail! Exception:%s\n" % e)

    def run(self):
        print("%sReceive And Delete Message From Queue%s\nQueueName:"
              "%s\nWaitSeconds:%s\n" % (10 * "=", 10 * "=", self.queue_name,
                                        self.wait_seconds))
        from mns.mns_exception import MNSServerException, MNSClientNetworkException
        logger = get_logger(config.log_path)
        acs_manager = AcsManager(
            self.product_key, self.mns_access_key_id,
            self.mns_access_key_secret, config.OSSDomain,
            config.OSSAccessKeyId, config.OSSAccessKeySecret)
        while True:
            try:
                self.msg_handler(acs_manager, logger)
            except MNSServerException as e:
                logger.error(e.message)

                if hasattr(e, 'type') and e.type == u"MessageNotExist":
                    print("Queue is empty")
            except MNSClientNetworkException:
                print u"network exception"
            except Exception as e:
                if hasattr(e, 'type') and e.type == u"QueueNotExist":
                    print("Queue not exist!")
                    sys.exit(0)
                else:
                    import traceback
                    print traceback.format_exc()


if __name__ == '__main__':
    receive_msg = ReceiveMessage(
        config.Productkey, config.MNSAccessKeyId,
        config.MNSAccessKeySecret,
        config.MNSEndpoint)
    receive_msg.run()
