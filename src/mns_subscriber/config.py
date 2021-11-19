# coding:utf-8
import os
from utils import get_logger

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
    OSSAccessKeyId = 'LTAI5tHYr3CZ59HCRLEocbDG'
    OSSAccessKeySecret = 'BMRI8WzUVMRbS6LHPM3bIiadWIPE8c'
    OSSEndpoint = ''
    OSSBucketName = ''

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = ''
    MNSAccessKeySecret = ''

    # LOG
    log_path = "/data/logs/{}/mns".format(project_name)

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
    OSSAccessKeyId = 'LTAI5tHYr3CZ59HCRLEocbDG'
    OSSAccessKeySecret = 'BMRI8WzUVMRbS6LHPM3bIiadWIPE8c'
    OSSEndpoint = 'http://oss-cn-shanghai.aliyuncs.com'
    OSSBucketName = 'cdbus-pro'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai-internal.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI5tLzBs74j8dEX4A8TPy6'
    MNSAccessKeySecret = 'uLU5qLEdxet7IZ6w7uB3t7U5PVo15F'

    # LOG
    log_path = "/data/logs/{}/mns".format(project_name)

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


else:
    # 物联网
    Productkey = 'a1vperyb2Cg'
    ProductHost = 'a1vperyb2Cg.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'jqSbrJZ11baH1aAH'
    DeviceSecret = 'bmq66tsx0OGju0CGqeYjzCTYlwA454j0'

    # OSS
    OSSDomain = 'cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSEndpoint = 'http://oss-cn-shanghai.aliyuncs.com'
    OSSBucketName = 'cdbus-dev'
    OSSAccessKeyId = 'LTAI5tHYr3CZ59HCRLEocbDG'
    OSSAccessKeySecret = 'BMRI8WzUVMRbS6LHPM3bIiadWIPE8c'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI5tLzBs74j8dEX4A8TPy6'
    MNSAccessKeySecret = 'uLU5qLEdxet7IZ6w7uB3t7U5PVo15F'

    # LOG
    log_path = project_dir + "/logs/mns"

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


redis_conf = dict(host="127.0.0.1", port=6379, db=0, decode_responses=True)
pgsql_conf = dict(host=pgsql_host, database=pgsql_db, port=pgsql_port,
                  user=pgsql_user, password=pgsql_passwd)

logger = get_logger(log_path)
logger.info('--------ENV={}---------------'.format(env))
print env