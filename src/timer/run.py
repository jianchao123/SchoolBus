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
    FromOssQueryFace, EveryFewMinutesExe, GenerateAAC, \
    EveryHoursExecute, CheckAccClose, RefreshWxAccessToken, \
    UploadAlarmData, FaceGenerateIsfinish, \
    EveryDayOneClock, DeviceMfrList

if __name__ == "__main__":
    generate_feature = GenerateFeature()
    every_minute_exe = EveryMinuteExe()
    from_oss_query_face = FromOssQueryFace()
    every_few_minutes_exe = EveryFewMinutesExe()
    every_hours_exe = EveryHoursExecute()
    generate_aac = GenerateAAC()
    check_acc_close = CheckAccClose()
    refresh_wx_access_token = RefreshWxAccessToken()
    upload_alarm_data = UploadAlarmData()
    face_generate_is_finish = FaceGenerateIsfinish()
    every_day_one_clock = EveryDayOneClock()
    device_mfr_list = DeviceMfrList()

    sched = BlockingScheduler()

    sched.add_job(upload_alarm_data.upload_alarm_data,
                  'interval', seconds=5)
    sched.add_job(face_generate_is_finish.face_generate_is_finish,
                  'interval', seconds=20)

    # 生成特征码
    sched.add_job(generate_feature.generate_feature, 'interval', seconds=2)
    # 生成aac文件
    sched.add_job(generate_aac.generate_audio, 'interval', seconds=10)
    # 检查acc熄火key
    sched.add_job(check_acc_close.check_acc_close, 'interval', seconds=5)
    # 上传人脸zip包到oss,将人脸匹配到记录
    sched.add_job(from_oss_query_face.from_oss_get_face, 'interval', seconds=16)
    # 刷新微信access token
    sched.add_job(refresh_wx_access_token.refresh_wechat_token,
                  'interval', seconds=30)
    sched.add_job(device_mfr_list.device_mfr_list,
                  'interval', seconds=35)
    # sched.add_job(heart_beat_30s.heartbeat,
    #               'interval', seconds=29)
    # sched.add_job(heart_beat_30s.send_order,
    #               'interval', seconds=10)
    # sched.add_job(heart_beat_30s.send_reg_dev_msg,
    #               'interval', seconds=2)

    # 每分钟执行
    sched.add_job(func=every_minute_exe.every_minute_execute,
                  trigger='cron', day="*", hour="*", minute="*")
    # 每五分钟执行
    sched.add_job(func=every_few_minutes_exe.every_few_minutes_execute,
                  trigger='cron', day="*", hour="*", minute="*/5")
    # 每小时执行
    sched.add_job(func=every_hours_exe.every_hours_execute,
                  trigger='cron', day="*", hour="*")
    # 凌晨任务
    sched.add_job(func=every_day_one_clock.everyday_one_clock,
                  trigger='cron', day="*", hour=1, minute=1, second=1)
    sched.add_job(every_hours_exe.every_hours_execute, 'interval', seconds=13)
    sched.start()

    # g = sched.start()
    # g.join()
