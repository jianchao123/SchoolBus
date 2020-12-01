# coding:utf-8

import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

project_src_dir = os.path.dirname(os.path.realpath(__file__))
project_src_dir = os.path.dirname(project_src_dir)
sys.path.insert(0, project_src_dir)

from apscheduler.schedulers.gevent import BlockingScheduler

from timer.RestTimer import GenerateTid, QueryFeature, EveryMinuteExe, \
    FromOssQueryFace, EveryFewMinutesExe, OrderSendMsg

if __name__ == "__main__":
    generate_tid = GenerateTid()
    query_feature = QueryFeature()
    every_minute_exe = EveryMinuteExe()
    from_oss_query_face = FromOssQueryFace()
    every_few_minutes_exe = EveryFewMinutesExe()
    order_send_msg = OrderSendMsg()

    sched = BlockingScheduler()
    sched.add_job(generate_tid.generate_tid, 'interval', seconds=13)
    sched.add_job(query_feature.query_feature, 'interval', seconds=9)
    sched.add_job(from_oss_query_face.from_oss_get_face, 'interval', seconds=16)
    sched.add_job(func=every_minute_exe.every_minute_execute,
                  trigger='cron', day="*", hour="*", minute="*")
    sched.add_job(func=every_few_minutes_exe.every_few_minutes_execute,
                  trigger='cron', day="*", hour="*", minute="*/5")
    sched.add_job(order_send_msg.order_sent_msg, 'interval', seconds=0.3)
    sched.start()

    # g = sched.start()
    # g.join()
