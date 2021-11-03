# coding:utf-8
import re
import os
import oss2
import json
import xlwt
import xlrd
import decimal
import hashlib
import inspect
import zipfile
from xlutils.copy import copy
from app import app


def is_chinese(self, string):
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return True


def md5_encrypt(pwd):
    """md5加密"""
    pwd = pwd + app.config['SALT']
    m = hashlib.md5(pwd.encode('utf-8'))
    return m.hexdigest().upper()


def gen_token(password, key, expire):
    """生成token"""
    from itsdangerous import TimedJSONWebSignatureSerializer

    token = TimedJSONWebSignatureSerializer(
        secret_key=key,
        expires_in=expire
    )
    return token.dumps({'password': password})


def mobile_verify(mobile):
    """手机号验证"""
    rgx = '13[0,1,2,3,4,5,6,7,8,9]|15[0,1,2,7,8,9,5,6,3]|18[0,1,9,5,6,3,4,2,7,8]|17[6,7]|147\d{8}'
    pattern = re.compile(rgx)
    a = pattern.match(str(mobile))
    if a:
        return True
    return False


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        super(DecimalEncoder, self).default(o)


def longitude_format(longitude):
    pattern = re.compile(r"\d{3}\.\d{6,}")
    return pattern.match(longitude)


def latitude_format(latitude):
    pattern = re.compile(r"\d{2}\.\d{6,}")
    return pattern.match(latitude)


def get_frame_name_param(frame, is_file=False):
    args, _, _, values = inspect.getargvalues(frame)

    func_name = inspect.getframeinfo(frame)[2]
    if is_file:
        return func_name, 'bulk add'
    else:

        func_param_list = []

        for i in args:
            func_param_list.append("%s=%s" % (i, values[i]))
        return func_name, ",".join(func_param_list)


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


def xlsx_names(file_dir):
    xlsx_list = []
    for root, dirs, files in os.walk(file_dir):
        for f in files:
            if os.path.splitext(f)[1] == '.xlsx':
                xlsx_list.append(os.path.join(root, f))
        return xlsx_list


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


def delete_oss_file(files, akid, aks, endpoint, bucketname):
    """删除oss文件"""
    auth = oss2.Auth(akid, aks)
    bucket = oss2.Bucket(auth, endpoint, bucketname)
    return bucket.batch_delete_objects(files)


def upload_zip(oss_key, local_path, akid, aks, endpoint, bucketname):
    """上传zip到oss"""
    auth = oss2.Auth(akid, aks)
    bucket = oss2.Bucket(auth, endpoint, bucketname)
    with open(local_path, 'rb') as file_obj:
        bucket.put_object(oss_key, file_obj)