# coding:utf-8
import os

project_name = "school_bus"
project_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))))
env_dist = os.environ
env = env_dist.get('BUS_ENV')

if env == "TEST":
    # 物联网
    Productkey = 'a1vperyb2Cg'
    ProductHost = 'a1vperyb2Cg.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'jqSbrJZ11baH1aAH'
    DeviceSecret = 'bmq66tsx0OGju0CGqeYjzCTYlwA454j0'

    # OSS
    OSSDomain = 'cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
    OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'
    OSSEndpoint = ''
    OSSBucketName = ''

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI4GL6gtEc4bnmj82yQ9wc'
    MNSAccessKeySecret = 'vhuBLJpqlOsSisnuUQ1xvE02GCXhIC'

    # LOG
    log_path = "/data/logs/{}/timer".format(project_name)

    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

    # 高德
    GD_AK = "7db32e8af1a361c8f86e10b58ad7a08e"

    # 百度音频转换
    BAIDU_APP_ID = '23117459'
    BAIDU_API_KEY = 'e8ZnYfnzvlptbcxdAYcYtTVI'
    BAIDU_SECRET_KEY = 'l8bkk6odc03fXgnLDxrYQuRwe62yFsQ2'

    # 微信公众号
    MP_ID = 'gh_949a03d359ca'
    MP_APP_ID = 'wxfe59baf99b8ff1d4'
    MP_APP_SECRET = 'bf3e50ed4b549fc007d5ad39634cdc4d'
    MP_TOKEN = 'gK9gY3cV2bM6pH9gF7vJ5uC8vN9cI0cL'
    MP_ENCODING_AES_KEY = 'CAmGrrm1rJ0HqgcbIBQbhKAHLUKGGbv3RJTTFnixTaC'


elif env == "PRO":

    # 物联网
    Productkey = 'a1nppCCo0Y2'
    ProductHost = 'a1nppCCo0Y2.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'VYMQSqHamIQgREVi'
    DeviceSecret = 'e2245121d52abc850b2fc220f937f512'

    # OSS
    OSSDomain = 'cdbus-pro.oss-cn-shanghai.aliyuncs.com'
    OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
    OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'
    OSSEndpoint = 'http://oss-cn-shanghai.aliyuncs.com'
    OSSBucketName = 'cdbus-pro'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai-internal.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI4GL6gtEc4bnmj82yQ9wc'
    MNSAccessKeySecret = 'vhuBLJpqlOsSisnuUQ1xvE02GCXhIC'

    # LOG
    log_path = "/data/logs/{}/timer".format(project_name)

    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

    # 高德
    GD_AK = "7db32e8af1a361c8f86e10b58ad7a08e"

    # 百度音频转换
    BAIDU_APP_ID = '23117459'
    BAIDU_API_KEY = 'e8ZnYfnzvlptbcxdAYcYtTVI'
    BAIDU_SECRET_KEY = 'l8bkk6odc03fXgnLDxrYQuRwe62yFsQ2'

    # 微信公众号
    MP_ID = 'gh_949a03d359ca'
    MP_APP_ID = 'wxfe59baf99b8ff1d4'
    MP_APP_SECRET = 'bf3e50ed4b549fc007d5ad39634cdc4d'
    MP_TOKEN = 'gK9gY3cV2bM6pH9gF7vJ5uC8vN9cI0cL'
    MP_ENCODING_AES_KEY = 'CAmGrrm1rJ0HqgcbIBQbhKAHLUKGGbv3RJTTFnixTaC'

    MP_PARENTS_TEMPLATE_ID = "aRznTze3zLqP9mSoOh45DhrAgL-OOz3ut2bE0c5TwpM"
    MP_STAFF_TEMP_ID = "NlJspxFFiPl4lH8gjf-pKU-dZiMuFYgdSJ4wSpmEesg"

    # 监控中心
    SC_URL = "https://car.vcolco.com/api/paas-trans-school-bus/school/bus/report"

    # MP_PARENTS_REDIRECT_URL = \
    #     "http://cdmp.wgxing.com/static/push.html?order_id={}"
    # MP_STAFF_REDIRECT_URL = \
    #     "http://cdmp.wgxing.com/static/alert.html?periods={}"

else:
    # # 物联网
    Productkey = 'a1vperyb2Cg'
    ProductHost = 'a1vperyb2Cg.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'jqSbrJZ11baH1aAH'
    DeviceSecret = 'bmq66tsx0OGju0CGqeYjzCTYlwA454j0'


    # OSS
    OSSDomain = 'cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSEndpoint = 'http://oss-cn-shanghai.aliyuncs.com'
    OSSEndpointInternal = 'http://oss-cn-shanghai-internal.aliyuncs.com'
    OSSBucketName = 'cdbus-dev'
    OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
    OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI4GL6gtEc4bnmj82yQ9wc'
    MNSAccessKeySecret = 'vhuBLJpqlOsSisnuUQ1xvE02GCXhIC'

    # LOG
    log_path = project_dir + "/logs/timer"

    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

    # 高德
    GD_AK = "7db32e8af1a361c8f86e10b58ad7a08e"

    # 百度音频转换
    BAIDU_APP_ID = '23117459'
    BAIDU_API_KEY = 'e8ZnYfnzvlptbcxdAYcYtTVI'
    BAIDU_SECRET_KEY = 'l8bkk6odc03fXgnLDxrYQuRwe62yFsQ2'

    # 微信公众号
    MP_ID = 'gh_949a03d359ca'
    MP_APP_ID = 'wxfe59baf99b8ff1d4'
    MP_APP_SECRET = 'bf3e50ed4b549fc007d5ad39634cdc4d'
    MP_TOKEN = 'gK9gY3cV2bM6pH9gF7vJ5uC8vN9cI0cL'
    MP_ENCODING_AES_KEY = 'CAmGrrm1rJ0HqgcbIBQbhKAHLUKGGbv3RJTTFnixTaC'

    # 监控中心
    SC_URL = ""

redis_conf = dict(host="127.0.0.1", port=6379, db=0, decode_responses=True)
pgsql_conf = dict(host=pgsql_host, database=pgsql_db, port=pgsql_port,
                  user=pgsql_user, password=pgsql_passwd)
print env