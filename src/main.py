# coding:utf-8
from flask import Flask
from flasgger import Swagger
from flask_cors import *


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

    from controller.UserProfileController import bp
    app.register_blueprint(bp, url_prefix='/user')
    return app


"""应用app对象"""
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
