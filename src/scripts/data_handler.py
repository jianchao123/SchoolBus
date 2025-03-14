# coding:utf-8
import time
import json
import os
import oss2
from PIL import Image
import requests
import time
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

project_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))))


# class DataHandler(object):
#
#     @db.transaction(is_commit=True)
#     def new_mfr(self, pgsql_cur):
#         """新厂商添加新数据"""
#         pass
#
#     @db.transaction(is_commit=True)
#     def add_data_to_audio_feature(self, pgsql_cur):
#         """添加数据到audio feature
#         只能用于武汉的设备
#         """
#         pgsql_db = db.PgsqlDbUtil
#         sql = "SELECT id FROM manufacturer WHERE status=1"
#         mfr_list = []
#         results = pgsql_db.query(pgsql_cur, sql)
#         for row in results:
#             mfr_list.append(row[0])
#
#         face_sql = "SELECT id,oss_url,feature,feature_crc," \
#                    "status,aac_url,nickname,stu_no " \
#                    "FROM face WHERE status != 10"
#         query_audio_sql = "SELECT id FROM audio WHERE face_id={} LIMIT 1"
#         query_feature_sql = "SELECT id FROM feature " \
#                             "WHERE face_id={} and mfr_id={} LIMIT 1"
#         face_set = pgsql_db.query(pgsql_cur, face_sql)
#         for face_row in face_set:
#             face_id = face_row[0]
#             oss_url = face_row[1]
#             feature = face_row[2]
#             feature_crc = face_row[3]
#             face_status = face_row[4]
#             aac_url = face_row[5]
#             nickname = face_row[6]
#             stu_no = face_row[7]
#
#             audio_row = pgsql_db.get(pgsql_cur, query_audio_sql.format(face_id))
#             # 不存在
#             if not audio_row:
#                 # audio
#                 a_d = {
#                     'aac_url': aac_url,
#                     'nickname': nickname,
#                     'stu_no': stu_no,
#                     'status': 3,
#                     'face_id': face_id
#                 }
#                 pgsql_db.insert(pgsql_cur, a_d, table_name='audio')
#
#             # feature
#             for mfr_id in mfr_list:
#                 # 厂商是武汉就添加feature数据
#                 # 是否存在
#                 feature_row = pgsql_db.get(
#                     pgsql_cur, query_feature_sql.format(face_id, mfr_id))
#                 if not feature_row:
#                     d = {
#                         'mfr_id': mfr_id,
#                         'face_id': face_id
#                     }
#                     if face_status == 1:
#                         d['status'] = -1
#                     else:
#                         # 等待处理
#                         if face_status == 2:
#                             d['status'] = 1
#                         # 处理中
#                         if face_status == 3:
#                             d['status'] = 2
#                         # 有效
#                         if face_status == 4:
#                             d['status'] = 3
#                         # 预期数据准备失败
#                         if face_status == 5:
#                             d['status'] = 4
#                         # 过期
#                         if face_status == 6:
#                             d['status'] = 3
#                         d['oss_url'] = oss_url if oss_url else 'null'
#                         d['feature'] = feature if feature else 'null'
#                         d['feature_crc'] = feature_crc if feature_crc else 'null'
#                     pgsql_db.insert(pgsql_cur, d, table_name='feature')
#
#
# class FeatureHttps(object):
#
#     @db.transaction(is_commit=True)
#     def change_http(self, pgsql_cur):
#         """
#         修改协议
#         """
#         pgsql_db = db.PgsqlDbUtil
#         results = pgsql_db.query(pgsql_cur, "SELECT oss_url,id FROM feature")
#         for row in results:
#             oss_url = row[0]
#             pk = row[1]
#             if "https" in oss_url:
#                 d = {
#                     'id': pk,
#                     'oss_url': oss_url.replace('https', 'http')
#                 }
#                 pgsql_db.update(pgsql_cur, d, table_name='feature')


class DataHandler(object):

    def __init__(self):
        auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
        self.bucket = oss2.Bucket(auth, config.OSSEndpoint, config.OSSBucketName)

    @db.transaction(is_commit=False)
    def rds_mysql_match(self, pgsql_cur):
        """比对redis和mysql设备状态"""

        pgsql_db = db.PgsqlDbUtil
        rds = db.rds_conn
        sql = "select device_name,status from device where status!=10;"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            dev_name = row[0]
            status = row[1]
            rds_status = rds.hget('DEVICE_CUR_STATUS_HASH', dev_name)
            if not rds_status or status != int(rds_status):
                print dev_name, status, rds.hget('DEVICE_CUR_STATUS_HASH', dev_name)

    @db.transaction(is_commit=False)
    def all_heartbeat(self, pgsql_cur):
        """
        所有心跳的设备是否存在于数据库
        """
        pgsql_db = db.PgsqlDbUtil
        rds = db.rds_conn

        sql = "select id,status,device_name from device where device_name='{}'"
        d = rds.hgetall('ALL_HEARTBEAT_HASH')
        for k, v in d.items():
            obj = pgsql_db.get(pgsql_cur, sql.format(k))
            print obj
            if not obj:
                print "not found devname={}".format(k)
            else:
                if obj[1] == 10:
                    print "found devname={} status={} pk={}".format(k, str(obj[1]), obj[0])

    @db.transaction(is_commit=True)
    def mfr_del(self, pgsql_cur, *args):
        """
        删除厂商
        """
        pk = args[0]
        pgsql_db = db.PgsqlDbUtil
        if pk:
            results = pgsql_db.query(pgsql_cur, "SELECT id FROM feature WHERE mfr_id={}".format(pk))
            for row in results:
                feature_id = row[0]
                pgsql_db.execute_sql(pgsql_cur, "DELETE FROM feature WHERE id={}".format(feature_id))

            pgsql_db.execute_sql(pgsql_cur, "DELETE FROM manufacturer WHERE id={}".format(pk))

    @db.transaction(is_commit=True)
    def mfr_add(self, pgsql_cur, *args):
        """
        添加厂商
        """
        pgsql_db = db.PgsqlDbUtil
        pk = args[0]
        name = args[1]

        # 添加厂商
        obj = pgsql_db.get(pgsql_cur, "SELECT id FROM manufacturer WHERE "
                                      "id={} LIMIT 1".format(pk))
        if not obj:
            d = {
                'id': int(pk),
                'name': name,
                'status': 1
            }
            pgsql_db.insert(pgsql_cur, d, table_name='manufacturer')

        # 添加feature
        face_results = pgsql_db.query(
            pgsql_cur, "SELECT id,oss_url FROM face WHERE status!=10")
        for row in face_results:
            face_id = row[0]
            oss_url = row[1]
            print face_id, oss_url
            feature_d = {
                'oss_url': oss_url,
                'mfr_id': pk,
                'face_id': face_id,
                'status': 1
            }
            pgsql_db.insert(pgsql_cur, feature_d, table_name='feature')

    @staticmethod
    def _feature_status(face_status, feature_results):
        """1表示所有feature生成成功 0失败"""
        feature_status = 1

        # face完成
        if face_status == 4:
            for feature_row in feature_results:
                if feature_row[1] != 3:
                    feature_status = 0
        # face 未绑定人脸
        if face_status == 1:
            for feature_row in feature_results:
                if feature_row[1] != -1:
                    feature_status = 0

        # face 等待处理
        if face_status == 2:
            for feature_row in feature_results:
                if feature_row[1] not in (1, 2, 3):
                    feature_status = 0

        # face 预期数据准备失败
        if face_status == 5:
            for feature_row in feature_results:
                if feature_row[1] not in (3, 4):
                    feature_status = 0
            # 且不能两条数据都是3
            if feature_results[0][1] == 3 or feature_results[1][1] == 3:
                if not (feature_results[0][1] ^ feature_results[1][1]):
                    feature_status = 0
        # face 过期
        if face_status == 6:
            for feature_row in feature_results:
                if feature_row[1] not in (3, 4):
                    feature_status = 0
        return feature_status

    @db.transaction(is_commit=False)
    def stu_data_integrity(self, pgsql_cur, *args):
        """学生数据完整性"""
        pgsql_db = db.PgsqlDbUtil
        stu_sql = "SELECT id FROM student WHERE status=1 order by id desc"
        face_sql = "SELECT id,status FROM face WHERE stu_id={} LIMIT 1"
        audio_sql = "SELECT id,status FROM audio WHERE face_id={} LIMIT 1"
        feature_sql = "SELECT id,status FROM feature WHERE face_id={}"
        mfr_sql = "SELECT count(id) FROM manufacturer LIMIT 1"
        mfr_count = pgsql_db.get(pgsql_cur, mfr_sql)[0]

        results = pgsql_db.query(pgsql_cur, stu_sql)
        for row in results:
            stu_id = row[0]

            face = pgsql_db.get(pgsql_cur, face_sql.format(str(stu_id)))
            if face:
                face_id = face[0]
                audio = pgsql_db.get(pgsql_cur, audio_sql.format(face_id))
                if not audio:
                    print "integrity audio, face_id={}".format(face_id)
                    continue
                feature_results = pgsql_db.query(pgsql_cur, feature_sql.format(face_id))
                feature_count = len(feature_results)
                if feature_count != mfr_count:
                    print "integrity feature, face_id={}".format(face_id)
                    continue
                # 逻辑性判断
                if face[1] == 4 and audio[1] == 3 and DataHandler._feature_status(4, feature_results):
                    pass
                elif face[1] == 1 and audio[1] == 3 and DataHandler._feature_status(1, feature_results):
                    pass
                elif face[1] == 2 and audio[1] == 3 and DataHandler._feature_status(2, feature_results):
                    pass
                elif face[1] == 5 and audio[1] == 3 and DataHandler._feature_status(5, feature_results):
                    pass
                elif face[1] == 6 and audio[1] == 3 and DataHandler._feature_status(6, feature_results):
                    pass
                else:
                    print "数据逻辑问题stu_id={}".format(stu_id)
            else:
                print "integrity face, stu_id={}".format(stu_id)

    def compress_under_size(self, imagefile, targetfile, targetsize):
        """压缩图片尺寸直到某一尺寸

        :param imagefile: 原图路径
        :param targetfile: 保存图片路径
        :param targetsize: 目标大小，单位byte
        """
        currentsize = os.path.getsize(imagefile)
        print currentsize
        for quality in range(99, 0, -1):  # 压缩质量递减
            if currentsize > targetsize:
                image = Image.open(imagefile)
                image = image.convert('RGB')
                image.save(targetfile, optimize=True, quality=quality)
                currentsize = os.path.getsize(targetfile)

    @db.transaction(is_commit=False)
    def png_2_jpg(self, pgsql_cur):

        pgsql_db = db.PgsqlDbUtil
        results = pgsql_db.query(pgsql_cur, "SELECT oss_url FROM feature WHERE status in (1,4)")
        for row in results:
            oss_url = row[0]
            temp_dir = project_dir + '/src/scripts/temp/'
            img_path = temp_dir + '{}'.format(str(time.time()).replace('.', ''))
            with open(img_path, 'w') as fd:
                fd.write(requests.get(oss_url).content)

            currentsize = os.path.getsize(img_path)
            if currentsize < 60 * 1024:
                continue

            time.sleep(0.1)
            # 压缩图片
            new_path = img_path + "_1.jpg"
            self.compress_under_size(img_path, new_path, 50*1024)

            time.sleep(0.1)
            oss_key = "person" + oss_url.split("person")[-1]
            print new_path
            with open(new_path, 'rb') as fileobj:
                self.bucket.put_object(oss_key, fileobj)

    @db.transaction(is_commit=False)
    def resize_image(self, pgsql_cur):
        pgsql_db = db.PgsqlDbUtil
        results = pgsql_db.query(pgsql_cur, "SELECT oss_url FROM feature WHERE status in (1,4)")
        for row in results:
            oss_url = row[0]
            # 先写入本地
            temp_dir = project_dir + '/src/scripts/temp/'
            img_path = temp_dir + '{}'.format(str(time.time()).replace('.', ''))
            with open(img_path, 'w') as fd:
                fd.write(requests.get(oss_url).content)

            # 压缩图片到
            new_path = img_path + "_1.jpg"
            img = Image.open(img_path)
            img = img.convert('RGB')
            out = img.resize((480, 640), Image.ANTIALIAS)
            out.save(new_path, 'jpeg')

            oss_key = "person" + oss_url.split("person")[-1]
            with open(new_path, 'rb') as fileobj:
                result = self.bucket.put_object(oss_key, fileobj)
                print('http status: {0}'.format(result.status))

    @db.transaction(is_commit=False)
    def stu_no_and_image_is_match(self, pgsql_cur):
        """身份证号和图片是否匹配"""
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT id,stu_no FROM student WHERE status=1"
        face_sql = "SELECT id,stu_no FROM face WHERE stu_id={}"
        feature_sql = "SELECT oss_url,status FROM feature WHERE face_id={}"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            print "---------------------------"
            stu_id = row[0]
            student_stu_no = row[1]
            face_results = pgsql_db.query(pgsql_cur, face_sql.format(stu_id))
            if len(face_results) > 1:
                print "人脸有两条记录 stu_id={}".format(stu_id)
                break
            face_id = face_results[0][0]
            face_stu_no = face_results[0][1]
            if student_stu_no != face_stu_no:
                print "student表和face表的stu_no不一致 stu_id={}".format(stu_id)
                break
            feature_results = pgsql_db.query(pgsql_cur, feature_sql.format(face_id))
            if len(feature_results) != 2:
                print "feature表记录条数不是2 stu_id={} face_id={}".format(stu_id, face_id)
                break
            if not feature_results[0][0]:
                if feature_results[0][1] != -1:
                    print "feature oss_url为空 stu_id={} face_id={}".format(stu_id, face_id)
                    break
            if not feature_results[1][0]:
                if feature_results[1][1] != -1:
                    print "feature oss_url为空 stu_id={} face_id={}".format(stu_id, face_id)
                    break
            if feature_results[0][0] and student_stu_no not in feature_results[0][0]:
                print "stu_no不在feature oss_url字段内 stu_id={} face_id={}".format(stu_id, face_id)
                break
            if feature_results[1][0] and student_stu_no not in feature_results[1][0]:
                print "stu_no不在feature oss_url字段内 stu_id={} face_id={}".format(
                    stu_id, face_id)
                break

    @db.transaction(is_commit=True)
    def copy_feature_to_face(self, pgsql_cur):
        """face的oss_url字段为空"""
        pgsql_db = db.PgsqlDbUtil
        results = pgsql_db.query(pgsql_cur, "select id from face where oss_url is null")
        for row in results:
            pk = row[0]
            oss_url = pgsql_db.get(pgsql_cur, "select oss_url from feature where face_id={} limit 1".format(pk))[0]
            if oss_url:
                d = {
                    'id': pk,
                    'oss_url': oss_url
                }
                pgsql_db.update(pgsql_cur, d, table_name='face')

    @db.transaction(is_commit=False)
    def is_exists_null_url(self, pgsql_cur):
        """url是否为空"""
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT oss_url FROM face WHERE status in (2,3,4,5,6)"
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            oss_url = row[0]
            if not self.bucket.object_exists("person" + oss_url.split('person')[-1]):
                print oss_url


if __name__ == '__main__':
    # data = DataHandler()
    # data.add_data_to_audio_feature()
    #d = FeatureHttps()
    #d.change_http()
    import sys
    d = DataHandler()
    func_name = sys.argv[1]
    getattr(d, func_name)(*sys.argv[2:])