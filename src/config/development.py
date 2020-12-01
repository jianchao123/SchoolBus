# coding:utf-8

from config.default import Config


class DevelopmentConfig(Config):
    """
    开发环境配置数据
    """

    # Flask config
    DEBUG = True

    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = \
        'postgresql://postgres:kIhHAWexFy7pU8qM@127.0.0.1/postgres'
    LOG_PATH = '/home/jianchao/code/transport/logs/main'

    # 阿里云OSS
    OSS_BUCKET = "bus-dev"
    OSS_REGION = "oss-cn-shanghai"
    OSS_POINT = "oss-cn-shanghai.aliyuncs.com"
    OSS_ALL_KEY = "LTAIWE5CGeOiozf7"
    OSS_ALL_SECRET = "IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj"

