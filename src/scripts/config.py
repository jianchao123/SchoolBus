# coding=utf-8

env = "PRO"
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

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI5tLzBs74j8dEX4A8TPy6'
    MNSAccessKeySecret = 'uLU5qLEdxet7IZ6w7uB3t7U5PVo15F'


    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

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
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI5tLzBs74j8dEX4A8TPy6'
    MNSAccessKeySecret = 'uLU5qLEdxet7IZ6w7uB3t7U5PVo15F'

    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

else:
    # 物联网
    Productkey = 'a1vperyb2Cg'
    ProductHost = 'a1vperyb2Cg.iot-as-mqtt.cn-shanghai.aliyuncs.com'
    ProductSecret = 'jqSbrJZ11baH1aAH'
    DeviceSecret = 'bmq66tsx0OGju0CGqeYjzCTYlwA454j0'

    # OSS
    OSSDomain = 'cdbus-dev.oss-cn-shanghai.aliyuncs.com'
    OSSAccessKeyId = 'LTAI5tHYr3CZ59HCRLEocbDG'
    OSSAccessKeySecret = 'BMRI8WzUVMRbS6LHPM3bIiadWIPE8c'
    OSSEndpoint = 'http://oss-cn-shanghai.aliyuncs.com'
    OSSBucketName = 'cdbus-dev'

    # MNS
    MNSEndpoint = 'http://1162097573951650.mns.cn-shanghai.aliyuncs.com/'
    MNSAccessKeyId = 'LTAI5tLzBs74j8dEX4A8TPy6'
    MNSAccessKeySecret = 'uLU5qLEdxet7IZ6w7uB3t7U5PVo15F'

    # PGSQL
    pgsql_host = '127.0.0.1'
    pgsql_db = "postgres"
    pgsql_port = 5432
    pgsql_user = "postgres"
    pgsql_passwd = "kIhHAWexFy7pU8qM"

redis_conf = dict(host="127.0.0.1", port=6379, db=0, decode_responses=True)
pgsql_conf = dict(host=pgsql_host, database=pgsql_db, port=pgsql_port,
                  user=pgsql_user, password=pgsql_passwd)

print env