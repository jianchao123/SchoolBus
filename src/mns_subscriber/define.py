# coding:utf-8


class RedisKey(object):
    # 注册模式相关
    DEVICE_USED = "DEVICE_USED_HASH"

    # 设备版本相关
    WUHAN_VERSION_NO = 264
    SHENZHEN_VERSION_NO = 276
    # UPGRADE_JSON = {"url": "https://img.pinganxiaoche.com/apps/1608795066.yaffs2",
    #                 "crc": -2090701703, "cmd": "update",
    #                 "version": 250, "size": 4843776}
    WUHAN_UPGRADE_JSON = {
        "url": "https://img.pinganxiaoche.com/apps/1624332193.yaffs2",
        "crc": 981940787, "cmd": "update", "version": 264, "size": 4893824}
    SHENZHEN_UPGRADE_JSON = {
        "url": "http://cdbus-pro.oss-cn-shanghai.aliyuncs.com/upgradepkt/276.tar.gz",
        "crc": 1208900159, "cmd": "update", "version": 276, "size": 4893824}

    # 当前设备返回的人员信息是在做什么操作(1更新 2查询设备上人员)
    QUERY_DEVICE_PEOPLE = "QUERY_DEVICE_PEOPLE"

    # 订单ID递增
    ORDER_ID_INCR = "ORDER_ID_INCR"

    # 学生上车集合{device_name}
    STUDENT_SET = 'STUDENT_SET:{}'

    # 每个设备当前时间戳
    DEVICE_CUR_TIMESTAMP = 'DEVICE_CUR_TIMESTAMP_HASH'

    # 设备当前状态
    DEVICE_CUR_STATUS = "DEVICE_CUR_STATUS_HASH"

    # 生成特征码的设备集合(设备名字)
    GENERATE_DEVICE_NAMES = "GENERATE_DEVICE_NAMES_SET"

    # ACC关闭HASH
    ACC_CLOSE = "ACC_CLOSE_HASH"

    # ACC开启
    ACC_OPEN_TIME = "ACC_OPEN_TIME_HASH"

    # 设备当前车上人数
    DEVICE_CUR_PEOPLE_NUMBER = "DEVICE_CUR_PEOPLE_NUMBER_HASH"

    # 上传人脸zip的时间戳
    UPLOAD_ZIP_TIMESTAMP = "UPLOAD_ZIP_TIMESTAMP"

    # OSS上所有的人脸
    OSS_ID_CARD_SET = "OSS_ID_CARD_SET"

    # 统计
    STATISTICS = "STATISTICS"

    # 微信access_token
    WECHAT_ACCESS_TOKEN = "WECHAT_ACCESS_TOKEN"

    # 设备当前gps
    DEVICE_CUR_GPS = "DEVICE_CUR_GPS_HASH"

    # 缓存车辆数据
    CACHE_CAR_DATA = "CACHE_CAR_DATA_HASH"

    # 工作人员数据
    CACHE_STAFF_DATA = "CACHE_STAFF_DATA_HASH"

    # 学校名字
    CACHE_SCHOOL_NAME_DATA = "CACHE_SCHOOL_NAME_DATA_HASH"

    # 去重key
    REMOVE_DUP_ORDER_SET = "REMOVE_DUP_ORDER_KEY"

    # 厂商生成二维码的设备
    MFR_GENERATE_DEVICE_HASH = "MFR_GENERATE_DEVICE_HASH"

    # 厂商设备分类
    MFR_DEVICE_HASH = "MFR_DEVICE_HASH"

    # 监控中心key
    SC_ORDER_LIST = "SC_ORDER_LIST"

    SC_ALARM_LIST = "SC_ALARM_LIST"

    ALL_HEARTBEAT_HASH = "ALL_HEARTBEAT_HASH"

    @staticmethod
    def get_device_mfr_name(rds_conn, device_name):
        mfr_name = rds_conn.hget(RedisKey.MFR_DEVICE_HASH, device_name)
        if not mfr_name:
            return "WUHAN"
        return mfr_name

grade = [u"TBD", u'小班', u'中班', u'大班', u'学前班', u'一年级', u'二年级', u'三年级',
         u'四年级', u'五年级', u'六年级']
classes = [u"TBD", u'一班', u'二班', u'三班', u'四班', u'五班', u'六班',
           u'七班', u'八班', u'九班', u'十班']
gender = [u"TBD", u'男', u'女']
duty = [u"TBD", u'驾驶员', u'照管员']