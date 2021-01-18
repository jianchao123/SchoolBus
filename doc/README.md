@[TOC](无感行后台)

# 消息队列

### 消息队列启动
```
# shell命令
workon transport
python consumer.py
``` 

### 发布消息
```python
from msgqueue import producer
d = {"id": 123}
producer.generate_create_user_msg(d["id"])
```

# 定时器

### 定时器启动
```
python run.py
```

# MNS

### mns启动
```
python recvdelmessage.py
```

# 服务器返回数据格式
### 数据格式
```python
{
    "msg": "error message",
    "data": [], # 数据,可能是数组可能是json,具体看对应的接口
    "status": 0 # 0 接口正常,非0表示接口错误,具体错误看对应的接口
}
```

# pip安装包报错
## psycopg2报错
```python
# sudo apt-get install python-psycopg2
# sudo apt-get install libpq-dev

```

## M2Crypto报错
```python
# sudo apt-get install swig libssl-dev
```

## -- unavailable modifier requested: 0 --
```python
# apt-get install uwsgi-plugin-python
```