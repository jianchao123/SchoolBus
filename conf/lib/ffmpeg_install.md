#### 1. 从FFmpeg的Github上下载源码
> git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
#### 2. 安装
>./configure --prefix=/usr/local/ffmpeg --enable-shared --disable-static --disable-doc --enable-ffplay --disable-x86asm
make
sudo make install
#### 3. 环境变量
>sudo vim /etc/profile
##### 添加以下内容
>export FFMPEG_HOME=/usr/local/ffmpeg
export PATH=$PATH:$FFMPEG_HOME/bin
export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig

##### 保存退出后，使配置生效
>source /etc/profile

##### 在/etc/ld.so.conf.d/下添加以下文件
>ffmpeg.conf

##### 内容为lib目录
>/usr/local/ffmpeg/lib

##### 使配置生效
>sudo ldconfig

#### 4. 配置pkg-config(可选)
>mkdir /usr/local/lib/pkgconfig/
cp /usr/local/ffmpeg/lib/pkgconfig/*.pc /usr/local/lib/pkgconfig/

##### 测试
> pkg-config --libs libavcodec libavdevice libavfilter libavformat libavutil libswresample libswscale

##### 编译方法
> g++ main.c -o main.o -I /usr/ffmpeg/include `pkg-config libavcodec libavdevice libavfilter libavformat libavutil libswresample libswscale --cflags --libs`

###### 相当于

>g++ main.c -o main.o -I /usr/local/ffmpeg/include -L /usr/ffmpeg/lib -lavcodec -lavdevice -lavfilter -lavformat -lavutil -lswresample -lswscale
========================== 2019.7.17 补充 ==========================

##### 添加libx264
> git clone http://git.videolan.org/git/x264.git
cd x264/
./configure --enable-shared --disable-asm
make
sudo make install

##### 重新编译FFmpeg

> ./configure --prefix=/usr/ffmpeg --enable-shared --disable-static --disable-doc --enable-libx264 --enable-gpl --disable-asm

