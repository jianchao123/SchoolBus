# coding:utf-8
import json
from utils import defines
from ext import cache


class IndexService(object):

    @staticmethod
    def index_list():
        results = cache.get(defines.RedisKey.STATISTICS)
        return json.loads(results)