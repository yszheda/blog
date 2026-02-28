Title: cocos2d-x游戏的性能检测
Date: 2015-07-20 11:22:00
description: Profilers for cocos2d-x
Tags: cocos2d-x, CS, tech, cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20150720-profilers-for-cocos2d-x
Category: tech

前段时间本渣负责了一些优化我们cocos2d-x游戏性能方面的工作，在这里做一点记录。

<!-- more -->

# OpenGL指标 #

在debug版的cocos2d-x游戏里，通常会在左下角显示三个指标（当然，是否显示这三个指标是可以配置的）：

- `GL verts`: 绘制的顶点数量

- `GL calls`: 绘制次数

- `FPS`: 帧率

可千万别小看了这三个不起眼的指标，对从它们入手进行分析常常能找到一些性能问题的症结。

`FPS`算是其中最容易理解的指标了，这个值当然是越高越好。根据`FPS`我们可以对性能问题做一些初步判断，确定是在哪个地方开始掉帧。此外，我们往往会碰到卡帧的情况，这时候画面像是突然被冻住了一般，这种情况其实与绘制渲染无关，而是因为在同一帧的计算量过大，CPU成为了瓶颈。针对这个问题就可以去定位计算的部分，对它进行优化或者将它拆到多帧里去做。

`GL calls`和`GL verts`都和绘制渲染有关，不过本渣以前在学校是做GPGPU的，并不觉得这主要是GPU的性能问题，而是数据或命令在CPU和GPU间传输时总线（bus）的问题。当数据量过大时，总线就成为了瓶颈。

先说下`GL calls`，这个值越小越好，合理使用[auto batching]()可以降低这一指标。最近本渣还通过这一指标意外地解决了我们游戏里的几个和`UIListView`相关的问题。这些问题都有一个共同点：滚动列表越滚越卡。本渣为此做了如下测试操作：在滚动列表处于初始位置时记下当前的`GL calls`（比方说记为`x`），在执行了若干次滚动操作后，让滚动列表回到初始位置，记下`GL calls`（比方说记为`y`）。此时前后两者的画面基本一致，绘制的开销应该也是一致的，也就是说`x`和`y`应该相等（当然，如果界面上有动画或者新加入的UI元素的话，可能会有些许偏差），然而有问题的地方`y`总是比`x`大，而且随着滚动操作的增加而增长。这就基本可以确认是没释放资源导致内存泄露了，review了下对应的代码果然如此：quick-cocos2d-x的`UIListView`有所谓的`async`模式，与cocos2d-x的`TableView`相似，并不会产生列表中的所有cells，而只产生显示区域的cells，当滚动产生新的cell时会先重用不在显示区域的cell实例（instance），从而降低开销；而有问题的代码（当然是本渣的队友小伙伴挖的坑啦，哈哈）在重用旧的cell实例时并没有把没用的UI资源释放掉，从而导致了这一问题。虽然我们码农通过代码并不难排查，但是`GL calls`这一指标提供了一种不需要看代码就能定位此类问题的方式，特别适合测试人员采用。

最后说下`GL verts`，这个值也是越低越好。这里顺带提醒下，有些人想要隐藏某些UI元素时会把它们的透明度设为0、或者把它们完全遮挡住，cocos2d-x对于完全透明或者完全被遮挡的`node`还是会做绘制的，这时通过`GL verts`这一指标就可以看出放不放这些“隐藏”UI元素的开销是不同的了。此外还有隐式产生这一问题的情况，例如cocostudio中放入一个带颜色的完全透明的Panel，需要注意避免踩坑（BTW. cocos2d-x对于带颜色的Panel是用`LayerColor`类来处理的，在我们所用的v3.2版本中，这个类的渲染代码还会引起游戏crash！）。当然，要降低`GL verts`还是需要和美术大大沟通好的。例如美术大大绞尽脑汁出了一张很精致的大图，但游戏里用不到那么大，还要缩放成0.3倍，这张图不仅很多细节在手机上完全看不清，而且还增加了`GL verts`开销。要避免这种情况，还是要团队里成员合作好，在美术资源方面要定好合适的大小，控制好图片细节的精细度。

# 性能检测器（Profiler） #

本渣之前玩过`gprof`和CUDA的`nvprof`，深知借助于专业的profiler可以给性能检测带来许多方便，于是前段时间也花了不少精力在找cocos2d-x相关的profiler。

## Android ##

[官方文档](http://www.cocos2d-x.org/wiki/Profiling_Cocos2d-x_with_ARM_DS-5_Streamline)提到ARM的`streamline`工具，但本渣看下来后并没有采用：一者是需要编译内核，对于我们这种小厂，这种可能玩坏测试机的我们还是玩不起的；二者是这篇文档很旧，当时cocos2d-x只有v2，不确定在我们v3.2的版本上是否能跑起来，而且本渣也没查到其他人在cocos2d-x v3.0以上版本试水的资料。

本渣最后用的是`android-ndk-profiler`，这个工具确实能正常运行并产生性能检测报告的。在cocos2d-x项目配置`android-ndk-profiler`基本照着leenjewel大神[这篇文章](http://leenjewel.github.io/blog/2015/04/17/android-ping-tai-yong-gprof-gei-cocos2d-x-zuo-xing-neng-fen-xi/)就可以，因为leenjewel写得很详细，本渣的做法和他差不多，所以这里就不赘述了。`android-ndk-profiler`的输出基本和`gprof`一样，如果你不知道如何分析`gprof`报告的话可以参考[文档](http://www.linuxselfhelp.com/gnu/gprof/html_chapter/gprof_5.html)。
不过`android-ndk-profiler`一个很大的问题是采样：如果采样率太低，收集到的数据可能不具有代表性；但调高采样率往往会导致crash——像本渣就遇到过在游戏刚启动、画面还没出来时就崩溃了orz...这无疑带来了不少麻烦，目前本渣还木有好的解决方案。

另外还有一些大神推荐高通的[Adreno Profiler](https://developer.qualcomm.com/software/adreno-gpu-profiler)，本渣暂时还木有尝试～

## iOS ##

iOS下当然是用强大的`Instruments`啦！不过本渣更熟悉`Instruments`的内存检测工具，之前也曾用`Leaks`解决了一些`C++`代码的内存泄漏问题，在用`Instruments`做性能检测方面暂时没有什么心得～

# Android开发者模式的性能检测工具 #

Android开发者模式里也有许多如检测GPU Overdraw等的工具，可以在做Android真机调试时进行性能检测和分析。当然，如何使用这些工具就不是本渣这里所要讨论的问题了哈～

# 参考资料 #

ARM Streamline:

- [ARM官方文档：Profiling Cocos2d-x Game engine -- DS-5 Streamline case study](https://community.arm.com/groups/tools/blog/2013/12/16/profiling-cocos2d-x-game-engine--ds-5-streamline-case-study)

- [cocos2d-x官方wiki，和ARM的差不多：PROFILING COCOS2D-X WITH ARM DS-5 STREAMLINE](http://www.cocos2d-x.org/wiki/Profiling_Cocos2d-x_with_ARM_DS-5_Streamline)

`android-ndk-prof`：

- [Profiler and profiling on Android NDK](http://discuss.cocos2d-x.org/t/profiler-and-profiling-on-android-ndk/1218)

- [android-ndk-profiler官方文档](https://github.com/richq/android-ndk-profiler/blob/master/docs/Usage.md)

- [Android 平台用 Gprof 给 Cocos2d-x 做性能分析](http://leenjewel.github.io/blog/2015/04/17/android-ping-tai-yong-gprof-gei-cocos2d-x-zuo-xing-neng-fen-xi/)

`Adreno Profiler`：

- [Adreno Profiler分析任意安卓游戏特效+抓取资源](http://qiankanglai.me/2015/05/16/Adreno-Profiler/)

- [使用Adreno Profiler分析android游戏](http://www.cnblogs.com/ghl_carmack/p/5401906.html)

- [高通在极客学院的课程“Adreno Profiler 性能分析工具解析”](http://www.jikexueyuan.com/course/1369.html)

`Instruments`:

- [cocos2d-x官方wiki：HOW TO OPTIMISE MEMORY USAGE](http://www.cocos2d-x.org/wiki/How_to_Optimise_Memory_Usage)

- [Cocos开发中性能优化工具介绍（一）：Xcode中Instruments工具使用](http://www.cocos.com/doc/tutorial/show?id=1837)

- [子龙山人大神的译文：怎样在xcode里面使用Memory Leaks和Instruments教程](http://www.cnblogs.com/andyque/archive/2011/08/08/2131140.html)
