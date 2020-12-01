# lbs子服务构建脚本
# build: docker build -t lbs.service:v1.0.0 .
# run: docker run -it --rm -p :80:80 -e "APP_MONGO_URI=mongodb://localhost:27017/test_db?connect=false" lbs.service:v1.0.0

# 基础镜像
FROM registry.cn-hangzhou.aliyuncs.com/rapself/base:v1.0.0

# 维护者
MAINTAINER jianchao

# 创建代码目录
RUN mkdir -p /data/www
RUN mkdir -p /etc/aliyun-opensearch

# 复制代码
COPY ./search.app/ /data/www
COPY ./conf/app.ini /etc/uwsgi/apps-enabled/app.ini
COPY ./conf/app.conf /etc/supervisor/conf.d/app.conf
COPY ./aliyun-opensearch-python-sdk-master/ /etc/aliyun-opensearch

# 安装包
WORKDIR /data/www
RUN apt-get update \
    && PACKAGES='uwsgi uwsgi-plugin-python supervisor' \
    && apt-get install -y --no-install-recommends ${PACKAGES} \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt

WORKDIR /etc/aliyun-opensearch
RUN python setup.py install

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/app.conf"]
