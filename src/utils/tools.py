# coding:utf-8
import re
import json
import decimal
import hashlib
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
