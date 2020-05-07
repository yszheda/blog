---
layout: post
title: "ARM NEON编程初探——一个简单的BGR888转YUV444实例详解"
date: 2017-06-10 13:00
comments: true
published: true
categories: [CS, tech]
keywords: ARM, NEON, assembly
description: Use ARM NEON to Accelerate BGR888ToYUV444
---

最近在学习ARM的SIMD指令集[NEON](https://developer.arm.com/technologies/neon)，发现这方面的资料真是太少了，我便来给NEON凑凑人气，姑且以这篇入门文章来分享一些心得吧。

学习一门新技术，总是有一些经典是绕不开的，对于NEON来说，这份必备的武林秘籍自然就是ARM官方的《NEON Programmer's Guide》（以下简称Guide）啦。别看这份Guide有四百多页，其实只有一百来页是正文，后面都是供查阅的手册，通读一番还是不难的。所以这里我也就不打算把Guide里的内容翻译过来敷衍了事了。在此我想借一个简单例子，展示我是如何把一个没采用NEON的普通程序改写为NEON程序、中间又是如何debug、如何调优的。当然，作为一枚ARM小白，我接触NEON指令集毕竟也才两周左右时间，错误在所难免，还请各位方家多多指正。

<!-- more -->

# BGR888ToYUV444

在众多并行操作模式（Map, Reduce, Scatter, Stencil等）中，最简单的也许要算Map了，所以我选了一个Map的例子——BGR888转YUV444。这两者都是颜色空间的格式：前者表示一个像素有B、G、R三个颜色通道，每个通道占8-bit，在内存中按照`B G R`的顺序从高位到低位排列；后者表示一个像素有Y、U、V三个通道，每个通道也是8-bit（444仅指Y、U、V的采样率比值为4:4:4，其他类型的采样率还有YUV422、YUV420），我们也假设它在内存中按照`V U Y`的顺序从高位到低位排列。如何把BGR888格式转成YUV444呢？根据[wiki](https://en.wikipedia.org/wiki/YUV)上的转换公式，我们可以写出如下代码（很显然，这是一一对应，典型的Map模式）：

```c
void BGR888ToYUV444(unsigned char *yuv, unsigned char *bgr, int pixel_num)
{
    int i;
    for (i = 0; i < pixel_num; ++i) {
        uint8_t r = bgr[i * 3];
        uint8_t g = bgr[i * 3 + 1];
        uint8_t b = bgr[i * 3 + 2];

        uint8_t y = 0.299 * r + 0.587 * g + 0.114 * b;
        uint8_t u = -0.169 * r - 0.331 * g + 0.5 * b + 128;
        uint8_t v = 0.5 * r - 0.419 * g - 0.081 * b + 128;

        yuv[i * 3] = y;
        yuv[i * 3 + 1] = u;
        yuv[i * 3 + 2] = v;
    }
}
```

这段代码的意思很简单，我们遍历所有像素，每次把B、G、R三个通道的值从内存中加载进来，再做浮点数乘法和加减法，得到Y、U、V的值，写入相应的内存中。那么，使用NEON可以怎样帮助这段程序跑得更快呢？

前面提到，NEON是一种SIMD（Single Instruction Multiple Data）指令，也就是说，NEON可以把若干源（source）操作数（operand）打包放到一个源寄存器中，对他们执行相同的操作，产生若干目的（dest）操作数，这种方式也叫向量化（vectorization）。这样的话，能打包多少数据同时做运算就取决于寄存器位宽，在ARMv7的NEON unit中，register file总大小是1024-bit，可以划分为16个128-bit的Q-register（Quadword register）或者32个64-bit的D-register（Dualword register），也就是说，最长的寄存器位宽是128-bit（详见Guide第一章）。以上面的R888ToYUV444函数为例，假设我们采用32-bit单精度浮点数float来做浮点运算，那么我们可以 把最多`128/32=4`个浮点数打包放到Q-register中做SIMD运算，一次拿4个BGR算出4个YUV，从而提高吞吐量，减少loop次数。

（细心的看官可能会问到双精度浮点数double的运算吧？遗憾的是，根据Guide，NEON并不支持double，你可以考虑使用[VFP/Vector Floating Point](https://en.wikipedia.org/wiki/ARM_architecture#VFP)，但[VFP并非SIMD单元](https://stackoverflow.com/questions/4097034/arm-cortex-a8-whats-the-difference-between-vfp-and-neon)）。

# 从浮点运算到整型运算

那么，我们还可以继续提高向量化程度吗？如果我们回头看[wiki](https://en.wikipedia.org/wiki/YUV)，我们会发现在早期不支持浮点操作的SIMD处理器中，使用了如下整型运算来把BGR转成YUV：

```c
// Refer to: https://en.wikipedia.org/wiki/YUV (Full swing for BT.601)
void BGR888ToYUV444(unsigned char *yuv, unsigned char *bgr, int pixel_num)
{
    int i;
    for (i = 0; i < pixel_num; ++i) {
        uint8_t r = bgr[i * 3];
        uint8_t g = bgr[i * 3 + 1];
        uint8_t b = bgr[i * 3 + 2];

        // 1. Multiply transform matrix (Y′: unsigned, U/V: signed)
        uint16_t y_tmp = 76 * r + 150 * g + 29 * b;
        int16_t u_tmp = -43 * r - 84 * g + 127 * b;
        int16_t v_tmp = 127 * r - 106 * g - 21 * b;

        // 2. Scale down (">>8") to 8-bit values with rounding ("+128") (Y′: unsigned, U/V: signed)
        y_tmp = (y_tmp + 128) >> 8;
        u_tmp = (u_tmp + 128) >> 8;
        v_tmp = (v_tmp + 128) >> 8;

        // 3. Add an offset to the values to eliminate any negative values (all results are 8-bit unsigned)
        yuv[i * 3] = (uint8_t) y_tmp;
        yuv[i * 3 + 1] = (uint8_t) (u_tmp + 128);
        yuv[i * 3 + 2] = (uint8_t) (v_tmp + 128);
    }
}
```

从这段代码我们不难发现，32-bit的float运算被16-bit的加减、乘法和移位运算所代替。这样的话，我们可以把最多`128/16=8`个整型数放到Q-register中做SIMD运算，一次拿8个BGR算出8个YUV，把向量化程度再提一倍。使用整型运算还有一个好处：一般而言，整型运算指令所需要的时钟周期少于浮点运算的时钟周期。所以，我以这段代码为基准（baseline），用NEON来加速它。（细心的看官也许已经看到我说法中的纰漏：虽然单个整型指令的周期小于单个相同运算的浮点指令的周期，但整型版本的BGR888ToYUV444比起浮点版本的多了移位和加法的overhead，指令数目是不同的，总的时钟周期不一定就短。Good point! 看官不妨看完本文后也用NEON改写浮点版本练练手，两相比较就不难得出最终的结论啦XD）

# NEON Intrinsics

接下来可以着手写NEON代码了。个人推荐新手先别急着一上来就写汇编，NEON提供了intrinsics，其实就是一套可在C/C++中调用的函数API，编译器会代劳把这些intrinsics转成NEON指令（详见Guide的第四章），这样就方便一些。我用NEON intrinsics改写的`BGR888ToYUV444`函数如下：

```c
void BGR888ToYUV444(unsigned char * __restrict__ yuv, unsigned char * __restrict__ bgr, int pixel_num)
{
    const uint8x8_t u8_zero = vdup_n_u8(0);
    const uint16x8_t u16_rounding = vdupq_n_u16(128);
    const int16x8_t s16_rounding = vdupq_n_s16(128);
    const int8x16_t s8_rounding = vdupq_n_s8(128);

    int count = pixel_num / 16;

    int i;
    for (i = 0; i < count; ++i) {
        // Load bgr
        uint8x16x3_t pixel_bgr = vld3q_u8(bgr);

        uint8x8_t high_r = vget_high_u8(pixel_bgr.val[0]);
        uint8x8_t low_r = vget_low_u8(pixel_bgr.val[0]);
        uint8x8_t high_g = vget_high_u8(pixel_bgr.val[1]);
        uint8x8_t low_g = vget_low_u8(pixel_bgr.val[1]);
        uint8x8_t high_b = vget_high_u8(pixel_bgr.val[2]);
        uint8x8_t low_b = vget_low_u8(pixel_bgr.val[2]);
        int16x8_t signed_high_r = vreinterpretq_s16_u16(vaddl_u8(high_r, u8_zero));
        int16x8_t signed_low_r = vreinterpretq_s16_u16(vaddl_u8(low_r, u8_zero));
        int16x8_t signed_high_g = vreinterpretq_s16_u16(vaddl_u8(high_g, u8_zero));
        int16x8_t signed_low_g = vreinterpretq_s16_u16(vaddl_u8(low_g, u8_zero));
        int16x8_t signed_high_b = vreinterpretq_s16_u16(vaddl_u8(high_b, u8_zero));
        int16x8_t signed_low_b = vreinterpretq_s16_u16(vaddl_u8(low_b, u8_zero));

        // NOTE:
        // declaration may not appear after executable statement in block
        uint16x8_t high_y;
        uint16x8_t low_y;
        uint8x8_t scalar = vdup_n_u8(76);
        int16x8_t high_u;
        int16x8_t low_u;
        int16x8_t signed_scalar = vdupq_n_s16(-43);
        int16x8_t high_v;
        int16x8_t low_v;
        uint8x16x3_t pixel_yuv;
        int8x16_t u;
        int8x16_t v;

        // 1. Multiply transform matrix (Y′: unsigned, U/V: signed)
        high_y = vmull_u8(high_r, scalar);
        low_y = vmull_u8(low_r, scalar);

        high_u = vmulq_s16(signed_high_r, signed_scalar);
        low_u = vmulq_s16(signed_low_r, signed_scalar);

        signed_scalar = vdupq_n_s16(127);
        high_v = vmulq_s16(signed_high_r, signed_scalar);
        low_v = vmulq_s16(signed_low_r, signed_scalar);

        scalar = vdup_n_u8(150);
        high_y = vmlal_u8(high_y, high_g, scalar);
        low_y = vmlal_u8(low_y, low_g, scalar);

        signed_scalar = vdupq_n_s16(-84);
        high_u = vmlaq_s16(high_u, signed_high_g, signed_scalar);
        low_u = vmlaq_s16(low_u, signed_low_g, signed_scalar);

        signed_scalar = vdupq_n_s16(-106);
        high_v = vmlaq_s16(high_v, signed_high_g, signed_scalar);
        low_v = vmlaq_s16(low_v, signed_low_g, signed_scalar);

        scalar = vdup_n_u8(29);
        high_y = vmlal_u8(high_y, high_b, scalar);
        low_y = vmlal_u8(low_y, low_b, scalar);

        signed_scalar = vdupq_n_s16(127);
        high_u = vmlaq_s16(high_u, signed_high_b, signed_scalar);
        low_u = vmlaq_s16(low_u, signed_low_b, signed_scalar);

        signed_scalar = vdupq_n_s16(-21);
        high_v = vmlaq_s16(high_v, signed_high_b, signed_scalar);
        low_v = vmlaq_s16(low_v, signed_low_b, signed_scalar);

        // 2. Scale down (">>8") to 8-bit values with rounding ("+128") (Y′: unsigned, U/V: signed)
        // 3. Add an offset to the values to eliminate any negative values (all results are 8-bit unsigned)

        high_y = vaddq_u16(high_y, u16_rounding);
        low_y = vaddq_u16(low_y, u16_rounding);

        high_u = vaddq_s16(high_u, s16_rounding);
        low_u = vaddq_s16(low_u, s16_rounding);

        high_v = vaddq_s16(high_v, s16_rounding);
        low_v = vaddq_s16(low_v, s16_rounding);

        pixel_yuv.val[0] = vcombine_u8(vqshrn_n_u16(low_y, 8), vqshrn_n_u16(high_y, 8));

        u = vcombine_s8(vqshrn_n_s16(low_u, 8), vqshrn_n_s16(high_u, 8));

        v = vcombine_s8(vqshrn_n_s16(low_v, 8), vqshrn_n_s16(high_v, 8));

        u = vaddq_s8(u, s8_rounding);
        pixel_yuv.val[1] = vreinterpretq_u8_s8(u);

        v = vaddq_s8(v, s8_rounding);
        pixel_yuv.val[2] = vreinterpretq_u8_s8(v);

        // Store
        vst3q_u8(yuv, pixel_yuv);

        bgr += 3 * 16;
        yuv += 3 * 16;
    }

    // Handle leftovers
    for (i = count * 16; i < pixel_num; ++i) {
        uint8_t r = bgr[i * 3];
        uint8_t g = bgr[i * 3 + 1];
        uint8_t b = bgr[i * 3 + 2];

        uint16_t y_tmp = 76 * r + 150 * g + 29 * b;
        int16_t u_tmp = -43 * r - 84 * g + 127 * b;
        int16_t v_tmp = 127 * r - 106 * g - 21 * b;

        y_tmp = (y_tmp + 128) >> 8;
        u_tmp = (u_tmp + 128) >> 8;
        v_tmp = (v_tmp + 128) >> 8;

        yuv[i * 3] = (uint8_t) y_tmp;
        yuv[i * 3 + 1] = (uint8_t) (u_tmp + 128);
        yuv[i * 3 + 2] = (uint8_t) (v_tmp + 128);
    }
}
```

这个函数中大部分都是很常用的NEON intrinsics，看官不妨结合查阅Guide的附录D自行熟悉，这里我仅针对几个点解释一下：

* 我用`vld3q_u8`指令从内存一次加载16个像素（也就是`uint8_t`类型的B、G、R三个通道的数值），将各个通道的16个数值放到一个Q-register中（也就是用了三个Q-register，每个分别存放16个B、16个G和16个R），`vst3q_u8`的写入操作也是类似的，这充分利用128-bit的带宽，使内存存取（memory access）的次数尽可能少。但是，后边运算的向量化程度其实仍然不变，只能同时进行8个16-bit整型运算，也就是说，对于运算的部分，理想加速比（speedup）是8而非16。（当然，一次从内存加载多少数据是一个design choice，没有绝对的答案，看官也可以尝试别的方式XD）

* 对于像素个数不能被16整除的情况，可能会有剩下的1到15个像素没被上述NEON代码处理到，这里我把它们称作leftovers，简单粗暴地跑了之前的for循环。其实leftover的情况如果占比高的话，还有更高明的处理方式，请各位看官参见Guide的6.2 Handling non-multiple array lengths一节。

* 我把Y通道计算的一部分放到一起，稍作解释，其他的很多运算都是类似的：

```c
// 复制8个值为128的uint16_t类型整数到某个Q-register，该Q-register对应的C变量是u16_rounding
const uint16x8_t u16_rounding = vdupq_n_u16(128);
// 复制8个值为128的uint8_t类型整数到某个D-register，该D-register对应的C变量是scalar
uint8x8_t scalar = vdup_n_u8(76);
// pixel_bgr.val[0]为一个Q-register，16个uint8_t类型的数，对应R通道
// pixel_bgr.val[1]为一个Q-register，16个uint8_t类型的数，对应G通道
// pixel_bgr.val[2]为一个Q-register，16个uint8_t类型的数，对应B通道
uint8x16x3_t pixel_bgr = vld3q_u8(bgr);
// 一个Q-register对应有两个D-register
// 这是拿到对应R通道的Q-register高位的D-register，有8个R值
// 参见Guide中Register overlap一节（这部分内容很重要！）
// 其他如low_r、high_g的情况相似，这里从略
uint8x8_t high_r = vget_high_u8(pixel_bgr.val[0]);
// 对8个R值执行乘76操作
// vmull是变长指令（常以单词末尾额外的L作为标记），源操作数是两个uint8x8_t的向量，目的操作数是uint16x8_t的向量
// 到这一步：Y = R * 76
// low_y的情况类似，从略
high_y = vmull_u8(high_r, scalar);
// 把scalar的8个128改为8个150
scalar = vdup_n_u8(150);
// 执行乘加运算
// 到这一步：Y = R * 76 + G * 150
high_y = vmlal_u8(high_y, high_g, scalar);
// 把scalar的8个150改为8个29
scalar = vdup_n_u8(29);
// 执行乘加运算
// 到这一步：Y = R * 76 + G * 150 + B * 29
high_y = vmlal_u8(high_y, high_b, scalar);
// 到这一步：Y = (R * 76 + G * 150 + B * 29) + 128
high_y = vaddq_u16(high_y, u16_rounding);
// vqshrn_n_u16是变窄指令（常以单词末尾额外的N作为标记，N为Narrow），将uint16x8_t的向量压缩为uint8x8_t
// 到这一步：Y = ((R * 76 + G * 150 + B * 29) + 128) >> 8
// vcombine_u8用于将两个D-register的值组装到一个Q-register中
pixel_yuv.val[0] = vcombine_u8(vqshrn_n_u16(low_y, 8), vqshrn_n_u16(high_y, 8));
```

* 看官也许已经注意到了，在前面的`BGR888ToYUV444`函数中，我并非像上面的代码一样，将一个通道的运算放到一块，而是有意将Y、U、V三个通道的运算打散搅在一起。这是为了尽可能减少data dependency所引起的stall，这也是优化NEON代码需要着重考虑的方向之一。

* 对NEON稍有了解的细心看官可能会问：乘法和加法所需要的128、76等常数为何不用立即数——例如NEON的`vmul_n`——而是采用先批量复制常数到向量再做向量运算？这是因为我们很多运算的源操作数是`int8x8_t`或`uint8x8_t`的向量，`vmul_n`等API很不幸不支持这种格式。这里也良心提醒看官，写NEON intrinsics或者汇编一定要对照Guide后面的附录列出的格式，否则编译器常常会报一些风马牛不相及的错误，把人往坑里带——我当初可是各种踩坑各种在不相关的地方纠结啊555...

## 交叉编译及debug

说到编译和debug，这里再良心提醒几点——如果看官早就知道了，那就权当我这好久没碰过嵌入式开发的小白在碎碎念好了：

* 一定要注意编译器EABI的版本！一定要注意编译器EABI的版本！一定要注意编译器EABI的版本！EABI指的是[Embedded-Application Binary Interface](https://en.wikipedia.org/wiki/Application_binary_interface)，我在这个白痴问题上浪费了不少时间，一定要把重要事情说三遍...

  - 一个需要注意的地方是gnueabi和androideabi的不一样。我最开始遇到的一个问题就是：把一个编译出来的可执行文件拷到开发板上，设了可执行权限，结果在运行时却出现「No such file or directory」，略诡异啊。用`strace`追踪发现是`exec`系统调用报的错，`exec`会根据可执行文件（在Linux系下是ELF）的`.interp`段运行相应的loader，由该loader做动态链接，再到可执行文件的入口地址开始执行。其实这时候用`readelf -l <program> | grep interpreter`查看ELF的loader地址，再看看设备上有没有该文件，基本可以确定EABI有没有用对了，但逗逼如我强行搞了个软链接[捂脸]...后来才发现是在Makefile里用gnueabi系的编译器编译Android程序，但其实编译Android程序还是直接用`ndk`才是王道啊！

  - 另一个需要注意的是float-abi。`gcc`中有一个选项`-mfloat-abi`，可选`soft`/`softfp`/`hardfp`：`soft`和后两者的区别是编译器不会生成浮点指令，浮点操作完全由软件实现；相比之下，`hardfp`走了另一个极端，浮点操作完全由硬件实现，效率最高；`softfp`则是走中间路线，它有着和`hardfp`完全不一样的calling convention——`hardfp`通过`VFP`来传浮点参数，而`softfp`还是通过整型寄存器来传参，和`soft`是一致的。因此，`softfp`编译的程序和`hardfp`编译的程序是互不兼容的，如果你把它们链接到一块，会出现「uses VFP register arguments, output does not」的报错。

* 需要使用正确的编译参数才能支持NEON。如果前面提到的`-mfloat-abi`指定了`soft`，那么就不支持NEON了。另外还常常需要`-mfpu=neon`来指定[FPU(Floating-Point Unit)](https://en.wikipedia.org/wiki/Floating-point_unit)是NEON Unit。具体的编译参数详见Guide第二章。 

* 可以使用`gdb`远程调试ARM设备上的程序：

1.在设备上启动`gdbserver`（假设在6666端口吧，哈哈我比较喜欢6666）：

```bash
# <program>是程序名
# <arg>是程序参数
$ gdbserver localhost:6666 <program> <arg>
```

2.在连接设备的主机（host）上启动对应EABI的`gdb`：
```
$ adb forward tcp:6666 tcp:6666
# <program>是程序名
$ gdb <program>
(gdb) target remote :6666
```

3.和`gdbserver`连接上后，就可以在主机端的`gdb`执行各种debug操作了。对于NEON程序，我们常常想查看NEON Unit的register file，可以采用下面的命令：
```
(gdb) info all-registers
```

# NEON汇编

虽然有了NEON intrinsics程序，但编译器<del>很笨很笨的</del>生成的汇编代码常常不尽如人意。要想发挥NEON指令集的最大威力，我们还需练就优化汇编这一上乘武功。好在有了intrinsics代码，我们可以“偷看”编译器或`objdump`的`-S`生成的“答案”，无需自己从头写汇编代码。当然，一开始看`-O3`优化过的汇编代码还是有点懵逼的，我个人比较偏好先看`-O0`（竟然和intrinsics的相差无几！）和`-O1`版的，以此为基准，再看看`-O2`和`-O3`，猜猜做了哪些优化，加以借鉴。本着这一思路，我用汇编又改写了一版`BGR888ToYUV444`，其中大部分汇编指令是由之前的intrinsics代码演化过来的，所以我这里也在注释标上了对应的intrinsics代码：

```c
void BGR888ToYUV444(unsigned char * __restrict__ yuv, unsigned char * __restrict__ bgr, int pixel_num)
{
    int count = pixel_num / 16;

    asm volatile(
            // const uint16x8_t u16_rounding = vdupq_n_u16(128);
            // const int16x8_t s16_rounding = vdupq_n_s16(128);
            "VMOV.I16 q3,#0x80\t\n"
            // const int8x16_t s8_rounding = vdupq_n_s8(128);
            "VMOV.I8  q4,#0x80\t\n"

            // i = 0
            "MOV      r2,#0\t\n"

            "LOOP: \t\n"

            // uint8x16x3_t pixel_bgr = vld3q_u8(bgr);
            "ADD      r12,r1,#0x18\t\n"
            "VLD3.8   {d0,d2,d4},[r1]\t\n"
            "VLD3.8   {d1,d3,d5},[r12]\t\n"

            // // bgr += 3 * 16;
            // "ADD      r1,r1,#0x30\t\n"

            // // i++
            // "ADD      r2,r2,#1\t\n"

            // int16x8_t signed_high_r = vreinterpretq_s16_u16(vmovl_u8(high_r));
            // int16x8_t signed_low_r = vreinterpretq_s16_u16(vmovl_u8(low_r));
            // int16x8_t signed_high_g = vreinterpretq_s16_u16(vmovl_u8(high_g));
            // int16x8_t signed_low_g = vreinterpretq_s16_u16(vmovl_u8(low_g));
            // int16x8_t signed_high_b = vreinterpretq_s16_u16(vmovl_u8(high_b));
            // int16x8_t signed_low_b = vreinterpretq_s16_u16(vmovl_u8(low_b));
            "VMOVL.U8 q5,d0\t\n"
            "VMOVL.U8 q6,d1\t\n"
            "VMOVL.U8 q7,d2\t\n"
            "VMOVL.U8 q8,d3\t\n"
            "VMOVL.U8 q9,d4\t\n"
            "VMOVL.U8 q10,d5\t\n"

            // uint8x8_t scalar = vdup_n_u8(76);
            // high_y = vmull_u8(high_r, scalar);
            // low_y = vmull_u8(low_r, scalar);
            "VMOV.I8  d26,#0x4c\t\n"
            "VMULL.U8 q11,d0,d26\t\n"
            "VMULL.U8 q12,d1,d26\t\n"

            // scalar = vdup_n_u8(150);
            // high_y = vmlal_u8(high_y, high_g, scalar);
            // low_y = vmlal_u8(low_y, low_g, scalar);
            "VMOV.I8  d26,#0x96\t\n"
            "VMLAL.U8 q11,d2,d26\t\n"
            "VMLAL.U8 q12,d3,d26\t\n"

            // scalar = vdup_n_u8(29);
            // high_y = vmlal_u8(high_y, high_b, scalar);
            // low_y = vmlal_u8(low_y, low_b, scalar);
            "VMOV.I8  d26,#0x1d\t\n"
            "VMLAL.U8 q11,d4,d26\t\n"
            "VMLAL.U8 q12,d5,d26\t\n"

            // int16x8_t signed_scalar = vdupq_n_s16(-43);
            // high_u = vmulq_s16(signed_high_r, signed_scalar);
            // low_u = vmulq_s16(signed_low_r, signed_scalar);
            "VMVN.I16 q1,#0x2a\t\n"
            "VMUL.I16 q13,q5,q1\t\n"
            "VMUL.I16 q14,q6,q1\t\n"

            // signed_scalar = vdupq_n_s16(127);
            // high_v = vmulq_s16(signed_high_r, signed_scalar);
            // low_v = vmulq_s16(signed_low_r, signed_scalar);
            "VMOV.I16 q2,#0x7f\t\n"
            "VMUL.I16 q15,q5,q2\t\n"
            "VMUL.I16 q0,q6,q2\t\n"

            // signed_scalar = vdupq_n_s16(-84);
            // high_u = vmlaq_s16(high_u, signed_high_g, signed_scalar);
            // low_u = vmlaq_s16(low_u, signed_low_g, signed_scalar);
            "VMVN.I16 q1,#0x53\t\n"
            "VMLA.I16 q13,q7,q1\t\n"
            "VMLA.I16 q14,q8,q1\t\n"

            // signed_scalar = vdupq_n_s16(-106);
            // high_v = vmlaq_s16(high_v, signed_high_g, signed_scalar);
            // low_v = vmlaq_s16(low_v, signed_low_g, signed_scalar);
            "VMVN.I16 q2,#0x69\t\n"
            "VMLA.I16 q15,q7,q2\t\n"
            "VMLA.I16 q0,q8,q2\t\n"

            // signed_scalar = vdupq_n_s16(127);
            // high_u = vmlaq_s16(high_u, signed_high_b, signed_scalar);
            // low_u = vmlaq_s16(low_u, signed_low_b, signed_scalar);
            "VMOV.I16 q1,#0x7f\t\n"
            "VMLA.I16 q13,q9,q1\t\n"
            "VMLA.I16 q14,q10,q1\t\n"

            // signed_scalar = vdupq_n_s16(-21);
            // high_v = vmlaq_s16(high_v, signed_high_b, signed_scalar);
            // low_v = vmlaq_s16(low_v, signed_low_b, signed_scalar);
            "VMVN.I16 q2,#0x14\t\n"
            "VMLA.I16 q15,q9,q2\t\n"
            "VMLA.I16 q0,q10,q2\t\n"

            // high_y = vaddq_u16(high_y, u16_rounding);
            // low_y = vaddq_u16(low_y, u16_rounding);
            "VADD.I16 q11,q11,q3\t\n"
            "VADD.I16 q12,q12,q3\t\n"

            // high_u = vaddq_s16(high_u, s16_rounding);
            // low_u = vaddq_s16(low_u, s16_rounding);
            "VADD.I16 q13,q13,q3\t\n"
            "VADD.I16 q14,q14,q3\t\n"

            // high_v = vaddq_s16(high_v, s16_rounding);
            // low_v = vaddq_s16(low_v, s16_rounding);
            "VADD.I16 q15,q15,q3\t\n"
            "VADD.I16 q0,q0,q3\t\n"

            // pixel_yuv.val[0] = vcombine_u8(vqshrn_n_u16(low_y, 8), vqshrn_n_u16(high_y, 8));
            "VQSHRN.U16 d10,q11,#8\t\n"
            "VQSHRN.U16 d11,q12,#8\t\n"

            // u = vcombine_s8(vqshrn_n_s16(low_u, 8), vqshrn_n_s16(high_u, 8));
            "VQSHRN.S16 d12,q13,#8\t\n"
            "VQSHRN.S16 d13,q14,#8\t\n"

            // v = vcombine_s8(vqshrn_n_s16(low_v, 8), vqshrn_n_s16(high_v, 8));
            "VQSHRN.S16 d14,q15,#8\t\n"
            "VQSHRN.S16 d15,q0,#8\t\n"

            // u = vaddq_s8(u, s8_rounding);
            // v = vaddq_s8(v, s8_rounding);
            "VADD.I8  q6,q6,q4\t\n"
            "VADD.I8  q7,q7,q4\t\n"

            // vst3q_u8(yuv, pixel_yuv);
            "ADD      r12,r0,#0x18\t\n"
            "VST3.8   {d10,d12,d14},[r0]\t\n"
            "VST3.8   {d11,d13,d15},[r12]\t\n"
            // bgr += 3 * 16;
            // yuv += 3 * 16;
            "ADD      r1,r1,#0x30\t\n"
            "ADD      r0,r0,#0x30\t\n"
            // i++
            "ADD      r2,r2,#1\t\n"
            // i < count
            "CMP      r2,r3\t\n"
            "BLT      LOOP\t\n"
            : [r0] "+r" (yuv), [r1] "+r" (bgr), [r3] "+r" (count)
            :
            : "r2", "memory", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "d10", "d11", "d12", "d13", "d14", "d15", "d16", "d17", "d18", "d19", "d20", "d21", "d22", "d23", "d24", "d25", "d26", "d27", "d28", "d29", "d30", "d31"
            );


    // Handle leftovers
    int i;
    for (i = count * 16; i < pixel_num; ++i) {
        uint8_t r = bgr[i * 3];
        uint8_t g = bgr[i * 3 + 1];
        uint8_t b = bgr[i * 3 + 2];

        uint16_t y_tmp = 76 * r + 150 * g + 29 * b;
        int16_t u_tmp = -43 * r - 84 * g + 127 * b;
        int16_t v_tmp = 127 * r - 106 * g - 21 * b;

        y_tmp = (y_tmp + 128) >> 8;
        u_tmp = (u_tmp + 128) >> 8;
        v_tmp = (v_tmp + 128) >> 8;

        yuv[i * 3] = (uint8_t) y_tmp;
        yuv[i * 3 + 1] = (uint8_t) (u_tmp + 128);
        yuv[i * 3 + 2] = (uint8_t) (v_tmp + 128);
    }
}
```

## GCC内联汇编

这里我用到了GCC内联汇编，其基本结构如下：

```
asm [volatile] ( AssemblerTemplate 
                 : OutputOperands 
                 [ : InputOperands
                 [ : Clobbers ] ])
```

其中，关键字`volatile`表示禁止编译器对这段汇编代码进行优化以避免编译器优化——你想啊，要是信任编译器优化效果的话，我们也不必手撸汇编了，不是么XD `AssemblerTemplate`自然是汇编代码部分了。`OutputOperands`和`InputOperands`是指定输出和输入的操作数，前面的代码在`OutputOperands`一栏中指定了输出和输入（指针`yuv`可读写，存放于`r0`寄存器；指针`bgr`可读写，存放于`r1`寄存器；变量`count`可读写，存放于`r3`寄存器）：

```
            : [r0] "+r" (yuv), [r1] "+r" (bgr), [r3] "+r" (count)
            :
```

`Clobbers`一栏用来告诉编译器这段内联汇编代码会改变的操作数。如果操作数是在寄存器，编译器会做保护，在执行内联汇编代码前save它的值，在执行内联汇编代码后restore；如果操作数是在内存、编译器在执行内联汇编代码前曾把内存的值cache在寄存器的话，编译器会把寄存器的值flush回内存，再执行内联汇编代码，下次直接从内存读取，从而保证操作数数值的正确性。在上一段代码中，我们会修改的操作数是循环中的自增变量`i`所在的寄存器`r2`、内存和32个D寄存器（这32个D寄存器我才懒得一个个敲呢，当然是录了个vim宏啦XD）：

```
            : "r2", "memory", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "d10", "d11", "d12", "d13", "d14", "d15", "d16", "d17", "d18", "d19", "d20", "d21", "d22", "d23", "d24", "d25", "d26", "d27", "d28", "d29", "d30", "d31"
```

更多关于GCC内联汇编的内容可参考：

* [ARM GCC Inline Assembler Cookbook](http://www.ethernut.de/en/documents/arm-inline-asm.html)

* [How to Use Inline Assembly Language in C Code](https://gcc.gnu.org/onlinedocs/gcc/Using-Assembly-Language-with-C.html)


## 从intrinsics到汇编

把intrinsics代码改成汇编的一个关键之处，是如何把C/C++里的变量名高效对应到寄存器。我在用`gcc`生成汇编代码时就发现，编译器对我这段intrinsics代码使用的实际Q-register超过16个，所以需要不断save/restore寄存器的值来重复使用寄存器。其实我们可以通过巧妙的排布寄存器来减少不必要的save/restore，这也是我写NEON汇编最开始想优化的一个点。在上面的BGR888ToYUV444程序中，我用Q0、Q1、Q2分别保存R、G、B的三个`uint8x16_t`向量，用Q3保存值为128的`int16x8_t`向量常量，用Q4保存值为128的`int8x16_t`向量常量。首先计算Y通道，把中间计算结果的两个`uint16x8_t`向量分别存到Q11和Q12。这个时候要计算U和V通道了，需要把数值从`uint8_t`类型转成`int16_t`，所以我把R通道的D0拷到Q5、D1拷到Q6（还记得Q0寄存器就是由D0和D1组成的吧？），把G通道的D2拷到Q7、D3拷到Q8，把R通道的D4拷到Q9、D5拷到Q10，之后便不再需要用Q0、Q1、Q2来保存R、G、B了。我们再把U通道中间计算结果的两个`int16x8_t`向量分别存到Q13和Q14，把V通道中间计算结果的两个`int16x8_t`向量分别存到Q15和Q0（还记得Q0可以被覆写吗？），这样就完美把16个Q寄存器/32个D寄存器都用了个遍，不需要额外save/restore。

## 如何debug汇编代码

写程序总是绕不开debug问题？那么如何debug NEON汇编呢？可以在汇编代码中使用[断点指令BRK](http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.dui0801c/pge1427897654274.html)，这样在`gdb`中就能在断点处停下来，执行相关debug操作了。要让程序继续运行只需增加PC跳过`BRK`即可。

另外，有一个图形化的[网页调试器](https://szeged.github.io/nevada/)值得安利一下，这对于新手来说是很用户友好很实用的工具。

## 继续优化

个人认为，在写intrinsics程序的阶段就要力求用尽可能少的intrinsics来实现功能，这样能保证生成的汇编指令尽可能精简。在指令足够精简之后，一项最重要的工作就是instruction reordering/scheduling，减少诸如RAW、WAW等memory dependency引起的stall。

这个时候你需要对每条指令重要阶段的时钟周期了然于心。如何查到相关资料呢？你可以到[ARM 信息中心](http://infocenter.arm.com/help/index.jsp)，查你所用的ARM处理器的Technical Reference Manual，其中就有一章Instruction Cycle Timing。另外，WebShaker为Cortex A8做了一个网页版[Cycle Counter for Cortex A8](http://pulsar.webshaker.net/ccc/index.php?lng=us)，如果你在使用这一处理器，这是一个很值得使用和参考的工具。

最后，对于实际处理器的NEON汇编调优，考虑到ARM指令和NEON指令走的是不同流水线、dual issue（详见Guide第五章）等等因素，如何达到最优scheduling仍是很有挑战性的问题。个人觉得，像我这种小白，还是需要有intruction-level profiler来定位性能热点进行优化，可惜目前为止尚未找到趁手的工具。另外，以前我在玩CUDA时，有不少不错的tutorial（CUDA玩家想必都会看过的要算Mark Harris的parallel reduction了）给出了step-by-step的优化思路、指标和方法，对新手快速上手CUDA、并迅速应用到新问题上很有帮助。但ARM在这方面确实很欠缺，即使是Guide里的三章Examples，也多半是告诉了最终答案而没有思路和方法。如果有ARM大神知道如何做step-by-step性能分析和优化，还望多多赐教。
