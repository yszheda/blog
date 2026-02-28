Title: 用Docker容器来生成quick-x/cocos2d-x游戏apk包
Date: 2016-07-28 02:13:00
description: Build Quick-x/Cocos2d-x apk on Docker Container
Tags: cocos2d-x, Docker, CS, tech, Docker, cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20160728-dockerfile-for-building-quickx-apk
Category: tech

前段时间本渣在做服务器端开发时，采用了`Docker`作为解决方案的一部分，最初的动机主要是想用`namespace`做环境隔离、用`cgroups`做资源限制，却也切身体会到`Docker`所带来的构建上的便利。故而本渣也回头去想之前cocos2d-x客户端的开发工作是否也能`Docker`化，很快就找到了一个很适合采用`Docker`的场景，那就是打apk包。从之前[搭建cocos2d-x游戏开发环境的博文](/2014/08/03/20140803-customize-dev-environment-for-cocos2d-x.html)中不难发现，要搭建打包环境特别麻烦，不仅需要下一堆软件包，而且安装Android SDK和NDK时还会遇到GFW的问题。也正是因为这个缘故，我们团队只有最开始的三位老司机在开发机上搭好了这套环境，之后陆陆续续来的新人都没做过这项工作，所以平时打包也基本是在这几台开发机上。这简直太应该`Docker`化了！有了一套配好打包环境的`Docker` image，再也不用担心小鲜肉跑来要求打包、占用开发机了！而且还可以扔到服务器上去做，多省心啊！想想就excited，于是本渣马上就折腾起`Dockerfile`来了！

首先要确定基础镜像。本渣一开始以为，配置`Linux`下的cocos2d-x打包环境需要在执行cocos2d-x代码里的`build/install-deps-linux.sh`，而这个脚本需要用到`Debian`系的包管理器，所以就选了`Ubuntu`作为基础镜像。

配置apk打包环境自然少不了下载需要的软件包。`Ubuntu`的`apt-get install`会询问用户是否安装软件包，在`Dockerfile`中需要把这一交互性去掉，最好采用：

```
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y
```

有些人喜欢把`DEBIAN_FRONTEND`设成`ENV`，这样`ENV`下面的命令就不用重复打`DEBIAN_FRONTEND=noninteractive`：

```
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get install -y
```

但根据[Deploying Python with Docker](https://medium.com/@rlbaker/deploying-python-with-docker-15a472cf12a5#.5vl6ihty3)的说法，这种做法是不推荐的，因为这会影响到容器使用，最好还是对每条需要的命令单独设置环境变量。

安装的几个软件包中少不了`Java`，我用的是Oracle的而非`openjdk`，所以需要用`add-apt-repository`把Oracle的ppa加上，这又需要先安装`add-apt-repository`：

```
# 更新软件包列表
RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq

# 安装add-apt-repository
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python-software-properties software-properties-common

# 安装Oracle Java
RUN echo "debconf shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections
RUN echo "debconf shared/accepted-oracle-license-v1-1 seen true" | debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive add-apt-repository ppa:webupd8team/java \
    && apt-get update -qq
RUN DEBIAN_FRONTEND=noninteractive apt-get -y oracle-java6-installer
```

打包还需要`ant`、之后下载SDK等需要`wget`或`curl`，这些软件包可以写在这句`apt-get -y`后面，因为我们不希望`Docker` image有太多layer。

接下来就是下载Android SDK和设置相应的环境变量了。Android SDK和NDK的google下载链接是被墙的，可以换成国内相关镜像的链接。本渣是先下好这些包，然后在我们内网nginx起了一个简单的静态页面，我们内部再通过这个页面去下载就灰常快了XD

```
# Install Android SDK
ENV ANDROID_SDK_ROOT /opt/android-sdk-linux

RUN cd /opt && wget -q https://dl.google.com/android/android-sdk_r24.4.1-linux.tgz -O android-sdk.tgz \
    && tar -zxvf android-sdk.tgz \
    && rm -f android-sdk.tgz

ENV PATH ${PATH}:${ANDROID_SDK_ROOT}:${ANDROID_SDK_ROOT}/tools

RUN echo y | android update sdk --no-ui --all --filter platform-tools | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter extra-android-support | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter android-20 | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter build-tools-20.0.0 | grep 'package installed'
```

如果你需要用代理来绕过GFW，可以这么写：

```
# NOTE: google is blocked by GFW in China,
# So I use the proxy: http://android-mirror.bugly.qq.com:8080.
# You can remove `--proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s`
# in the following commands if you don't have to worry about this issue.
RUN echo y | android update sdk --no-ui --all --filter platform-tools --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter extra-android-support --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter android-20 --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s | grep 'package installed'
RUN echo y | android update sdk --no-ui --all --filter build-tools-20.0.0 --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s | grep 'package installed'
```

接下来就是安装Android NDK了，和SDK差不多。

```
# Install Android NDK
ENV ANDROID_NDK_ROOT /opt/android-ndk-r10e
ENV NDK_ROOT /opt/android-ndk-r10e

RUN cd /opt && wget -q http://dl.google.com/android/repository/android-ndk-r10e-linux-x86_64.zip -O android-ndk.zip \
    && unzip -q android-ndk.zip \
    && rm -f android-ndk.zip

ENV PATH ${PATH}:${ANDROID_NDK_ROOT}
```

最后别忘了清理安装的软件包：

```
RUN apt-get clean
```

到了这一步，本渣就可以先把`Docker` image构建起来，把cocos2d-x代码、quick-x代码和客户端代码作为host的三个volumn挂载到`Docker` container里了。经试验发现还需要做如下配置：

- 在`PATH`里加入`cocos2d-console/bin`的目录才能使用`cocos`命令。

- `cocos2d-console`需要安装`python`。

- 需要把quick-x代码所在目录配在`QUICK_V3_ROOT`环境变量中。

- quick-x用到`php`，需要安装。

- 需要装上32位系统的软件包`lib32stdc++6`和`lib32z1`才能正常打包。

于是本渣就可以相应地在`Dockerfile`中继续添加了，虽然试验的过程有点繁琐，但可以保证生成的`Docker` image只包含需要的软件包，让image尽可能小。

接下来就是如何继续优化了，例如以上需要从host挂载cocos2d-x代码和quick-x代码的volumn还是比较烦。其中我们完全没必要把整份cocos2d-x代码挂载进来，因为创建cocos2d-x项目时会把需要的源代码文件拷到项目目录里，所以我们只需要其中的`cocos2d-console`，配置好`cocos`所在的目录到环境变量`PATH`即可。最后我把`cocos2d-console`和`quick-x`的代码打包，放到之前的内网网页中，这样就有了一份只需要挂载项目代码目录就能进行apk打包的`Dockerfile`啦！

还记得前面所提到的cocos2d-x代码里的`build/install-deps-linux.sh`脚本吗？其实这个脚本还是有交互，所以我也把它所实现的功能挪到了`Dockerfile`中，其实也不外乎用`apt-get`下载一些软件包和下载`glfw`编译安装罢了。既然这个脚本并非必须，那么基础镜像也就不一定非要`Debian`系的系统了，小巧的`Alpine`无疑才是更理想的基础镜像。不过，目前我们主要是内网开发用，还没有压缩`Docker` image体积的需求，本渣也就不打算重新用`Alpine`折腾一遍了XD

__Update:__

我把一份通用的`Dockerfile`放到了[Github](https://github.com/yszheda/quick-x-apk-docker)上，你也可以在Docker Hub拉取对应的`Docker`镜像：

```
docker pull galoisplusplus/quick-x-apk-docker
```

这一`Docker`镜像对不采用quick-x的cocos2d-x游戏打包也是可以用的，只需要把`Dockerfile`中quick-x的部分去掉后进行构建即可。
