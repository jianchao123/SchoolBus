# coding:utf-8


class Config(object):
    """
    默认配置数据
    """

    # Flask config
    DEBUG = False
    TESTING = False
    SECRET_KEY = '‭1DF5E76‬'

    # Mysql
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_POOL_RECYCLE = 360
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_RECORD_QUERIES = False

    # Redis
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = '6379'
    REDIS_PASSWORD = ''
    REDIS_DB = 0

    # OSS config
    OSS_BUCKET = ""
    OSS_REGION = ""
    OSS_POINT = ""
    OSS_ALL_KEY = ""
    OSS_ALL_SECRET = ""

    # encrypt
    SALT = "LFLgi9VU"

    APP_LOG_LEVEL = 'info'

