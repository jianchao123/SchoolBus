# coding:utf-8
# 导入模块
import Cython.Build
from os import path
d = path.dirname(__file__)

if __name__ == '__main__':
    # 传入要编译成pyd的py文件
    ext1 = Cython.Build.cythonize("{}/AcsManager.py".format(d))

    # 下面还要导入另一个模块
    import distutils.core

    # 调用setup方法
    distutils.core.setup(ext_modules=ext1)

