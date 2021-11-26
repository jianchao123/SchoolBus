# coding:utf-8
import os
import configparser

project_name = "school_bus"
project_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))))
env_dist = os.environ
env = "DEV"
if env == "TEST":
    log_path = "/data/logs/{}/mns".format(project_name)
elif env == 'PRO':
    log_path = "/data/logs/{}/mns".format(project_name)
else:
    log_path = project_dir + "/logs/mns"


config_name = os.environ.get('BUS_ENV', 'DEV')
if config_name == 'PRO':
    setting_file = 'setting_pro.ini'
elif config_name == 'TEST':
    setting_file = 'setting_test.ini'
else:
    setting_file = 'setting_dev.ini'


class MyConfigParser(configparser.ConfigParser):

    def __init__(self, defaults=None):
        configparser.ConfigParser.__init__(self, defaults=defaults)

    # 这里重写了optionxform方法，直接返回选项名
    def optionxform(self, optionstr):
        return optionstr


config = MyConfigParser()
real_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), setting_file)
config.read(real_path, encoding='utf-8')
secs = config.sections()
for section in secs:
    kvs = config[section].items()
    globals().update(kvs)
    # for k, v in kvs:
    #     print k, v

config_namespace = globals()
redis_conf = dict(host="127.0.0.1", port=6379, db=0, decode_responses=True)
pgsql_conf = dict(host=config_namespace['pgsql_host'],
                  database=config_namespace['pgsql_db'],
                  port=config_namespace['pgsql_port'],
                  user=config_namespace['pgsql_user'],
                  password=config_namespace['pgsql_passwd'])

print env
