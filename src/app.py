# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from werkzeug.utils import ImportStringError
from flask import Flask
from werkzeug.utils import find_modules, import_string
from flasgger import Swagger
from flask_cors import *


def register_blueprints(root, app):
    """
    蓝图注册帮助函数

    args:
        root: 蓝图所在模块
        app: Flask实例
    """

    # find_modules读到pyc了,import_string会报错
    for name in find_modules(root, recursive=False):
        try:
            mod = import_string(name)
            if hasattr(mod, 'bp') and hasattr(mod, 'url_prefix'):
                app.register_blueprint(
                    mod.bp, url_prefix=mod.url_prefix)
        except ImportStringError:
            continue


def create_app():
    """
    创建flask app对象
    """
    app = Flask(__name__)

    Swagger(app)
    CORS(app, supports_credentials=True)

    # 加载配置
    from config import load_config
    app.config.from_object(load_config())

    # 初始化log conf对象
    from ext import log, conf, cache
    log.init_app(app)
    conf.init_app(app)
    cache.init_app(app)

    register_blueprints('controller', app)
    # from controller import bp
    # app.register_blueprint(bp, url_prefix='/user')

    return app


"""应用app对象"""
app = create_app()

if __name__ == '__main__':
    app.run()
