# coding:utf-8
# 导入模块
import Cython.Build

if __name__ == '__main__':
    # 传入要编译成pyd的py文件
    ext1 = Cython.Build.cythonize("AlertInfoService.py")
    ext2 = Cython.Build.cythonize("CarService.py")
    ext3 = Cython.Build.cythonize("ConfigService.py")
    ext4 = Cython.Build.cythonize("DeviceService.py")
    ext5 = Cython.Build.cythonize("ExportTaskService.py")
    ext6 = Cython.Build.cythonize("IndexService.py")
    ext7 = Cython.Build.cythonize("MiniService.py")
    ext8 = Cython.Build.cythonize("OrderService.py")
    ext9 = Cython.Build.cythonize("SchoolService.py")
    ext10 = Cython.Build.cythonize("StudentService.py")
    ext11 = Cython.Build.cythonize("UserProfileService.py")
    ext12 = Cython.Build.cythonize("WorkerService.py")
    ext13 = Cython.Build.cythonize("WxMPservice.py")

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
    distutils.core.setup(ext_modules=ext13)
