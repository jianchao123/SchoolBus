# coding:utf-8
from timer.utils import get_location


def get_location_by_gps(longitude, latitude):
    """用户请求的时候调用"""
    get_location(longitude, latitude)
    # TODO