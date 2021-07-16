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


class DataHandler(object):

    @db.transaction(is_commit=True)
    def new_mfr(self, pgsql_cur):
        """新厂商添加新数据"""
        pass

    @db.transaction(is_commit=True)
    def add_data_to_audio_feature(self, pgsql_cur):
        """添加数据到audio feature
        只能用于武汉的设备
        """
        pgsql_db = db.PgsqlDbUtil
        sql = "SELECT id FROM manufacturer WHERE status=1"
        mfr_list = []
        results = pgsql_db.query(pgsql_cur, sql)
        for row in results:
            mfr_list.append(row[0])

        face_sql = "SELECT id,oss_url,feature,feature_crc," \
                   "status,aac_url,nickname,stu_no " \
                   "FROM face WHERE status != 10"
        query_audio_sql = "SELECT id FROM audio WHERE face_id={} LIMIT 1"
        query_feature_sql = "SELECT id FROM feature " \
                            "WHERE face_id={} and mfr_id={} LIMIT 1"
        face_set = pgsql_db.query(pgsql_cur, face_sql)
        for face_row in face_set:
            face_id = face_row[0]
            oss_url = face_row[1]
            feature = face_row[2]
            feature_crc = face_row[3]
            face_status = face_row[4]
            aac_url = face_row[5]
            nickname = face_row[6]
            stu_no = face_row[7]

            audio_row = pgsql_db.get(pgsql_cur, query_audio_sql.format(face_id))
            # 不存在
            if not audio_row:
                # audio
                a_d = {
                    'aac_url': aac_url,
                    'nickname': nickname,
                    'stu_no': stu_no,
                    'status': 3,
                    'face_id': face_id
                }
                pgsql_db.insert(pgsql_cur, a_d, table_name='audio')

            # feature
            for mfr_id in mfr_list:
                # 是否存在
                feature_row = pgsql_db.get(
                    pgsql_cur, query_feature_sql.format(face_id, mfr_id))
                if not feature_row:
                    d = {
                        'mfr_id': mfr_id,
                        'face_id': face_id
                    }
                    if face_status == 1:
                        d['status'] = -1
                    else:
                        if face_status == 2:
                            d['status'] = 1
                        if face_status == 3:
                            d['status'] = 2
                        if face_status == 4:
                            d['status'] = 3
                        if face_status == 5:
                            d['status'] = 4
                        if face_status == 6:
                            d['status'] = 3
                        d['oss_url'] = oss_url if oss_url else 'null'
                        d['feature'] = feature if feature else 'null'
                        d['feature_crc'] = feature_crc if feature_crc else 'null'
                    pgsql_db.insert(pgsql_cur, d, table_name='feature')


if __name__ == '__main__':
    data = DataHandler()
    data.add_data_to_audio_feature()