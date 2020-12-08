# coding:utf-8


class RedisKey(object):

    # 注册模式相关
    DEVICE_USED = "DEVICE_USED_HASH"

    # 设备版本相关
    APPOINT_VERSION_NO = 232
    UPGRADE_JSON = {'url': 'https://img.pinganxiaoche.com/apps/1600666302.yaffs2', 'crc': -282402801, 'cmd': 'update', 'version': 232, 'size': 4756736}

    # 当前设备返回的人员信息是在做什么操作(1更新 2查询设备上人员)
    QUERY_DEVICE_PEOPLE = "QUERY_DEVICE_PEOPLE"

    # 订单ID递增
    ORDER_ID_INCR = "ORDER_ID_INCR"

    # 学生上车栈
    STUDENT_STACK = 'STUDENT_STACK'

    # 每个设备当前时间戳
    DEVICE_CUR_TIMESTAMP = 'DEVICE_CUR_TIMESTAMP_HASH'

    # 设备当前状态
    DEVICE_CUR_STATUS = "DEVICE_CUR_STATUS_HASH"

    # 生成特征码的设备集合
    GENERATE_DEVICE_NAMES = "GENERATE_DEVICE_NAMES_HASH"

    # ACC关闭HASH
    ACC_CLOSE = "ACC_CLOSE_HASH"


grade = [u'小班', u'中班', u'大班', u'学前班', u'一年级', u'二年级', u'三年级',
         u'四年级', u'五年级', u'六年级']
classes = [u'一班', u'二班', u'三班', u'四班', u'五班', u'六班',
           u'七班', u'八班', u'九班', u'十班']