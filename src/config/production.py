# coding:utf-8

from .default import Config


class ProductionConfig(Config):
    """
    产品环境配置数据
    """
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = ''
    LOG_PATH = ''
