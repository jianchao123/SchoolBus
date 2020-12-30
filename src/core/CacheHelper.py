# coding=utf-8

from redis import StrictRedis as Redis


class CCacheHelper(Redis):

    def __init__(self):
        """
        缓存类初始化
        """
        self.host = 'localhost'
        self.port = 6379
        self.password = ''
        self.db = 0

    def init_app(self, app):
        self.host = app.config['REDIS_HOST']
        self.port = app.config['REDIS_PORT']
        self.password = app.config['REDIS_PASSWORD']
        self.db = app.config['REDIS_DB']

        if self.password == '':
            super(CCacheHelper, self).__init__(
                self.host, self.port, self.db, decode_responses=True)
        else:
            super(CCacheHelper, self).__init__(
                self.host, self.port, self.db, password=self.password,
                decode_responses=True)