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
    OSSDomain = 'https://cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
    OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'
    OSSEndpoint = ''
    OSSBucketName = ''

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI4GL6gtEc4bnmj82yQ9wc'
    MNSAccessKeySecret = 'vhuBLJpqlOsSisnuUQ1xvE02GCXhIC'

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
    MP_PARENTS_TEMPLATE_ID = "aRznTze3zLqP9mSoOh45DhrAgL-OOz3ut2bE0c5TwpM"
    MP_STAFF_TEMP_ID = "NlJspxFFiPl4lH8gjf-pKU-dZiMuFYgdSJ4wSpmEesg"
    MP_PARENTS_REDIRECT_URL = "http://cdmp.wgxing.com/index.html?order_id={}"
    MP_STAFF_REDIRECT_URL = "http://cdmp.wgxing.com/alert.html?periods={}"


elif env == "PRO":
    # 物联网
    Productkey = ''
    ProductHost = ''
    ProductSecret = ''
    DeviceSecret = ''

    # OSS
    OSSDomain = ''
    OSSAccessKeyId = ''
    OSSAccessKeySecret = ''
    OSSEndpoint = ''
    OSSBucketName = ''

    # MNS
    MNSEndpoint = ''
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
    MP_PARENTS_TEMPLATE_ID = "aRznTze3zLqP9mSoOh45DhrAgL-OOz3ut2bE0c5TwpM"
    MP_STAFF_TEMP_ID = "NlJspxFFiPl4lH8gjf-pKU-dZiMuFYgdSJ4wSpmEesg"
    MP_PARENTS_REDIRECT_URL = "http://cdmp.wgxing.com/index.html?order_id={}"
    MP_STAFF_REDIRECT_URL = "http://cdmp.wgxing.com/alert.html?periods={}"

else:
    # 物联网
    Productkey = 'a1vperyb2Cg'
    ProductHost = 'a1vperyb2Cg.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'jqSbrJZ11baH1aAH'
    DeviceSecret = 'bmq66tsx0OGju0CGqeYjzCTYlwA454j0'

    # OSS
    OSSDomain = 'https://cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSAccessKeyId = 'LTAIWE5CGeOiozf7'
    OSSAccessKeySecret = 'IGuoRIxwMlPQqJ9ujWyTvSq2em4RDj'
    OSSEndpoint = 'oss-cn-shanghai.aliyuncs.com'
    OSSBucketName = 'cdbus-dev'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI4GL6gtEc4bnmj82yQ9wc'
    MNSAccessKeySecret = 'vhuBLJpqlOsSisnuUQ1xvE02GCXhIC'

    # LOG
    log_path = project_dir + "/logs/msgqueue"

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
    MP_PARENTS_REDIRECT_URL = "http://cdmp.wgxing.com/index.html?order_id={}"
    MP_STAFF_REDIRECT_URL = "http://cdmp.wgxing.com/alert.html?periods={}"

redis_conf = dict(host="127.0.0.1", port=6379, db=0, decode_responses=True)
pgsql_conf = dict(host=pgsql_host, database=pgsql_db, port=pgsql_port,
                  user=pgsql_user, password=pgsql_passwd)

logger = get_logger(log_path)
logger.info('--------ENV={}---------------'.format(env))
print env