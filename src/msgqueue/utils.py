# coding: utf-8
import os
import xlwt
import xlrd
import oss2
import zipfile
from xlutils.copy import copy
import logging
import config


def get_logger(log_path):
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def create_new_workbook():
    workbook = xlwt.Workbook()  # 新建一个工作簿
    return workbook


def write_excel_xls(workbook, path, sheet_name, value):
    index = len(value)  # 获取需要写入数据的行数
    sheet = workbook.add_sheet(sheet_name)  # 在工作簿中新建一个表格
    for i in range(0, index):
        for j in range(0, len(value[i])):
            sheet.write(i, j, value[i][j])  # 像表格中写入数据（对应的行和列）
    workbook.save(path)  # 保存工作簿
    return sheet


def write_excel_xls_append(path, value, sheet_index):
    index = len(value)  # 获取需要写入数据的行数
    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[sheet_index])  # 获取工作簿中所有表格中的的第一个表格
    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    new_workbook = copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(sheet_index)  # 获取转化后工作簿中的第一个表格
    for i in range(0, index):
        for j in range(0, len(value[i])):
            new_worksheet.write(i + rows_old, j,
                                value[i][j])  # 追加写入数据，注意是从i+rows_old行开始写入
    new_workbook.save(path)  # 保存工作簿


def zip_dir(dir_path, out_full_name):
    """
    压缩指定文件夹
    :param dir_path: 目标文件夹路径
    :param out_full_name: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(out_full_name, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dir_path):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dir_path, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename),
                      os.path.join(fpath, filename))
    zip.close()


def delete_oss_file(files):
    """删除oss文件"""
    auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
    bucket = oss2.Bucket(auth, config.OSSEndpoint, config.OSSBucketName)
    return bucket.batch_delete_objects(files)


def upload_zip(oss_key, local_path):
    """上传zip到oss"""
    auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
    bucket = oss2.Bucket(auth, config.OSSEndpoint, config.OSSBucketName)
    with open(local_path, 'rb') as file_obj:
        bucket.put_object(oss_key, file_obj)


def safe_unicode(obj, * args):
    """ return the unicode representation of obj """
    try:
        return unicode(obj, * args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return unicode(ascii_text)


def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')


def oss_file_exists(oss_key):
    """文件是否存在"""
    auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
    bucket = oss2.Bucket(auth, config.OSSEndpoint, config.OSSBucketName)
    return bucket.object_exists(oss_key)


project_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))))


def aip_word_to_audio(text, oss_key):
    """文字转语音"""

    import os
    import time
    from aip import AipSpeech
    auth = oss2.Auth(config.OSSAccessKeyId, config.OSSAccessKeySecret)
    bucket = oss2.Bucket(auth, config.OSSEndpoint, config.OSSBucketName)
    aip_client = AipSpeech(config.BAIDU_APP_ID, config.BAIDU_API_KEY,
                           config.BAIDU_SECRET_KEY)

    result = aip_client.synthesis(text, 'zh', 1, {
        'vol': 5,
    })
    temp_dir = project_dir + '/src/msgqueue/temp/'

    aac_path = temp_dir + '{}.aac'.format(int(time.time()))
    if not isinstance(result, dict):
        mp3_path = temp_dir + str(int(time.time())) + '.mp3'

        with open(mp3_path, 'wb') as f:
            f.write(result)
        os.system('ffmpeg -i {} -codec:a aac -b:a 32k {}'
                  ''.format(mp3_path, aac_path))
        with open(aac_path, 'rb') as f:
            bucket.put_object(oss_key, f)
        os.remove(mp3_path)
        os.remove(aac_path)
        return True
    else:
        print result
    return False


def zip_name_list(zip_url, local_path):
    import requests
    import time
    print zip_url
    res = requests.get(zip_url)

    temp_file = \
        local_path + '/src/msgqueue/temp/' + str(int(time.time())) + '.zip'
    print temp_file
    with open(temp_file, 'wb') as fd:
        fd.write(res.content)
    zip = zipfile.ZipFile(temp_file, 'r')
    return zip.namelist()


if __name__ == "__main__":
    print zip_name_list("https://cdbus-pro.oss-cn-shanghai.aliyuncs.com/facezip/%E7%89%A9%E6%B5%81%E4%B8%AD%E5%BF%83%E4%B9%98%E8%BD%A6%E4%BA%BA%E5%91%98%E7%85%A7%E7%89%87.zip")