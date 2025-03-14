# coding:utf-8
# 导入模块
import Cython.Build
from os import path
d = path.dirname(__file__)

if __name__ == '__main__':
    # 传入要编译成pyd的py文件
    ext1 = Cython.Build.cythonize("{}/AlertInfoController.py".format(d))
    ext2 = Cython.Build.cythonize("{}/CarController.py".format(d))
    ext3 = Cython.Build.cythonize("{}/ConfigController.py".format(d))
    ext4 = Cython.Build.cythonize("{}/DeviceController.py".format(d))
    ext5 = Cython.Build.cythonize("{}/ExportTaskController.py".format(d))
    ext6 = Cython.Build.cythonize("{}/IndexController.py".format(d))
    ext7 = Cython.Build.cythonize("{}/OrderController.py".format(d))
    ext8 = Cython.Build.cythonize("{}/SchoolController.py".format(d))
    ext9 = Cython.Build.cythonize("{}/StudentController.py".format(d))
    ext10 = Cython.Build.cythonize("{}/UserProfileController.py".format(d))
    ext11 = Cython.Build.cythonize("{}/WorkerController.py".format(d))
    ext12 = Cython.Build.cythonize("{}/WxMPController.py".format(d))

    # 下面还要导入另一个模块
    import distutils.core

    # 调用setup方法
    distutils.core.setup(ext_modules=ext1)
    distutils.core.setup(ext_modules=ext2)
    distutils.core.setup(ext_modules=ext3)
    distutils.core.setup(ext_modules=ext4)
    distutils.core.setup(ext_modules=ext5)
    distutils.core.setup(ext_modules=ext6)
    distutils.core.setup(ext_modules=ext7)
    distutils.core.setup(ext_modules=ext8)
    distutils.core.setup(ext_modules=ext9)
    distutils.core.setup(ext_modules=ext10)
    distutils.core.setup(ext_modules=ext11)
    distutils.core.setup(ext_modules=ext12)
