# coding:utf-8


class GlobalErrorCode(object):
    """全局错误码"""
    PARAM_ERROR = (1, u"参数错误")
    BUSINESS_ERROR = (2, u"逻辑错误")
    JSON_PARSE_ERROR = (3, u"json解析错误")
    OBJ_NOT_FOUND_ERROR = (4, u"对象找不到")
    REQUIRE_TOKEN_ERR = (5, u"需要TOKEN")
    INVALID_TOKEN_ERR = (6, u'无效的token值')
    REQUIRE_JSON_FORMAT_ERR = (7, u'需要json格式的请求体')
    PARAMS_DESERIALIZE_ERR = (8, u'参数json反序列化错误')
    MISSING_PARAM_ERR = (9, u'缺少参数 {}')
    PARAMETER_BETWEEN_ERR = (10, u'参数 page={} 取值错误, 范围 >=1')
    PARAMETER_STATUS_AND_EXPECT_ERR = (11, u'参数 status={} 取值错误, 预期值{}')
    PARAMETER_KEY_ERR = (12, u'参数{}不是{}.')
    SYSTEM_ERR = (12, u"系统错误")
    NO_PERMISSION = (13, u"没有权限")
    INVALID_PK_ERR = (14, u"无效Pk")
    DB_COMMIT_ERR = (15, u"提交错误")
    UNKNOWN_ERR = (999, u'未知错误')
    GUEST_USER_ERR = (16, u"GUEST帐号不能操作模块")


class SubErrorCode(object):
    """局部错误码"""

    USER_REQUIRE_TOKEN_ERR = (200001, u"需要TOKEN")
    USER_INVALID_TOKEN_ERR = (200002, u'无效的token值')
    USER_PWD_ERR = (200009, u"密码错误")
    USER_PWD_LEN_ERR = (200010, u"用户密码错误")

    ORDER_NUMBER_TOO_BIG = (200020, u"订单条数太大")
    ORDER_EXPORTING = (200021, u"订单导出中")

    STUDENT_ID_CARD_ALREADY_EXISTS = (200030, u"学生身份证号已经存在")


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

    # 学生上车集合
    STUDENT_SET = 'STUDENT_SET:{}'

    # 每个设备当前时间戳
    DEVICE_CUR_TIMESTAMP = 'DEVICE_CUR_TIMESTAMP_HASH'

    # 设备当前状态
    DEVICE_CUR_STATUS = "DEVICE_CUR_STATUS_HASH"

    # 生成特征码的设备集合
    GENERATE_DEVICE_NAMES = "GENERATE_DEVICE_NAMES_HASH"

    # ACC关闭HASH
    ACC_CLOSE = "ACC_CLOSE_HASH"

    # 设备当前车上人数
    DEVICE_CUR_PEOPLE_NUMBER = "DEVICE_CUR_PEOPLE_NUMBER_HASH"

    # 上传人脸zip的时间戳
    UPLOAD_ZIP_TIMESTAMP = "UPLOAD_ZIP_TIMESTAMP"

    # OSS上所有的人脸
    OSS_ID_CARD_SET = "OSS_ID_CARD_SET"


grade = [u'小班', u'中班', u'大班', u'学前班', u'一年级', u'二年级', u'三年级',
         u'四年级', u'五年级', u'六年级']
classes = [u'一班', u'二班', u'三班', u'四班', u'五班', u'六班',
           u'七班', u'八班', u'九班', u'十班']
gender = [u'男', u'女']