# coding:utf-8
from utils import defines
from ext import cache


class IndexService(object):

    @staticmethod
    def index_list():
        results = cache.hgetall(defines.RedisKey.STATISTICS)
        d = {}
        for k, v in results:
            d[k] = v
        return d