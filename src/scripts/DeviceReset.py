# coding:utf-8
import time
import json
import base64
import decimal
from datetime import datetime
from aliyunsdkcore import client

from aliyunsdkcore.client import AcsClient
from aliyunsdkiot.request.v20180120.RegisterDeviceRequest import \
    RegisterDeviceRequest
from aliyunsdkiot.request.v20180120.PubRequest import PubRequest
import db
import config


class Test(object):

    def __init__(self, product_key, mns_access_key_id, mns_access_key_secret):
        self.client = AcsClient(mns_access_key_id,
                                mns_access_key_secret, 'cn-shanghai')
        self.product_key = product_key

    def pub_msg(self, devname, jdata):
        request = PubRequest()
        request.set_accept_format('json')

        topic = '/' + self.product_key + '/' + devname + '/user/get'
        print topic
        request.set_TopicFullName(topic)
        message = json.dumps(jdata, encoding="utf-8")
        print message
        message = base64.b64encode(message)
        request.set_MessageContent(message)
        request.set_ProductKey(self.product_key)
        # request.set_Qos("Qos")

        response = self.client.do_action_with_exception(request)
        print response
        return response

    def set_workmode(self, device_name, workmode):
        """
        设置设备工作模式
        :param device_name:
        :param workmode:
        :return:
        """
        if workmode not in [0, 1, 3]:
            return -1
        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": "川A:AD123456",
            "workmode": workmode,
            "delayoff": 2,
            "leftdetect": 1,
            "jiange": 10,
            "cleartime": 70,
            "shxmode": 1,
            "volume": 6,
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "noreg": 1,
            "light_type": 0
        }
        return self.pub_msg(device_name, jdata)

    def reset(self):
        d = {"cmd": "reset000"}
        self.pub_msg('dev_61', d)

    @db.transaction(is_commit=True)
    def init_all_people(self):
        mysql_db = db.MysqlDbUtil(self.mysql_cur)
        results = mysql_db.query('SELECT `id`,`feature_crc` FROM `face` '
                                 'WHERE `status`=1 AND `feature` IS NOT NULL')
        face_ids = [str(row[0]) for row in results]

        self.pub_msg()

    def publish_del_people_msg(self, device_name, fid):
        """从设备上删除人员"""
        jdata = {
            "cmd": "delface",
            "fid": int(fid)
        }
        self.pub_msg(device_name, jdata)

    def register(self):
        # 发布消息注册
        msg = {
            "cmd": "devid",
            "devname": 'dev_31',
            "productkey": 'a1vperyb2Cg',
            "devsecret": '3973ed8bf2a45c31e0153ffc7b3cbf66',
            "devicetype": 0,
            "time": int(time.time())
        }
        self.pub_msg('newdev', msg)

    def register_to_device(self):
        d = {'ttsurl': 'https://cdbus-dev.oss-cn-shanghai.aliyuncs.com/person/video/qsc.aac',
             'go_station': '',
             'return_station': '',
             'faceurl': '',
             'school': '',
             'group': 0,
             'name': '17975',
             'cmd': 'addface',
             'feature': u'6RBtPbpPXbwWjz89XJzRvDVuG76LiLU8PitmPej2XD2NdYO9X0WcuxySjT3/o4O7Uq5VPL89eLudebi82pvPveqtB70kL1Q9+DUrvZhRlj2mm2q8KWWTPAun0L3g/Zk8uJJ3PbDoiz2QW5I8lgQYvGfCRDy0LCe9jWvXu67JTj1Qgw497FIwvP5vmzvsjlg8VSgkPSq6trt0csU9Tw4kPmloBj0GEhI980yePZ3tD7vYO/O8jBSbOraIprwFLQA9fXwCPEMuBL4AmVa9qMiMO346YD0mtuI9EgmzPWt2iL0e3uU9TPSPvaXaE75E+i66LgbPPDtWYb0XvMs9bMcYPFZyirxnuiy+rjWLvc+E6T3iBSk9dEV6vSQ1qr3j0QY9OvuSvfcKuT3kjIi9rpQuPaCCwrz0x6y9Pxc6Pc1bkDyYPY09j2ooPbZ9qT3LAH49TGI3uttT2rtHlrk8OeJdPQBYx7rDTVe9CckkvRJQhTzUusC9cNjxPNraX70TdYE8YJ6/PZY5ij1sdk89IJ0ouypCIj3jDYE9d26SPQChnjwvQwE+WvgkPeZPaj3HRQU9TqTqulFjSz0Kh/+9KC8ZPdE62TxWebw9r6n3PM9fHbxvRFw9maufPEzFeL1fqtM8LqNNPSyX7jyTsQO9YC2IvaWXCT20WAm9L1nBvEU32D06V409aGCzPGlsgL06+V69lhO5PY+nLL1FutA8QbFUPR9GU70dG2E8a8qtPPjuvjx/Gjm96E38PIuA1jvRG/29Ql00PedD8b0dUDQ9AJBNPaZqU7tn+iA7b6XkPbrZS72da1e8hCmAva3Ikb3xNj++41+cParNojx3xik97FstvVP97Lzfscg8Gh4OPrOMrT2BvJu8/rJ1PKsdED3Jo587Kf/pO2A1kD3PJjm9IqNHvQSg3rxn8/478npePZTjq7wcWaK7UC9NPeUGYb2hvTK8vSOhPcQQ/Tu7grg8SgJSPaWGZr3FZ8O9rKHWPETovT3YsqU9FBQFPj9x3Txs7+M8pgTovIs+mL0hlzk8SulUvX+39bxzOxq+sRCnOwcDQb3ahZg96PWhPAJWq71GKOW8Pf+hPeBjwDz2saU80xJ0vdKRsr2Bb6E9ZgSPvXqMGj0UXmK80N4APRsg0bzE3te8C4tXPR+67L1L35E9gpMwPQDyz7uJKZ09ZlcYu19ugrzSIBM9mTWqvUGbRLuAbmM86diCvYAyT7vtIh092KhhPRXJIT2Wx6Y9ZssVPtzjt70rLSg+BY5+vV/qH73UuNY9q8XyvJWcjTyOTu47UOctPMJp/bxj9K09rbbyPVRU0z1QOrw6DYF1veKSmr1H1xm+9IaWPXTNDj0teWi8Uc8CvQ==',
             'fid': 17975, 'cardno': '', 'fno': u'dev_5'}

        self.pub_msg('dev_5', d)

    def people_list(self):
        jdata = {
            "cmd": "devwhitelist",
            "pkt_inx": -1
        }
        self.pub_msg('dev_6', jdata)

    def upgrade_232(self):
        #d = {'url': 'https://img.pinganxiaoche.com/apps/1600666302.yaffs2', 'crc': -282402801, 'cmd': 'update', 'version': 232, 'size': 4756736}
        d = {"url": "https://img.pinganxiaoche.com/apps/1603938449.yaffs2", "crc": -163501493, "cmd": "update", "version": 237, "size": 4767616}
        self.pub_msg('dev_77', d)

    def batchaddface(self):
        """批量添加人脸"""
        jdata = {
            "url": 'https://cdbus-dev.oss-cn-shanghai.aliyuncs.com/txts/1597287230.txt',
            "cmd": "batchaddface"
        }
        self.pub_msg('dev_19', jdata)

    def get_version(self):
        d = {
            'cmd': 'version'
        }
        self.pub_msg('dev_38', d)

    def batchdelface(self):
        jdata = {
            "fids": "25002,25003,25004,25005",
            "cmd": "batchdelface"
        }
        self.pub_msg('dev_37', jdata)

    def devwhitelist(self):
        jdata = {
            "cmd": "devwhitelist",
            "pkt_inx": -1
        }
        self.pub_msg("dev_33", jdata)

    def set_plea(self):
        jdata = {
            "cmd": "set_audiotype",
            "value": 1
        }
        self.pub_msg("dev_7", jdata)

    def ddddddddd(self):
        jdata = {
            "cmd": "syntime",
            "time": int(time.time()),
            "chepai": "test",
            "workmode": 3,
            "delayoff": 2,
            "leftdetect": 1,
            "jiange": 10,
            "cleartime": 70,
            "shxmode": 0,
            "volume": -20,
            "facesize": 390,
            "uploadtype": 1,
            "natstatus": 0,
            "timezone": 8,
            "temperature": 0,
            "noreg": 1,
            "light_type": 0
        }
        self.pub_msg("dev_55", jdata)

    def testest(self):
        start = time.time()
        rds = db.rds_conn
        print len(list(rds.sinter('test', 'test1')))

    def set_oss(self):
        OSSDomain = 'https://cdbus-dev.oss-cn-shanghai.aliyuncs.com'
        OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
        OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'
        jdata = {
            "cmd": "ossinfo",
            "ossdomain": OSSDomain,
            "osskeyid": OSSAccessKeyId,
            "osskeysecret": OSSAccessKeySecret[12:] + OSSAccessKeySecret[:12]
        }
        self.pub_msg("dev_55", jdata)

    def update_face(self):
        jdata = {
            "cmd": "updateface",
            "fid": 15,
            "fno": "",
            "name": "简超",
            "feature": "wSJGPc6mbj3vsQ08pC+IvbU4hzzOBPC8X1eEvFKZGD1mIa89BfZgvVMh3zxMTCk9VsWfPQabmLpQLy88JXOgveGJrbyZgyY931dOPfOZaj0nkYI8u3QQvdkZ/rxmrdk9mZdJveJvxrun/5M821aMO34i3L2btJ06Oahvu8RwMD3Y5je8GNJUvRo6Nr2XiwM9j5LzPOLMgTxuQA283WobvSJSXzxJzja8plzsvWt1Eb0C7Ju9rdCvOg1Ohr1YjGa7qYWNvH5xhD09CVG8VRVlvS2P2zw+4S09jpAsu7KYGr2UDxu74I/8vREZcb0PjJq9IN+tvCKIHT2JxvU8uVmNvehb4jxK9Ae+hwwfPZZPi7xZqHs9tZiHvXfFhzwNOmE9j/DRPOc+Dz1mqzQ9A9jqPe1JSj0zKsE7TH+wPQCKjz0GKJY9du5xPXNHBj2ADW49/mZKveOd0D2TsAo+8/E9u9F3Gz1c3He9m7a3POaEuT1yUwG+smv6vEyORj3YSZk8baYxPQUjijyb6mG9KB+pvd43Ab1b7Y69+9GYvbw+Szwlq8I9B386O9ZMgj1ghLC9bcAnvepYnbymu0S8s8PavPRdObyiPcY9N/IqvZxEsj18hrY9ye+iPTvzyL1PxWo9w9IJPUTxJ707lJ69xSmvvA0sQz3qy649Jtu0PFRKbLxzFGE8AgHXPdMwBDwGOuy4H0RXPGK5XjxHmQ09JmpfvKIse7xc9/M92Z+GvLZmnrsUTj497z7PvH6QoL1+pxo9+QmLukrkyr30xoq9TEwsPamuiT00DKY9m4zrPW9RhbywFGi9PT6nvDlv4r0o8L49ng60u2tBML0YuWM9MpaMvb4eRL0EqEk8cjOpPfhj6rw/z8s9hqo9vDiMUb0pbcM9S9+ZvL0JXT0/5u09/6yDPc4PQzxYL3s8euDsvE4kVb17vCW92znhO67NzruVH3u9v7RHPYFwkzxeEDa8N0ucPVNAnDyx/wS98zcZPho+lT3ubZY9Ww6evMTr7bmsLQs++WPCPfTZID0XVde99WdTPbUu5LylrBa9+1RHPWv6vr0dTnu9IhgMvj6YuL1kGL+96avMPUL2iD39myo9VGXzu5tTxb3IsVG9o5QWPfLcVLtaFAY9LZ2OPaRixDwzbKq9WXmsPYDqPbz30Im7IJBSvTUHYjy67Qo+ylSnPT3KTT17/CG9/wyCvYrEoLwcVI08u2JqPQSTW71O2Q6+0CQnPLaEKj5zW4I8ysSEvKsM3rzZetI9sUjrPWpkj72Nfja+c9HpvUZNw7zJQru8ryNUvUK1Jj11wRs9BO7QPVocXz3Duok9QsFbPYruUzyqlg4+j+3mPXS44bwAlwK9W7A9vQ==",
            "ttsurl": "http://cdbus-dev.oss-cn-shanghai.aliyuncs.com/audio/123456789012345678.aac",
            "group": 0,
            "faceurl": "",
            "cardno": ""
        }

        self.pub_msg("dev_57", jdata)

    def delte_key(self):
        ks = db.rds_conn.keys('hash:token.id:*')
        for row in ks:
            db.rds_conn.delete(row)

    @db.transaction(is_commit=True)
    def generate_crc(self, cursor):
        import zlib
        pgdb = db.PgsqlDbUtil
        results = pgdb.query(cursor, 'SELECT id,feature_crc,feature FROM face')
        for row in results:
            d = {
                'id': row[0],
                'feature_crc': zlib.crc32(base64.b64decode(row[2]))
            }
            pgdb.update(cursor, d, 'face')

    def clear_car_number(self):
        jdata = {
            "cmd": "clearcnt",
            "value": 0
        }
        self.pub_msg("dev_57", jdata)


if __name__ == '__main__':
    t = Test(config.Productkey, config.MNSAccessKeyId,
             config.MNSAccessKeySecret)
    #t.ddddddddd()
    t.reset()

    # import struct
    #
    # fid_dict = {}
    # d = [u'"10MAAF21hc87HfqgAAAAAA=="', u'"rGEAANbjmHISlXvoAAAAAK1hAACSQfwOs07CZAAAAACqYQAAbpKnMs+HitIAAAAAq2EAAPJyneLoulOBAAAAAA=="', u'"WEMAAPp8iaEX3yf/AAAAAFpDAABonU8dU13P4gAAAABeQwAA87eimGjhVbQAAAAAX0MAAFcUV+hGuhUxAAAAAGVDAADq6yEMIOtq2wAAAABnQwAAwg7PY3q/2JsAAAAAaEMAAG9eKIG/XCI5AAAAAGlDAACDXuYljYmJTAAAAAA="', u'"UUQAAD090QvRtmnpAAAAAA=="', u'"+EMAAB/DUvP6AGI8AAAAAA=="', u'"ukUAADYQicG4IIg5AAAAALtFAADpic+jvSQ/oAAAAAC/RQAAAxJPZTofNokAAAAAwkUAADHTU1CQARWTAAAAAMNFAACFulQKPjbt9gAAAAA="', u'"qEYAAHpIwuRXKpLcAAAAAA=="', u'"UkYAAG32SpxaYvRNAAAAAFNGAAD8KCxdX4/uEgAAAAA="', u'"jkgAALz+9z6XyE9+AAAAAA=="', u'"8UsAAPCeKqbtssHfAAAAAA=="', u'"xV4AADerwTjkOGTWAAAAAMZeAAArndq8TWEL4wAAAADHXgAAKN+C9KYv3ckAAAAAyl4AAHnvpgnHfsmPAAAAAM1eAABn7NJj8z+oDAAAAAA="', u'"PV8AADxyT4d+3/VEAAAAAA=="']
    # for row in d:
    #     data = base64.b64decode(row)
    #     length = len(data)
    #     offset = 0
    #     while offset < length:
    #         s = data[offset: offset + 16]
    #         ret_all = struct.unpack('<IiiI', s)
    #         fid = ret_all[0]
    #         feature_crc = ret_all[2]
    #         fid_dict[str(fid)] = feature_crc
    #         offset += 16
    # print fid_dict.keys()