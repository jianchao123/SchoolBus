# coding:utf-8
import os


def wav2aac():
    path = "./temp/voice"  # 文件夹目录
    files = os.listdir(path)  # 得到文件夹下的所有文件名称
    for row in files:  # 遍历文件夹
        if not os.path.isdir(row):  # 判断是否是文件夹，不是文件夹才打开
            if "wav" in row:
                local_path = path + "/" + row
                aac_path = path + "/" + row.replace("wav", "aac")
                os.system(
                    'ffmpeg -i {} -codec:a aac -b:a 32k {}'.format(local_path, aac_path))


wav2aac()