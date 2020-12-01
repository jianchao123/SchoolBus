# coding:utf-8

"""
日志输出模块
"""
import logging
import threading
import json


""" 日志等级定义 """
LOG_LEVEL = {
    'debug': 0,
    'info': 1,
    'warning': 2,
    'error': 3,
    'critical': 4
}


class OutPutFileHelper(object):

    @staticmethod
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


class CLogHelper(object):
    """ 日志类 """

    def __init__(self, service_name='default'):
        """
        日志类初始化

        args:
            service_name: 服务名称
        """
        CLogHelper.logger = self
        self.local_object = threading.local()
        self.local_object.sequence_id = ''
        self.service_name = service_name
        self.log_level = 0
        super(CLogHelper, self).__init__()

    def init_app(self, app):
        """
        日志库初始化

        args:
            app: flask app对象
        """
        self.service_name = app.config.get('APP_SERVICE_NAME', '')
        self.log_level = LOG_LEVEL[app.config['APP_LOG_LEVEL']]

    @property
    def sequence_id(self):
        """
        获取当前记录处理的sequence_id

        return:
            str.
        """
        return self.local_object.sequence_id

    @sequence_id.setter
    def sequence_id(self, seq_id):
        """
        设置当前记录处理的sequence_id

        args:
            seq_id: 当前sequence_id
        """
        self.local_object.sequence_id = seq_id

    def _make_log(self, msg, level):
        """
        构造日志输出记录对象

        args:
            msg: 日志信息
            level: 日志等级

        return:
            dict.
        """
        if not hasattr(self.local_object, 'sequence_id'):
            self.local_object.sequence_id = ''

        return {
            'topic': level,
            'serviceName': self.service_name,
            'content': msg,
            'sequenceId': self.sequence_id
        }

    def log(self, msg):
        """
        记录日志

        args:
            msg: 日志文本
        """
        from ext import conf
        print msg
        log_obj = OutPutFileHelper.get_logger(conf.config["LOG_PATH"])
        log_obj.error(msg)

    def debug(self, msg):
        """
        输出debug日志

        args:
            msg: 日志文本
        """
        level = 'debug'
        if self.log_level > LOG_LEVEL[level]:
            return

        log = self._make_log(msg, level)
        self.log(json.dumps(log))

    def info(self, msg):
        """
        输出info日志

        args:
            msg: 日志文本
        """
        level = 'info'
        if self.log_level > LOG_LEVEL[level]:
            return

        log = self._make_log(msg, level)
        self.log(json.dumps(log))

    def warning(self, msg):
        """
        输出warning日志

        args:
            msg: 日志文本
        """
        level = 'warning'
        if self.log_level > LOG_LEVEL[level]:
            return

        log = self._make_log(msg, level)
        self.log(json.dumps(log))

    def error(self, msg):
        """
        输出error日志

        args:
            msg: 日志文本
        """
        level = 'error'
        if self.log_level > LOG_LEVEL[level]:
            return

        # log = self._make_log(msg, level)
        self.log(msg)

    def critical(self, msg):
        """
        输出critical日志

        args:
            msg: 日志文本
        """
        level = 'critical'
        if self.log_level > LOG_LEVEL[level]:
            return

        log = self._make_log(msg, level)
        self.log(json.dumps(log))
