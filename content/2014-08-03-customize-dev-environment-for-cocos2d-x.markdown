Title: Customize Development Environment for cocos2d-x
Date: 2014-08-03 02:13:00
description: Customize Development Environment for cocos2d-x
Tags: cocos2d-x, CS, tech, cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20140803-customize-dev-environment-for-cocos2d-x
Category: tech

本渣不久前答完辩毕了业，很快就入职开始新的搬砖历程——在一个只有四名码农的团队里做cocos2d-x的前端开发——说起来我们还是公司第一个做大型手游和cocos2d-x手游的团队呢！搬砖的第一步自然是配置相关环境啦，这里就来记录一下自己近来在这方面的学习和折腾吧。

# 配置Mac OS X开发及iOS打包环境 #

## 安装`XCode` ##

## 安装命令行工具 ##

- 安装Xcode Command Line Tools：

```
xcode-select --install
```

- 安装OS X下的包管理器[Homebrew](http://brew.sh/)（Mac OS X已自带`ruby`）：

```
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

之后就可以用`brew install`安装`python`、`git`等package 。

# 配置Android打包环境 #

## 安装`Java` ##

在[官网](https://java.com/download)下载安装即可。

## Android sdk ##

由于Google被墙了，要在`Android`官网下载需要翻墙，在以下国内站点下载也可以：

```
# 中国科学院开源协会
http://mirrors.opencas.cn
 
# 腾讯Bugly镜像
http://android-mirror.bugly.qq.com:8080
```

`sdk`下载后，再安装`platform-tools`、`extra-android-support`、`android-20`和`build-tools-20.0.0`。
可以通过`Android SDK Manager`图形界面安装，也可以在`sdk`的`tools`目录下通过命令行安装：

```
./android update sdk --no-ui --all --filter platform-tools
./android update sdk --no-ui --all --filter extra-android-support
./android update sdk --no-ui --all --filter android-20
./android update sdk --no-ui --all --filter build-tools-20.0.0
```

如果要用代理安装可以用：

```
./android update sdk --no-ui --all --filter platform-tools --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s
./android update sdk --no-ui --all --filter extra-android-support --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s
./android update sdk --no-ui --all --filter android-20 --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s
./android update sdk --no-ui --all --filter build-tools-20.0.0 --proxy-host android-mirror.bugly.qq.com --proxy-port 8080 -s
```

### adb ###

在sdk工具中平时开发用得最多的是`adb`，这里把一些`adb`常用命令也记一下：

- 启动adb服务：

```
adb start-server
```

- 关闭adb服务：

```
adb kill-server
```

- 列举Android设备：

```
adb devices
```

- 通过usb连接Android设备：

```
adb usb
```

- 安装apk包：

```
adb install -r <apk>
```

- 卸载应用：

```
adb uninstall <app>
```

可以通过以下命令获取app名字：

```
adb shell pm list packages
```

- 清除应用数据：

```
adb shell pm clear <app>
```

- 查看日志：

```
adb logcat
```

查看cocos2d-x游戏的日志可以用pipe给grep做过滤：

```
adb logcat | grep cocos2d
```

`adb logcat`本身的过滤选项可以查看[官方文档](https://developer.android.com/studio/command-line/logcat.html)。

- 清除日志缓存：

```
adb logcat -c
```

- 进入设备终端：

```
adb shell
```

- 从Android设备拷贝文件到电脑：

```
adb pull <remote> <local>
```

- 从电脑拷贝文件到Android设备：

```
adb push <local> <remote>
```

- 查看GPU渲染数据。在Android设备的“开发者选项”中选择“GPU呈现模式分析（开启在adb shell dumpsys gfxinfo中）”，就可以用以下命令输出某app最后120帧的渲染情况：

```
adb shell dumpsys gfxinfo <app>
```

例如查看Google Calendar的渲染情况：

```
adb shell dumpsys gfxinfo com.google.android.calendar
```

输出：

```
Profile data in ms:

        com.google.android.calendar/com.android.calendar.AllInOneCalendarActivity/android.view.ViewRootImpl@423c4ad0
        Draw    Process Execute
        15.60   3.92    17.66
        54.51   10.14   23.59
        1.59    3.00    1.57
        13.04   13.78   1.54
```

Draw、Process、Execute三项加起来就是一帧渲染的总时间了，接下来可以用sdk的`systrace`工具来做进一步的性能分析，这就不是本文要讨论的话题了。


`adb shell dumpsys`还有其他很多选项（`adb shell service list`里列举的都能用），不过对于cocos2d-x开发来说并不常用：

- 查看CPU使用情况：

```
adb shell dumpsys cpuinfo
```

当然，Android系统也是Linux，所以也可以用：

```
adb shell cat /proc/cpuinfo
```

- 查看内存使用情况：

```
adb shell dumpsys meminfo
```

也可以用：

```
adb shell cat /proc/meminfo
```

还可以针对某个app查看内存占用：

```
adb shell dumpsys meminfo <app>
```

- 查看activity：

```
adb shell dumpsys activity
```

查看window：

```
adb shell dumpsys window
```

- 查看电池使用情况：

```
adb shell dumpsys battery
```

更详细的信息可以用以下命令：

```
adb shell dumpsys batterystats
```

- 查看wifi使用情况：

```
adb shell dumpsys wifi
```

## Android NDK ##

和SDK一样，可以翻墙到`Android`官网或者在国内镜像站点下载。
cocos2d-x对NDK r10的支持有问题，采用NDK r9d。

__Update: 目前cocos2d-x已支持NDK r10。__

### ndk-stack ###

在NDK工具中平时开发用得最多的是`ndk-stack`，主要用来分析crash。

一种是实时分析crash：

```
adb logcat | ndk-stack -sym $PROJECT_PATH/obj/local/armeabi
```

另一种是分析现有的crash dump：

```
ndk-stack -sym $PROJECT_PATH/obj/local/armeabi -dump <dump-file>
```

## 安装`ant` ##

```
brew install ant
```

# cocos2d-x游戏引擎 #

下载[cocos2d-x](https://github.com/cocos2d/cocos2d-x)代码，执行以下命令下载所有代码：

```
git clone https://github.com/cocos2d/cocos2d-x.git
cd cocos2d-x
python download-deps.py
git submodule update --init
```

再执行`setup.py`，这个脚本会在`~/.bash_profile`或`~/.bash_login`或`~/.profile`中设好`COCOS_CONSOLE_ROOT`、`COCOS_X_ROOT`、`COCOS_TEMPLATES_ROOT`、`NDK_ROOT`、`ANDROID_SDK_ROOT`、`ANT_ROOT`等环境变量。之后`source`一下被写入环境变量的文件，就可以用`cocos`命令了。

# <del>IDE?</del> #

本渣一开始用XCode，但XCode实在太慢太卡了，XVim也一点都不好用。作为vim粉，要毛线IDE，果断用vim做为cocos2d-x开发编辑器XD

由于平时主要是写C++，所以本渣主要用了以下的vim插件：

- [a.vim](http://www.vim.org/scripts/script.php?script_id=31)：快速在`.h/.hpp`和`.c/.cpp`之间切换

- [c.vim](http://www.vim.org/scripts/script.php?script_id=213)：针对C/C++的代码片段（code snippet）、热键等综合工具

- [snipmate](http://www.vim.org/scripts/script.php?script_id=2540)：代码片段自动补全

- [clang_complete](http://www.vim.org/scripts/script.php?script_id=3302)：使用强大的`clang`来做C/C++的代码自动补全

- [ag.vim](https://github.com/rking/ag.vim)：想必用过[ag](https://github.com/ggreer/the_silver_searcher)的都非常喜欢它完秒`ack`和`grep`的速度，`ag.vim`就是在vim中用ag进行搜索（其实用`:!ag`也可以哈）。

- [YouCompleteMe](http://valloric.github.io/YouCompleteMe/)：YCM是本渣非常喜欢的神器！不过要在cocos2d-x开发中更好使用YCM需要配置`.ycm_extra_conf.py`文件，本渣写了[一份](https://gist.github.com/yszheda/72401e99c1235d32bcaf)放到项目目录下，对于cocos2d-x项目基本是够用的。


后来本渣在Stackoverflow上看到一个话题[Cocos2d-x C++ development tool (no need to be a full IDE)](http://stackoverflow.com/questions/34573846/cocos2d-x-c-development-tool-no-need-to-be-a-full-ide)，题主希望开发工具能做到：

> auto code complement, class function hint, code formatting and available to see cocos2d-x source code conveniently.

这么简单的需求，vim完全能胜任啊！而且还不需要用以上所有插件，所以本渣写了个酱紫的[回答](http://stackoverflow.com/questions/34573846/cocos2d-x-c-development-tool-no-need-to-be-a-full-ide/35481145#35481145)。

# 参考资料 #

[Android性能－gfxinfo、systrace、traceview](http://qa.blog.163.com/blog/static/190147002201611833520773/)

[Android 性能分析案例](http://blog.chengyunfeng.com/?p=458)


[ndk-stack官方文档](https://developer.android.com/ndk/guides/ndk-stack.html)

[How to check crash log using android ndk in cocos2d-x](http://stackoverflow.com/questions/18436383/how-to-check-crash-log-using-android-ndk-in-cocos2d-x)

[Android NDK开发Crash错误定位](http://blog.csdn.net/xyang81/article/details/42319789)

[[cocos2dx]利用NDK崩溃日志查找BUG](http://blog.bookbook.in/ji-zhu/-cocos2dx-li-yong-ndkbeng-kui-ri-zhi-cha-zhao-bug)

[android使用ndk-stack调试JNI部分的C/C++代码](http://blog.csdn.net/oldmtn/article/details/8889654)


[在macos上设置quickx和cocos2dx的vim开发环境](http://yi.github.io/work/2014/06/20/%E5%9C%A8MacOS%E4%B8%8A%E8%AE%BE%E7%BD%AEquickx%E5%92%8Ccocos2dx%E7%9A%84Vim%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/)
