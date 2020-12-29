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
    STUDENT_NOT_FOUND_PARENTS_MOBILE = (200031, u"不是家长或工作人员,无法绑定")
    STUDENT_NOT_PARENTS = (200032, u"您不是家长")

    WORKER_EMP_NO_ALREADY_EXISTS = (200040, u"工号已经存在")
    WORKER_ALREADY_EXISTS_DUTY = (200041, u"该车辆已经存在该职务的工作人员")
    WORKER_NO_CHANGE_DUTY = (200042, u"工作人员已绑车辆,不能修改职务,需先解绑")
    WORKER_ALREADY_BOUNDING_CAR = (200043, u"工作人员已经绑定了A车辆,需要先将A车辆的工作员位置填补后才能删除这个工作员")

    CAR_NOT_FOUND = (200050, u"车辆未找到")
    CAR_CHEPAI_ALREADY_EXISTS = (200051, u"车牌已经存在")
    CAR_BOUNDING_TO_STUDENT = (200052, u"车辆已经绑定了学生,不能删除,请先解除学生对车辆的绑定")
    CAR_BOUNDING_TO_DEVICE = (200053, u"车辆已经绑定了设备,不能删除,请先解除设备对车辆的绑定")
    CAR_BOUNDING_TO_WORKER = (200054, u"车辆已经绑定了工作人员,请先解除工作人员对车辆的绑定")
    CAR_ALREADY_BOUNDING_WORKER = (200055, u"车辆已经绑定工作人员")

    SCHOOL_NAME_ALREADY_EXISTS = (200060, u"学校名字已经存在")

    DEVICE_INITED_NOT_CHANGE = (200070, u"初始化已完成,不能再修改设备类型")
    DEVICE_CHEPAI_NOT_FOUND = (200071, u"需要先在车辆列表修改车牌")
    DEVICE_FIRST_BOUNDING_WORKER = (200072, u"需要先绑定工作人员")
    DEVICE_PLEASE_WAITING = (200073, u"请等待")
    DEVICE_UNINITIALIZED_ERR = (200074, u"设备未初始化")
    DEVICE_ALREADY_CLOSE = (200075, u"设备已经关闭")
    DEVICE_OPEN_THREE_MINUTES_LATER = (200076, u"开机三分钟后才能执行该功能")
    DEVICE_CAR_ALREADY_BINDING = (200077, u"车辆已经绑定设备")

    TASK_EXECUTING = (200071, u"任务执行中")


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


grade = [u"TBD", u'小班', u'中班', u'大班', u'学前班', u'一年级', u'二年级', u'三年级',
         u'四年级', u'五年级', u'六年级']
classes = [u"TBD", u'一班', u'二班', u'三班', u'四班', u'五班', u'六班',
           u'七班', u'八班', u'九班', u'十班']
gender = [u"TBD", u'男', u'女']
duty = [u"TBD", u'驾驶员', u'照管员']