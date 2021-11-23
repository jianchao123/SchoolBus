# coding:utf-8

from config.default import Config


class DevelopmentConfig(Config):
    """
    开发环境配置数据
    """

    # Flask config
    DEBUG = True

    # PostgreSQL
    #SQLALCHEMY_DATABASE_URI = 'mysql://root:kIhHAWexFy7pU8qM@127.0.0.1/transport?charset=utf8mb4'
    #SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:kIhHAWexFy7pU8qM@cdmp.wgxing.com/postgres'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:kIhHAWexFy7pU8qM@127.0.0.1/postgres'
    LOG_PATH = '/home/jianchao/code/transport/logs/main'

    # https://cdbus-dev.oss-cn-shanghai.aliyuncs.com/snap_77_1608629051.jpg
    # 阿里云OSS
    OSS_BUCKET = "cdbus-dev"
    OSS_REGION = "oss-cn-shanghai"
    OSS_POINT = "oss-cn-shanghai.aliyuncs.com"
    OSS_ALL_KEY = "LTAI5tHYr3CZ59HCRLEocbDG"
    OSS_ALL_SECRET = "BMRI8WzUVMRbS6LHPM3bIiadWIPE8c"

    # 微信公众号
    # MP_ID = 'gh_4af7ffea23bf'
    # MP_APP_ID = 'wxc4a0aec4b79dd568'
    # MP_APP_SECRET = '786b35eb993cec74a73e423f61cd3c63'
    # MP_TOKEN = '5Yt1r5XfFMs8ncVTIOWGQNNPW3PLnTZz'
    # MP_ENCODING_AES_KEY = 'HHPL5pzFm1AqUlUk3M25LsyuoYfgfIBi1dHcPQQmme6'
    MP_ID = 'gh_949a03d359ca'
    MP_APP_ID = 'wxfe59baf99b8ff1d4'
    MP_APP_SECRET = 'bf3e50ed4b549fc007d5ad39634cdc4d'
    MP_TOKEN = 'gK9gY3cV2bM6pH9gF7vJ5uC8vN9cI0cL'
    MP_ENCODING_AES_KEY = 'CAmGrrm1rJ0HqgcbIBQbhKAHLUKGGbv3RJTTFnixTaC'
    MP_AUTH_URI = 'http://cdmpdev.wgxing.com/static/getOpenid.html' # wechat redirect_uri,可用于本地测试,微信的bug
    #MP_AUTH_URI = 'http://cdmp.wgxing.com/static/getOpenid.html'  # wechat redirect_uri,可用于本地测试,微信的bug

    # 实时刷脸图片 format
    REALTIME_FACE_IMG = 'http://' + OSS_BUCKET + '.' + OSS_POINT + \
                        '/snap_{fid}_{timestamp}.jpg'