# coding:utf-8
import traceback
from functools import wraps
from decimal import Decimal
import redis
import psycopg2.extras
from DBUtils.PooledDB import PooledDB
from redis import ConnectionPool
import config as conf

# pgsql
pgsql_pool = PooledDB(
    creator=psycopg2,   # 使用连接数据库的模块 psycopg2
    maxconnections=6,   # 连接池允许的最大连接数，0 和 None 表示不限制连接数
    mincached=1,        # 初始化时，链接池中至少创建的空闲的链接，0 表示不创建
    maxcached=4,        # 链接池中最多闲置的链接，0 和 None 不限制
    blocking=False,     # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
    maxusage=None,      # 一个链接最多被重复使用的次数，None 表示无限制
    setsession=[],      # 开始会话前执行的命令列表
    **conf.pgsql_conf
)

# redis
rds_pool = ConnectionPool(**conf.redis_conf)
rds_conn = redis.Redis(connection_pool=rds_pool)


# 事务装饰器
def transaction(is_commit=False):
    def _transaction(func):
        @wraps(func)
        def __transaction(self, *args, **kwargs):
            pgsql_conn = None
            pgsql_cur = None
            try:
                pgsql_conn = pgsql_pool.connection()
                pgsql_cur = pgsql_conn.cursor()
                pgsql_cur.execute('BEGIN')
                result = func(self, pgsql_cur, *args, **kwargs)
                if is_commit:
                    pgsql_conn.commit()
                return result
            except:
                if pgsql_conn:
                    pgsql_conn.rollback()
                print traceback.format_exc()
            finally:
                if pgsql_cur:
                    pgsql_cur.close()
                if pgsql_conn:
                    pgsql_conn.close()

        return __transaction
    return _transaction


class PgsqlDbUtil(object):

    def __init__(self, pgsql_cur):
        self.pgsql_cur = pgsql_cur

    def get(self, sql):
        self.pgsql_cur.execute(sql)
        result = self.pgsql_cur.fetchone()
        return result

    def query(self, sql):
        self.pgsql_cur.execute(sql)
        result = self.pgsql_cur.fetchall()
        return result

    def insert(self, data, table_name=None):
        keys = ""
        values = ""
        time_list = ["now()", "NOW()", "current_timestamp",
                     "CURRENT_TIMESTAMP", "null"]
        for k, v in data.items():
            keys += k + ","
            if isinstance(v, (int, float, Decimal, long)) or \
                    v in time_list or "TO_DATE" in v or \
                    "TO_DATE" in v:
                values += str(v) + ","
            else:
                values += "'" + str(v) + "'" + ","

        keys = keys[:-1]
        values = values[:-1]

        sql = "INSERT INTO {}({}) VALUES({})".format(table_name, keys, values)
        print sql
        self.pgsql_cur.execute(sql)

    def update(self, data, table_name=None):
        sql = "UPDATE {} SET ".format(table_name)
        for k, v in data.items():
            if k != '`id`':
                if isinstance(v, (int, float, Decimal, long)):
                    sql += k + "=" + str(v) + ","
                elif v in ["now()", "NOW()", "current_timestamp",
                           "CURRENT_TIMESTAMP"]:
                    sql += k + "=" + v + ","
                elif "TO_DATE" in v:
                    sql += k + "=" + v + ","
                else:
                    sql += k + "=" + "'" + v + "'" + ","
        if isinstance(data["`id`"], list):
            sql = sql[:-1] + " WHERE `id` in ({})".format(",".join(data["`id`"]))
        else:
            sql = sql[:-1] + " WHERE `id` = {}".format(data["`id`"])
        self.pgsql_cur.execute(sql)

    def delete_all(self, table_name=None):
        self.pgsql_cur.execute("DELETE FROM `{}` WHERE 1=1".format(table_name))

    def execute_sql(self, sql):
        return self.pgsql_cur.execute(sql)