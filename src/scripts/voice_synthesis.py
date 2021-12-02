# -*- coding:utf-8 -*-
"""
windows python3环境下运行，生成的语音文件格式是wav，需要转换为aac
"""
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import wave
import os

FILENAME = ""

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class Ws_Param(object):
 # 初始化
 def __init__(self, APPID, APIKey, APISecret, d):
  self.APPID = APPID
  self.APIKey = APIKey
  self.APISecret = APISecret
  self.Text = d[1]
  global FILENAME
  FILENAME = d[0]

  # 公共参数(common)
  self.CommonArgs = {"app_id": self.APPID}
  # 业务参数(business)，更多个性化参数可在官网查看
  self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000",
                       "vcn": "xiaoyan", "tte": "utf8", "volume": 100}
  self.Data = {"status": 2,
               "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
  # 使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
  # self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

 # 生成url
 def create_url(self):
  url = 'wss://tts-api.xfyun.cn/v2/tts'
  # 生成RFC1123格式的时间戳
  now = datetime.now()
  date = format_date_time(mktime(now.timetuple()))

  # 拼接字符串
  signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
  signature_origin += "date: " + date + "\n"
  signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
  # 进行hmac-sha256进行加密
  signature_sha = hmac.new(self.APISecret.encode('utf-8'),
                           signature_origin.encode('utf-8'),
                           digestmod=hashlib.sha256).digest()
  signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

  authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
   self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
  authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(
   encoding='utf-8')
  # 将请求的鉴权参数组合为字典
  v = {
   "authorization": authorization,
   "date": date,
   "host": "ws-api.xfyun.cn"
  }
  # 拼接鉴权参数，生成url
  url = url + '?' + urlencode(v)
  # print("date: ",date)
  # print("v: ",v)
  # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
  # print('websocket url :', url)
  return url


def on_message(ws, message):
 try:
  message = json.loads(message)
  code = message["code"]
  sid = message["sid"]
  audio = message["data"]["audio"]
  audio = base64.b64decode(audio)
  status = message["data"]["status"]
  if status == 2:
   print("ws is closed")
   ws.close()
  if code != 0:
   errMsg = message["message"]
   print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
  else:
   pcm_path = './{}.pcm'.format(FILENAME)
   with open(pcm_path, 'ab') as f:
    f.write(audio)

   with open(pcm_path, 'rb') as pcmfile:
    pcmdata = pcmfile.read()
   with wave.open('./{}.wav'.format(FILENAME), 'wb') as wavfile:
    wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
    wavfile.writeframes(pcmdata)

 except Exception as e:
  print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
 print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws):
 print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
 def run(*args):
  d = {"common": wsParam.CommonArgs,
       "business": wsParam.BusinessArgs,
       "data": wsParam.Data,
       }
  d = json.dumps(d)
  print("------>开始发送文本数据")
  ws.send(d)
  if os.path.exists('./demo.pcm'):
   os.remove('./demo.pcm')

 thread.start_new_thread(run, ())

if __name__ == "__main__":
 # 测试时候在此处正确填写相关信息即可运行
 d = [["abnormal", "温度异常。"],
      ["deng", "等"],
      ["disconnected", "未连接服务器。"],
      ["down", "下车。"],
      ["intozhiliustatus", "分钟后将进入防滞留检测状态。"],
      ["min1", "一"], ["min2", "二"], ["min3", "三"], ["min4", "四"], ["min5", "五"],
      ["min6", "六"], ["min7", "七"], ["min8", "八"], ["min9", "九"],
      ["min10", "十"],
      ["normal", "温度正常。"],
      ["notice", "智能终端提醒您。"],
      ["overloaded", "已超载。"],
      ["qingzhuce", "请注册。"],
      ["up", "上车。"],
      ["xunluo", "同学没有下车，请巡逻车厢。"],
      ["xunluo_1", "名同学没有下车，请巡逻车厢。"],
      ["zhiliujiance", "请注意。现在开始防滞留报警检测，请未下车的同学迅速到屏幕前刷脸报警"],
      ["please_up", "请上车。"],
      ["put_coin", "请投币。"]]
 for row in d:
  wsParam = Ws_Param(APPID='5fcf2d79',
                     APISecret='646a4b68e00e843981d60f6274539ac4',
                     APIKey='9823762fc5fd1f88842967bd2a43488e',
                     d=row)
  websocket.enableTrace(False)
  wsUrl = wsParam.create_url()
  ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error,
                              on_close=on_close)
  ws.on_open = on_open
  ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
  import time

  time.sleep(5)
