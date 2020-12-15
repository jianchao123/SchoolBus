# coding:utf-8
import re
from functools import wraps
from flask import request, jsonify, g

from utils.defines import GlobalErrorCode
from ext import log
from AppError import *


def make_error_resp(error_code, error_msg):
    """
    构造错误返回值

    args:
        error_code: 错误码
        error_msg: 错误信息

    return:
        字典.
    """
    return make_resp({}, error_code, error_msg)


def make_correct_resp(data={}):
    """
    构造正确返回值

    args:
        data: 返回数据

    return:
        字典.
    """
    return make_resp(data, 0, '')


def make_resp(data, status, msg):
    """
    构造返回值

    args:
        data: 返回数据
        status: 错误码
        msg: 错误信息

    return:
        字典.
    """
    return {
        'data': data,
        'status': status,
        'msg': msg
    }


def is_argument_exists(req_args, args_name):
    """
    判断参数是否存在.

    args:
        req_args: 请求参数字典
        args_name: 必需的参数名称列表

    return:
        None. 所有参数都存在
        string. 不存在的参数名
    """
    for arg_name in args_name:
        if arg_name not in req_args:
            return arg_name
    return None


def parse_post_args(request):
    """
    解析post请求的json参数体

    args:
        request: flask.request实体

    return:
        解析得到的参数字典. 可为None.

    exception:
        ApiArgsError.
    """
    if not request.is_json:
        raise ApiArgsError(*GlobalErrorCode.REQUIRE_JSON_FORMAT_ERR)

    try:
        req_args = request.get_json()
        return req_args
    except:
        raise ApiArgsError(*GlobalErrorCode.PARAMS_DESERIALIZE_ERR)


def missing_parameter(err_tuple, *args):
    return err_tuple[0], err_tuple[1].format(",".join(args))


def post_check_args(request, args_name):
    """
    校验POST请求中的参数. args_name长度为0时不解析参数, 返回None.

    args:
        request: flask.request实体
        args_name: 参数名称列表，例如['name', 'password']

    return:
        解析得到的参数字典. 可为None.

    exception:
        ApiArgsError.
    """

    req_args = parse_post_args(request)

    non_exists_name = is_argument_exists(req_args, args_name)
    if non_exists_name:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.MISSING_PARAM_ERR, non_exists_name))
    return req_args


def get_check_args(request, args_name):
    """
    校验GET请求中的参数. args_name长度为0时不解析参数, 返回None.

    args:
        request: flask.request实体
        args_name: 参数名称列表，例如['name', 'password']

    return:
        解析得到的参数字典. 可为None.

    exception:
        ApiArgsError.
    """

    req_args = request.values
    non_exists_name = is_argument_exists(req_args, args_name)
    if non_exists_name:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.MISSING_PARAM_ERR, non_exists_name))
    return req_args


def format_exception(ex):
    """
    格式化异常的具体信息

    args:
        ex: 异常对象

    return:
        str.

    exception:
        不抛出异常.
    """
    try:
        import traceback
        import sys
        from StringIO import StringIO

        exc_type, exc_value, exc_trackback = sys.exc_info()
        fp = StringIO()
        traceback.print_exception(exc_type, exc_value, exc_trackback, file=fp)
        stacks = fp.getvalue()
        fp.close()

        return '{}'.format(stacks)
    except:
        return '{}'.format(ex)


def post_require_check(args_name):
    """
    decorator.
    用于校验POST请求中的参数是否存在. 参数在http body中, json字符串.
    """

    def post_require_check_wrapper(fn):
        """
        包装函数.
        校验POST请求中的参数, 通过则用调用fn. 否则抛出AppErrorBase异常.
        """

        @wraps(fn)
        def __wrapper(**arg):
            try:
                args = None
                if len(args_name):
                    args = post_check_args(request, args_name)
                r = fn(args, **arg)
                return jsonify(make_correct_resp(r))
            except AppErrorBase as ex:
                log.error((str(ex.error_code) + " " + ex.error_msg))
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                import traceback
                print traceback.format_exc()
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))

        return __wrapper

    return post_require_check_wrapper


def get_require_check(args_name):
    """
    decorator.
    用于校验GET请求中的参数是否存在. 参数在http url中.
    """

    def get_require_check_wrapper(fn):
        """
        包装函数.
        校验GET请求中的参数, 通过则用调用fn. 否则抛出AppErrorBase异常.
        """

        @wraps(fn)
        def __wrapper(**arg):
            try:
                args = None
                if len(args_name):
                    args = get_check_args(request, args_name)
                r = fn(args, **arg)
                return jsonify(make_correct_resp(r))
            except AppErrorBase as ex:
                log.error(str(ex))
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                log.critical('[未知错误]{}'.format(format_exception(ex)))
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))

        return __wrapper

    return get_require_check_wrapper


def format_resp_time(time_str):
    """
    将数据库中时间字段格式化为返回所需
    YYYY-MM-DD HH:MM:SS -> MM-DD HH:MM

    args:
        time_str: 需格式化的时间, YYYY-MM-DD HH:MM:SS

    return:
        MM-DD HH:MM
    """
    try:
        return str(time_str)[5:16]
    except Exception as ex:
        log.critical('[未知错误]{}'.format(format_exception(ex)))
        return time_str


def parse_page_size_arg(args):
    """
    解析page和size参数.

    args:
        args.page: 页码
        args.size: 数量

    return:
        (page, size)

    exception:
        ApiArgsError.
    """
    page = parse_type_arg(args, 'page', int)
    if page < 1:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.PARAMETER_BETWEEN_ERR, page))

    size = parse_type_arg(args, 'size', int)
    if size < 1:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.PARAMETER_BETWEEN_ERR, page))

    return page, size


def parse_status_arg(args, expect):
    """
    解析status 参数.

    args:
        args.status: 状态值
        expect: 预期范围

    return:
        status

    exception:
        ApiArgsError.
    """
    status = parse_type_arg(args, 'status', int)
    if status not in expect:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.PARAMETER_STATUS_AND_EXPECT_ERR, status, expect))

    return status


def parse_type_arg(args, key, t):
    """
    解析args中的key参数.

    args:
        args: 参数字典
        key: 参数名
        t: 参数类型

    return:
        t类型的值.

    exception:
        ApiArgsError.
    """
    try:
        v = t(args[key])
        return v
    except ValueError as ex:
        raise ApiArgsError(*missing_parameter(
            GlobalErrorCode.PARAMETER_KEY_ERR, key, t))


def second():
    """
    获取当前秒数
    """
    import time
    return int(time.time())


def require_token_check(req, g):
    """
    校验用户token

    args:
        req: flask.request实体
        g: flask.g 实体

    return:
        userId.

    exception:
        ApiArgsError.
    """
    from service.UserProfileService import UserProfileService

    if 'token' not in req.headers:
        raise ApiArgsError(*GlobalErrorCode.REQUIRE_TOKEN_ERR)

    token = req.headers.get('token')
    g.user_id = UserProfileService.token_to_id(token)
    if UserProfileService.INVALID_USER_ID == g.user_id:
        raise ApiArgsError(*GlobalErrorCode.INVALID_TOKEN_ERR)
    return g.user_id


def get_require_check_with_user(args_name):
    """
    装饰器，校验用户以及GET请求中的参数，参数在http url中
    """

    def get_require_check_with_user_wrapper(fn):
        """
        校验用户及GET请求中的参数，通过则调用fn
        """

        @wraps(fn)
        def __wrapper(**arg):
            try:
                require_token_check(request, g)
                args = get_check_args(request, args_name)
                return jsonify(make_correct_resp(fn(g.user_id, args, **arg)))
            except AppErrorBase as ex:
                log.error(ex)
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                log.error(ex)
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))

        return __wrapper

    return get_require_check_with_user_wrapper


def post_require_check_with_user(args_name):
    """
    装饰器，校验用户以及POST请求中的参数，参数在http url中
    """

    def post_require_check_with_user_wrapper(fn):
        """
        校验用户及GET请求中的参数，通过则调用fn
        """

        @wraps(fn)
        def __wrapper(**arg):
            try:
                require_token_check(request, g)
                args = post_check_args(request, args_name)
                return jsonify(make_correct_resp(fn(g.user_id, args, **arg)))
            except AppErrorBase as ex:
                import traceback
                print traceback.format_exc()
                log.error(ex)
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                import traceback
                print traceback.format_exc()
                log.error(ex)
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))
        return __wrapper
    return post_require_check_with_user_wrapper


def is_authentication(user_info, path):
    """
    是否有模块权限
    :param user_info:
    :param path:
    :return:
    """
    operation_data = user_info['operation_data']
    for row in operation_data:
        r = re.compile(row['url']).match(path)
        if r:
            return True
    return False


def get_require_check_with_permissions(args_name):

    def get_require_check_with_user_wrapper(fn):

        @wraps(fn)
        def __wrapper(**arg):
            try:
                require_token_check(request, g)
                # 校验参数
                args = get_check_args(request, args_name)
                return jsonify(make_correct_resp(
                    fn(g.user_id, args, **arg)))
            except AppErrorBase as ex:
                log.error(ex)
                import traceback
                print(traceback.format_exc())
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                log.error(ex)
                import traceback
                print(traceback.format_exc())
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))

        return __wrapper

    return get_require_check_with_user_wrapper


def post_require_check_with_permissions(args_name):

    def post_require_check_with_user_wrapper(fn):

        @wraps(fn)
        def __wrapper(**arg):
            try:
                require_token_check(request, g)
                # 不需要校验参数
                if not len(args_name):
                    return jsonify(
                        make_correct_resp(
                            fn(g.user_id, parse_post_args(request), **arg)))
                # 校验参数
                args = post_check_args(request, args_name)
                return jsonify(make_correct_resp(fn(g.user_id, args, **arg)))
            except AppErrorBase as ex:
                log.error(ex)
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                import traceback
                print traceback.format_exc()
                log.error(ex)
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))

        return __wrapper
    return post_require_check_with_user_wrapper


def form_none_param_with_permissions():

    def form_with_user_wrapper(fn):

        @wraps(fn)
        def __wrapper(**arg):
            try:
                return jsonify(make_correct_resp(fn(None, None, **arg)))
            except AppErrorBase as ex:
                log.error(ex)
                return jsonify(make_error_resp(
                    ex.error_code,
                    ex.error_msg
                ))
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                return jsonify(make_error_resp(*GlobalErrorCode.UNKNOWN_ERR))
        return __wrapper
    return form_with_user_wrapper