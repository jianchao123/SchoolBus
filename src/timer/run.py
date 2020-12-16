# coding:utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

project_src_dir = os.path.dirname(os.path.realpath(__file__))
project_src_dir = os.path.dirname(project_src_dir)
sys.path.insert(0, project_src_dir)

from apscheduler.schedulers.gevent import BlockingScheduler

from timer.RestTimer import GenerateFeature, EveryMinuteExe, \
    FromOssQueryFace, EveryFewMinutesExe, OrderSendMsg, GenerateAAC, \
    EveryHoursExecute, CheckAccClose

if __name__ == "__main__":
    generate_feature = GenerateFeature()
    every_minute_exe = EveryMinuteExe()
    from_oss_query_face = FromOssQueryFace()
    every_few_minutes_exe = EveryFewMinutesExe()
    every_hours_exe = EveryHoursExecute()
    order_send_msg = OrderSendMsg()
    generate_aac = GenerateAAC()
    check_acc_close = CheckAccClose()

    sched = BlockingScheduler()
    # 顺序发送消息
    sched.add_job(order_send_msg.order_sent_msg, 'interval', seconds=0.5)
    # 生成特征码
    sched.add_job(generate_feature.generate_feature, 'interval', seconds=1)
    # 生成aac文件
    sched.add_job(generate_aac.generate_audio, 'interval', seconds=10)
    # 检查acc熄火key
    sched.add_job(check_acc_close.check_acc_close, 'interval', seconds=11)
    # 上传人脸zip包到oss,将人脸匹配到记录
    sched.add_job(from_oss_query_face.from_oss_get_face, 'interval', seconds=16)
    # 每分钟执行
    sched.add_job(func=every_minute_exe.every_minute_execute,
                  trigger='cron', day="*", hour="*", minute="*")
    # 每五分钟执行
    sched.add_job(func=every_few_minutes_exe.every_few_minutes_execute,
                  trigger='cron', day="*", hour="*", minute="*/5")
    # 每小时执行
    sched.add_job(func=every_hours_exe.every_hours_execute,
                  trigger='cron', day="*", hour="*")
    sched.start()

    # g = sched.start()
    # g.join()
