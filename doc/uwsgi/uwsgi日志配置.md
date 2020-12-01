# uwsgi日志转储

#### daemonize=/data/log/uwsgi/uwsgi.log，uwsgi的日志转储经过验证使用logrotate是不可行的，uwsgi本身提供根据文件大小来rotate的功能，如果想要通过日期每天转储，首先需要使用touch-logreopen来设置一个监听对象：
```
daemonize=/data/logs/uwsgi/uwsgi.log
# 使得uwsgi.log文件被转存后能继续在uwsgi.log文件中写入日志,且不会中断当前程序的执行
touch-logreopen =/data/logs/uwsgi/.touchforlogrotat
```
#### 在创建脚本touchforlogrotat.sh
```
#!/bin/bash

DIR=`echo $(cd "$(dirname "$0")"; pwd)`       #获取当前目录
LOGDIR="/data/logs/uwsgi/"                   #log目录

sourcelogpath="${LOGDIR}uwsgi.log"            #log源地址
touchfile="${LOGDIR}.touchforlogrotat"       #需要touch的文件

DATE=`date -d "yesterday" +"%Y%m%d"`
destlogpath="${LOGDIR}uwsgi-${DATE}.log"     #重命名后的文件
mv $sourcelogpath $destlogpath

touch $touchfile                            # 更新文件时间戳
```

#### 当监听对象touch-logreopen所指向的文件被touch，时间戳改变后，uwsgi会重新打开uwsgi.log文件进行写入，且不会中断当前程序的执行。如果没有touch-logreopen这个监听对象，是无法对uwsgi.log进行转储的。通过crontab设置定时任务
```
crontab -e
```

#### 输入以下行，表示每天0点进行转储
```
0 0 * * * sh /home/vhost/transport/touchforlogrotate.sh
```