# coding:utf-8

from .default import Config


class TestingConfig(Config):
    """
    测试环境配置数据
    """

    DEBUG = False
