# coding:utf-8

from .default import Config


class ProductionConfig(Config):
    """
    产品环境配置数据
    """
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:kIhHAWexFy7pU8qM@127.0.0.1/postgres'
    LOG_PATH = '/home/jianchao/code/transport/logs/main'

    # https://cdbus-dev.oss-cn-shanghai.aliyuncs.com/snap_77_1608629051.jpg
    # 阿里云OSS
    OSS_BUCKET = "cdbus-pro"
    OSS_REGION = "oss-cn-shanghai"
    OSS_POINT = "oss-cn-shanghai.aliyuncs.com"
    OSS_ALL_KEY = "LTAIWE5CGeOiozf7"
    OSS_ALL_SECRET = "IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj"

    # 微信公众号
    MP_ID = 'gh_949a03d359ca'
    MP_APP_ID = 'wxfe59baf99b8ff1d4'
    MP_APP_SECRET = 'bf3e50ed4b549fc007d5ad39634cdc4d'
    MP_TOKEN = 'gK9gY3cV2bM6pH9gF7vJ5uC8vN9cI0cL'
    MP_ENCODING_AES_KEY = 'CAmGrrm1rJ0HqgcbIBQbhKAHLUKGGbv3RJTTFnixTaC'
    MP_AUTH_URI = 'http://cdmp.wgxing.com/static/getOpenid.html'

    # 实时刷脸图片 format
    REALTIME_FACE_IMG = 'http://' + OSS_BUCKET + '.' + \
                        OSS_POINT + '/snap_{fid}_{timestamp}.jpg'
