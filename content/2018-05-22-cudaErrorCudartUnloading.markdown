Title: cudaErrorCudartUnloading问题排查及建议方案
Date: 2018-05-22 22:00:00
description: cudaErrorCudartUnloading
Tags: CUDA, CS, tech, CUDA, GPGPU
Slug: 20180522-cudaErrorCudartUnloading
Category: tech

最近一段时间一直在负责做我厂神经网络前向框架库的优化，前几天接了一个bug report，报错信息大体是这样的：

```
Program hit cudaErrorCudartUnloading (error 29) due to "driver shutting down" on CUDA API call to cudaFreeHost.
```

同样的库链接出来的可执行文件，有的会出现这种问题有的不会，一开始让我很自然以为是使用库的应用程序出了bug。排除了这种可能之后，这句话最后的`cudaFreeHost`又让我想当然地以为是个内存相关的问题，折腾了一阵后才发现方向又双叒叕错了。而且我发现，无论我在报错的那段代码前使用任何CUDA runtime API，都会出现这个错误。
后来在网上查找相关信息，以下的bug report虽然没有具体解决方案，但相似的call stack让我怀疑这和我遇到的是同一个问题，而且也让我把怀疑的目光聚焦在"driver shutting down"而非`cudaFreeHost`上。

* https://github.com/opencv/opencv/issues/7816

* https://github.com/BVLC/caffe/issues/6281

* https://stackoverflow.com/questions/40979060/cudaerrorcudartunloading-error-29-due-to-driver-shutting-down

* https://github.com/NVlabs/SASSI/issues/4

* https://blog.csdn.net/jobbofhe/article/details/79386160

# 强制阻止"driver shutting down"？

首先一个看似理所当然的思路是：我们能否在使用CUDA API时防止CUDA driver不被shutdown呢？问题在于"driver shutting down"究竟指的是什么？如果从`cudaErrorCudartUnloading`的字面意思来讲，很可能是指cuda_runtime的library被卸载了。
由于我们用的是动态链接库，于是我尝试在报错的地方前加上`dlopen`强制加载`libcuda_runtime.so`。改完后马上发现不对，如果是动态库被卸载，理应是调用CUDA API时发现相关symbol都没有定义才对，而不应该是可以正常调用动态库的函数、然后返回error code这样的runtime error现象。
此外，我通过`strace`发现，还有诸如`libcuda.so`、`libnvidia-fatbinaryloader.so`之类的动态库会被加载，都要试一遍并不现实。何况和CUDA相关的动态库并不少（可参考[《NVIDIA Accelerated Linux Graphics Driver README and Installation Guide》中的“Chapter 5. Listing of Installed Components”](http://us.download.nvidia.com/XFree86/Linux-x86/367.35/README/installedcomponents.html)），不同的程序依赖的动态库也不尽相同，上述做法即使可行，也很难通用。

无独有偶，在nvidia开发者论坛上也有开发者有[类似的想法](https://devtalk.nvidia.com/default/topic/1019780/?comment=5191690)，被官方人士否定了：

> For instance, can I have my class maintain certain variables/handles that will force cuda run time library to stay loaded.
>
> No. It is a bad design practice to put calls to the CUDA runtime API in constructors that may run before main and destructors that may run after main.

# 如何使CUDA runtime API正常运作？

对于CUDA应用程序开发者而言，我们通常是通过调用CUDA runtime API来向GPU设备下达我们的指令。所以首先让我们来看，在程序中调用CUDA runtime API时，有什么角色参与了进来。我从[Nicholas Wilt的《The CUDA Handbook》](http://www.cudahandbook.com/)中借了一张图：

![image](/images/cudaErrorCudartUnloading/CUDA-software-layers.png)

我们可以看到，主要的角色有：运行在操作系统的User Mode下的CUDART(CUDA Runtime) library（对于动态库来说就是上文提到的`libcuda_runtime.so`）和CUDA driver library（对于动态库来说就是上文提到的`libcuda.so`），还有运行在Kernel Mode下的CUDA driver内核模块。众所周知，我们的CUDA应用程序是运行在操作系统的User Mode下的，无法直接操作GPU硬件，在操作系统中有权控制GPU硬件的是运行在Kernel Mode下的内核模块（OT一下，作为CUDA使用者，我们很少能感觉到这些内核模块的存在，也它们许最有存在感的时候就是我们遇上`Driver/library version mismatch`错误了XD）。在Linux下我们可以通过`lsmod | grep nvidia`来查看这些内核模块，通常有管理Unified Memory的`nvidia_uvm`、Linux内核[Direct Rendering Manager](https://dri.freedesktop.org/wiki/DRM/)显示驱动`nvidia_drm`、还有`nvidia_modeset`。与这些内核模块沟通的是运行在User Mode下的CUDA driver library，我们所调用的CUDA runtime API会被CUDART library转换成一系列CUDA driver API，交由CUDA driver library这个连接CUDA内核模块与其他运行在User Mode下CUDA library的中介。

那么，要使CUDA runtime API所表示的指令能被正常传达到GPU，就需要上述角色都能通力协作了。这就自然引发一个问题：在我们的程序运行的时候，这些角色什么时候开始/结束工作？它们什么时候被初始化？我们不妨`strace`看一下CUDA应用程序的系统调用：
首先，`libcuda_runtime.so`、`libcuda.so`、`libnvidia-fatbinaryloader.so`等动态库被加载。当前被加载进内核的内核模块列表文件`/proc/modules`被读取，由于`nvidia_uvm`、`nvidia_drm`等模块之前已被加载，所以不需要额外`insmod`。接下来，设备参数文件`/proc/driver/nvidia/params`被读取，相关的设备——如`/dev/nvidia0`（GPU卡0）、`/dev/nvidia-uvm`（看名字自然与Unified Memory有关，可能是Pascal体系Nvidia GPU的Page Migration Engine）、`/dev/nvidiactl`等——被打开，并通过`ioctl`初始化设定。（此外，还有home目录下`~/.nv/ComputeCache`的一些文件被使用，这个目录是用来缓存PTX伪汇编JIT编译后的二进制文件fat binaries，与我们当前的问题无关，感兴趣的朋友可参考[Mark Harris的《CUDA Pro Tip: Understand Fat Binaries and JIT Caching》](https://devblogs.nvidia.com/cuda-pro-tip-understand-fat-binaries-jit-caching/)。）要使CUDA runtime API能被正常执行，需要完成上述动态库的加载、内核模块的加载和GPU设备设置。

但以上还只是从系统调用角度来探究的一个必要条件，还有一个条件写过CUDA的朋友应该不陌生，那就是CUDA context（如果你没印象了，可以回顾一下CUDA官方指南中讲[初始化](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#initialization)和[context](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#context)的部分）。我们都知道：所有CUDA的资源（包括分配的内存、CUDA event等等）和操作都只在CUDA context内有效；在第一次调用CUDA runtime API时，如果当前设备没有创建CUDA context，新的context会被创建出来作为当前设备的primary context。这些操作对于CUDA runtime API使用者来说是不透明的，那么又是谁做的呢？让我来引用一下[SOF上某个问题下](https://stackoverflow.com/questions/35815597/cuda-call-fails-in-destructor)community wiki的标准答案：

> The CUDA front end invoked by nvcc silently adds a lot of boilerplate code and translation unit scope objects which perform CUDA context setup and teardown. That code must run before any API calls which rely on a CUDA context can be executed. If your object containing CUDA runtime API calls in its destructor invokes the API after the context is torn down, your code may fail with a runtime error.

这段话提供了几个信息：一是`nvcc`插入了一些代码来完成的CUDA context的创建和销毁所需要做的准备工作，二是CUDA context销毁之后再调用CUDA runtime API就可能会出现runtime error这样的未定义行为（Undefined Behaviour，简称UB）。

接下来让我们来稍微深入地探究一下。我们有若干`.cu`文件通过`nvcc`编译后产生的`.o`文件，还有这些`.o`文件链接后生成的可执行文件`exe`。我们通过`nm`等工具去查看这些`.o`文件，不难发现这些文件的代码段中都被插入了一个以`__sti____cudaRegisterAll_`为名字前缀的函数。我们在`gdb <exe>`中对其中函数设置断点再单步调试，可以看到类似这样的call stack：

```
(gdb) bt
#0  0x00002aaab16695c0 in __cudaRegisterFatBinary () at /usr/local/cuda/lib64/libcudart.so.8.0
#1  0x00002aaaaad3eee1 in __sti____cudaRegisterAll_53_tmpxft_000017c3_00000000_19_im2col_compute_61_cpp1_ii_a0760701() ()
    at /tmp/tmpxft_000017c3_00000000-4_im2col.compute_61.cudafe1.stub.c:98
#2  0x00002aaaaaaba3a3 in _dl_init_internal () at /lib64/ld-linux-x86-64.so.2
#3  0x00002aaaaaaac46a in _dl_start_user () at /lib64/ld-linux-x86-64.so.2
#4  0x0000000000000001 in  ()
#5  0x00007fffffffe2a8 in  ()
#6  0x0000000000000000 in  ()
```

再执行若干步，call stack就变成：

```
(gdb) bt
#0  0x00002aaab16692b0 in __cudaRegisterFunction () at /usr/local/cuda/lib64/libcudart.so.8.0
#1  0x00002aaaaad3ef3e in __sti____cudaRegisterAll_53_tmpxft_000017c3_00000000_19_im2col_compute_61_cpp1_ii_a0760701() (__T263=0x7c4b30)
    at /tmp/tmpxft_000017c3_00000000-4_im2col.compute_61.cudafe1.stub.c:97
#2  0x00002aaaaad3ef3e in __sti____cudaRegisterAll_53_tmpxft_000017c3_00000000_19_im2col_compute_61_cpp1_ii_a0760701() ()
    at /tmp/tmpxft_000017c3_00000000-4_im2col.compute_61.cudafe1.stub.c:98
#3  0x00002aaaaaaba3a3 in _dl_init_internal () at /lib64/ld-linux-x86-64.so.2
#4  0x00002aaaaaaac46a in _dl_start_user () at /lib64/ld-linux-x86-64.so.2
#5  0x0000000000000001 in  ()
#6  0x00007fffffffe2a8 in  ()
#7  0x0000000000000000 in  ()
```


```
(gdb) bt
#0  0x00002aaaaae8ea20 in atexit () at XXX.so
#1  0x00002aaaaaaba3a3 in _dl_init_internal () at /lib64/ld-linux-x86-64.so.2
#2  0x00002aaaaaaac46a in _dl_start_user () at /lib64/ld-linux-x86-64.so.2
#3  0x0000000000000001 in  ()
#4  0x00007fffffffe2a8 in  ()
#5  0x0000000000000000 in  ()
```


那么CUDA context何时被创建完成呢？通过对`cuInit`设置断点可以发现，与官方指南的描述一致，也就是在进入`main`函数之后调用第一个CUDA runtime API的时候：

```
(gdb) bt
#0  0x00002aaab1ab7440 in cuInit () at /lib64/libcuda.so.1
#1  0x00002aaab167add5 in  () at /usr/local/cuda/lib64/libcudart.so.8.0
#2  0x00002aaab167ae31 in  () at /usr/local/cuda/lib64/libcudart.so.8.0
#3  0x00002aaabe416bb0 in pthread_once () at /lib64/libpthread.so.0
#4  0x00002aaab16ad919 in  () at /usr/local/cuda/lib64/libcudart.so.8.0
#5  0x00002aaab167700a in  () at /usr/local/cuda/lib64/libcudart.so.8.0
#6  0x00002aaab167aceb in  () at /usr/local/cuda/lib64/libcudart.so.8.0
#7  0x00002aaab16a000a in cudaGetDevice () at /usr/local/cuda/lib64/libcudart.so.8.0
...
#10 0x0000000000405d77 in main(int, char**) (argc=<optimized out>, argv=<optimized out>)
```


其中，和context创建相关的若干函数就在`${CUDA_PATH}/include/crt/host_runtime.h`中声明过：

```cpp
#define __cudaRegisterBinary(X)                                                   \
        __cudaFatCubinHandle = __cudaRegisterFatBinary((void*)&__fatDeviceText); \
        { void (*callback_fp)(void **) =  (void (*)(void **))(X); (*callback_fp)(__cudaFatCubinHandle); }\
        atexit(__cudaUnregisterBinaryUtil)
       

extern "C" {
extern void** CUDARTAPI __cudaRegisterFatBinary(
  void *fatCubin
);

extern void CUDARTAPI __cudaUnregisterFatBinary(
  void **fatCubinHandle
);

extern void CUDARTAPI __cudaRegisterFunction(
        void   **fatCubinHandle,
  const char    *hostFun,
        char    *deviceFun,
  const char    *deviceName,
        int      thread_limit,
        uint3   *tid,
        uint3   *bid,
        dim3    *bDim,
        dim3    *gDim,
        int     *wSize
);
}

static void **__cudaFatCubinHandle;

static void __cdecl __cudaUnregisterBinaryUtil(void)
{
  ____nv_dummy_param_ref((void *)&__cudaFatCubinHandle);
  __cudaUnregisterFatBinary(__cudaFatCubinHandle);
}
```

但这些函数都没有文档，[Yong Li博士写的《GPGPU-SIM Code Study》](http://people.cs.pitt.edu/~yongli/notes/gpgpu/GPGPUSIMNotes.html)稍微详细一些，我就直接贴过来了：

> The simplest way to look at how nvcc compiles the ECS (Execution Configuration Syntax) and manages kernel code is to use nvcc’s `--cuda` switch. This generates a .cu.c file that can be compiled and linked without any support from NVIDIA proprietary tools. It can be thought of as CUDA source files in open source C. Inspection of this file verified how the ECS is managed, and showed how kernel code was managed.
>
> 1. Device code is embedded as a fat binary object in the executable’s `.rodata` section. It has variable length depending on the kernel code.
>
> 2. For each kernel, a host function with the same name as the kernel is added to the source code.
>
> 3. Before `main(..)` is called, a function called `cudaRegisterAll(..)` performs the following work:
>
> • Calls a registration function, `cudaRegisterFatBinary(..)`, with a void pointer to the fat binary data. This is where we can access the kernel code directly.
>
> • For each kernel in the source file, a device function registration function, `cudaRegisterFunction(..)`, is called. With the list of parameters is a pointer to the function mentioned in step 2.
>
> 4. As aforementioned, each ECS is replaced with the following function calls from the execution management category of the CUDA runtime API.
>
> • `cudaConfigureCall(..)` is called once to set up the launch configuration.
>
> • The function from the second step is called. This calls another function, in which, `cudaSetupArgument(..)` is called once for each kernel parameter. Then, `cudaLaunch(..)` launches the kernel with a pointer to the function from the second step.
>
> 5. An unregister function, `cudaUnregisterBinaryUtil(..)`, is called with a handle to the fatbin data on program exit.

其中，`cudaConfigureCall`、`cudaSetupArgument`、`cudaLaunch`在CUDA7.5以后已经“过气”（deprecated）了，由于这些并不是在进入`main`函数之前会被调用的API，我们可以不用管。我们需要关注的是，在`main`函数被调用之前，`nvcc`加入的内部初始化代码做了以下几件事情（我们可以结合上面`host_runtime.h`头文件暴露出的接口和相关call stack来确认）：

1. 通过`__cudaRegisterFatBinary`注册fat binary入口函数。这是CUDA context创建的准备工作之一，如果在`__cudaRegisterFatBinary`执行之前调用CUDA runtime API很可能也会出现UB。SOF上就有这样一个问题，题主在`static`对象构造函数中调用了kernel函数，结果就出现了"invalid device function"错误，SOF上的[CUDA大神talonmies的答案](https://stackoverflow.com/questions/24869167/trouble-launching-cuda-kernels-from-static-initialization-code/24883665#24883665)就探究了`static`对象构造函数和`__cudaRegisterFatBinary`的调用顺序及其产生的问题，非常推荐一读。
2. 通过`__cudaRegisterFunction`注册每个device的kernel函数
3. 通过`atexit`注册`__cudaUnregisterBinaryUtil`的注销函数。这个函数是CUDA context销毁的清理工作之一，前面提到，CUDA context销毁之后CUDA runtime API就很可能无法再被正常使用了，换言之，如果CUDA runtime API在`__cudaUnregisterBinaryUtil`执行完后被调用就有可能是UB。而`__cudaUnregisterBinaryUtil`在什么时候被调用又是符合[`atexit`](http://en.cppreference.com/w/cpp/utility/program/atexit)规则的——在`main`函数执行完后程序`exit`的某阶段被调用（`main`函数的执行过程可以参考[这篇文章](http://umumble.com/blogs/development/the-thorny-path-of-hello-world/)）——这也是我们理解和解决`cudaErrorCudartUnloading`问题的关键之处。

![image](/images/cudaErrorCudartUnloading/main-procedure.png)

# 一切皆全局对象之过

吃透本码渣上述啰里啰唆的理论后，再通过代码来排查`cudaErrorCudartUnloading`问题就简单了。原来，竟和之前提过的[SOF上的问题](https://stackoverflow.com/questions/35815597/cuda-call-fails-in-destructor)相似，我们代码中也使用了一个全局`static` singleton对象，在singleton对象的析构函数中调用CUDA runtime API来执行释放内存等操作。而我们知道，`static`对象是在`main`函数执行完后`exit`进行析构的，而之前提到`__cudaUnregisterBinaryUtil`也是在这个阶段被调用，这两者的顺序是未定义的。如果`__cudaUnregisterBinaryUtil`等清理context的操作在`static`对象析构之前就调用了，就会产生`cudaErrorCudartUnloading`报错。这种UB也解释了，为何之前我们的库链接出来的不同可执行文件，有的会出现这个问题而有的不会。


# 解决方案

在github上搜`cudaErrorCudartUnloading`相关的patch，处理方式也是五花八门，这里姑且列举几种。

## 跳过`cudaErrorCudartUnloading`检查

比如[arrayfire项目的这个patch](https://github.com/arrayfire/arrayfire/pull/170)。可以，这很佛系（滑稽）

```cpp
-    CUDA_CHECK(cudaFree(ptr));
+    cudaError_t err = cudaFree(ptr);
+    if (err != cudaErrorCudartUnloading) // see issue #167
+        CUDA_CHECK(err);
```

## 干脆把可能会有`cudaErrorCudartUnloading`的CUDA runtime API去掉

比如kaldi项目的[这个issue](https://github.com/kaldi-asr/kaldi/issues/2178)和[PR](https://github.com/kaldi-asr/kaldi/pull/2185)。论佛系，谁都不服就服你（滑稽）

## 把CUDA runtime API放到一个独立的de-initialisation、finalize之类的接口，让用户在`main`函数`return`前调用

比如MXNet项目的`MXNotifyShutdown`（参见：[c_api.cc](https://github.com/apache/incubator-mxnet/blob/master/src/c_api/c_api.cc)）。佛系了辣么久总算看到了一种符合本程序员审美的“优雅”方案（滑稽）

恰好在SOF另一个问题中，talonmies大神（啊哈，又是talonmies大神！）在[留言](https://stackoverflow.com/questions/16979982/cuda-streams-destruction-and-cudadevicereset/16982503?noredirect=1#comment24536013_16982503)里也表达了一样的意思，不能赞同更多啊：

> The obvious answer is don't put CUDA API calls in the destructor. In your class you have an explicit intialisation method not called through the constructor, so why not have an explicit de-initialisation method as well? That way scope becomes a non-issue

上面的方案虽然“优雅”，但对于库维护者却有多了一层隐忧：万一加了个接口，使用者要撕逼呢？（滑稽）万一使用者根本就不鸟你，没在`main`函数`return`前调用呢？要说别人打开方式不对，人家还可以说是库的实现不够稳健把你批判一通呢。如果你也有这种隐忧，请接着看接下来的“黑科技”。

## 土法黑科技（滑稽）

首先，CUDA runtime API还是不能放在全局对象析构函数中，那么应该放在什么地方才合适呢？毕竟我们不知道库使用者最后用的是哪个API啊？不过，我们却可以知道库使用者使用什么API时是在`main`函数的作用域，那个时候是可以创建有效的CUDA context、正常使用CUDA runtime API的。这又和我们析构函数中调用的CUDA runtime API有什么关系呢？你可能还记得吧，前边提到`nvcc`加入的内部初始化代码通过`atexit`注册`__cudaUnregisterBinaryUtil`的注销函数，我们自然也可以如法炮制：

```cpp
// 首先调用一个“无害”的CUDA runtime API，确保在调用`atexit`之前CUDA context已被创建
// 这样就确保我们通过`atexit`注册的函数在CUDA context相关的销毁函数（例如`__cudaUnregisterBinaryUtil`）之前就被执行
// “无害”的CUDA runtime API？这里指不会造成影响内存占用等副作用的函数，我采用了`cudaGetDeviceCount`
// 《The CUDA Handbook》中推荐使用`cudaFree(0);`来完成CUDART初始化CUDA context的过程，这也是可以的
int gpu_num;
cudaError_t err = cudaGetDeviceCount(&gpu_num);

std::atexit([](){
    // 调用原来在全局对象析构函数中的CUDA runtime API
});
```

那么，应该在哪个地方插入上面的代码呢？解铃还须系铃人，我们的`cudaErrorCudartUnloading`问题出在`static` singleton对象身上，但以下singleton的惰性初始化却也给了我们提供了一个绝佳的入口：

```cpp
// OT一下，和本中老年人一样上了年纪的朋友可能知道
// 以前在C++中要实现线程安全的singleton有多蛋疼
// 有诸如Double-Checked Locking之类略恶心的写法
// 但自打用了C++11之后啊，腰不酸了,背不疼了,腿啊也不抽筋了,码代码也有劲儿了（滑稽）
// 以下实现在C++11标准中是保证线程安全的
static Singleton& instance()
{
     static Singleton s;
     return s;
}
```

因为库使用者只会在`main`函数中通过这个接口使用singleton对象，所以只要在这个接口初始化CUDA context并用`atexit`注册清理函数就可以辣！当然，作为一位严谨的库作者，你也许会问：不能对库使用者抱任何幻想，万一别人在某个全局变量初始化时调用了呢？Bingo！我只能说目前我们的业务流程可以让库使用者不会想这么写来恶心自己而已...（捂脸）万一真的有这么作的使用者，这种方法就失效了，使用者会遇到和[前面提到的SOF某问题](https://stackoverflow.com/questions/24869167/trouble-launching-cuda-kernels-from-static-initialization-code)相似的报错。毕竟，黑科技也不是万能的啊！


# 后记

解决完`cudaErrorCudartUnloading`这个问题之后，又接到新的救火任务，排查一个使用加密狗API导致的程序闪退问题。加密狗和`cudaErrorCudartUnloading`两个问题看似风马牛不相及，本质竟然也是相似的：又是一样的UB现象；又是全局对象；又是在全局对象构造和析构时调用了加密狗API，和加密狗内部的初始化和销毁函数的执行顺序未定义。看来，不乱挖坑还是要有基本的常识——在使用外设设备相关的接口时，要保证在`main`函数的作用域里啊！

# 参考资料
* [《CUDA官方指南》](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
* [Nicholas Wilt的《The CUDA Handbook》](http://www.cudahandbook.com/)
* [《NVIDIA Accelerated Linux Graphics Driver README and Installation Guide》中的“Chapter 5. Listing of Installed Components”](http://us.download.nvidia.com/XFree86/Linux-x86/367.35/README/installedcomponents.html)
* [CUDA Pro Tip: Understand Fat Binaries and JIT Caching](https://devblogs.nvidia.com/cuda-pro-tip-understand-fat-binaries-jit-caching/)
* [Yong Li博士写的《GPGPU-SIM Code Study》](http://people.cs.pitt.edu/~yongli/notes/gpgpu/GPGPUSIMNotes.html)
* [The thorny path of Hello World](http://umumble.com/blogs/development/the-thorny-path-of-hello-world/)