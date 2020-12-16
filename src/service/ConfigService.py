# coding:utf-8
from ext import conf


class ConfigService(object):
    """配置"""

    @staticmethod
    def config_list():
        """配置列表"""
        print dir(conf)
        data = {
            'oss': {
                'oss_key': conf.config['OSS_ALL_KEY'],
                'oss_secret': conf.config['OSS_ALL_SECRET'],
                'oss_bucket': conf.config['OSS_BUCKET'],
                'oss_region': conf.config['OSS_REGION']
            }
        }
        return data
