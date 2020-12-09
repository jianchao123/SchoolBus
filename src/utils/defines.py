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