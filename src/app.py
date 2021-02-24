# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from werkzeug.utils import ImportStringError
from werkzeug.utils import find_modules, import_string
from flask import Flask
from flask_cors import *
from flasgger import Swagger


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
    from ext import log, conf, cache, cache1
    log.init_app(app)
    conf.init_app(app)
    cache.init_app(app)
    app.config['REDIS_DB'] = 1
    cache1.init_app(app)
    from flask_sqlalchemy import SQLAlchemy
    SQLAlchemy(app)
    register_blueprints('controller', app)

    # from controller import bp
    # app.register_blueprint(bp, url_prefix='/user')

    # from controller.UserProfileController import bp as user_bp
    # from controller.AlertInfoController import bp as alert_bp
    # from controller.CarController import bp as car_bp
    # from controller.DeviceController import bp as device_bp
    # from controller.OrderController import bp as order_bp
    # from controller.SchoolController import bp as school_bp
    # from controller.StudentController import bp as student_bp
    # from controller.WorkerController import bp as worker_bp
    # app.register_blueprint(user_bp, url_prefix='/user')
    # app.register_blueprint(alert_bp, url_prefix='/alert_info')
    # app.register_blueprint(car_bp, url_prefix='/car')
    # app.register_blueprint(device_bp, url_prefix='/device')
    # app.register_blueprint(order_bp, url_prefix='/order')
    # app.register_blueprint(school_bp, url_prefix='/school')
    # app.register_blueprint(student_bp, url_prefix='/student')
    # app.register_blueprint(worker_bp, url_prefix='/worker')
    return app


"""应用app对象"""
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
