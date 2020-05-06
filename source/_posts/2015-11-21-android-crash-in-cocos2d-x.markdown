---
layout: post
title: "记一次cocos2d-x游戏android崩溃排查"
date: 2015-11-21 22:53
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: android, Android, breakpad, debug, crash, 崩溃, 游戏崩溃, cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, game, mobile game, game devolopment
description: android crash in cocos2d-x
---

最近查google breakpad回传的crash log，发现了不少`cocos2d::FileUtilsAndroid::getData`引起的崩溃。崩溃日志的关键信息如下：

<!-- more -->

{% codeblock lang:text %}
Operating system: Android
                  0.0.0 Linux 3.4.0-3215177 #1 SMP PREEMPT Thu Nov 6 17:48:34 KST 2014 armv7l
CPU: arm
     ARMv7 Qualcomm Krait features: swp,half,thumb,fastmult,vfpv2,edsp,neon,vfpv3,tls,vfpv4,idiva,idivt
     4 CPUs

Crash reason:  SIGSEGV
Crash address: 0x0

Thread 11 (crashed)
 0  libc.so + 0x22284
     r0 = 0x00000000    r1 = 0x7a634048    r2 = 0x00001000    r3 = 0x5a007304
     r4 = 0x40090d9c    r5 = 0x01632924    r6 = 0x01632924    r7 = 0x40091334
     r8 = 0x01632924    r9 = 0x00001000   r10 = 0x7a634280   r12 = 0x00000035
     fp = 0x00001000    sp = 0x78a78390    lr = 0x00000280    pc = 0x4005b284
    Found by: given as instruction pointer in context
 1  libc.so + 0x25aaf
     sp = 0x78a783a0    pc = 0x4005eab1
    Found by: stack scanning
 2  libcocos2dlua.so!cocos2d::FileUtilsAndroid::getData [CCFileUtils-android.cpp : 273 + 0xb]
     sp = 0x78a783c8    pc = 0x77fe2415
    Found by: stack scanning
 3  libcocos2dlua.so!cocos2d::FileUtilsAndroid::getDataFromFile [CCFileUtils-android.cpp : 307 + 0x5]
     r4 = 0x78a78450    r5 = 0x7d307558    r6 = 0x78a78450    r7 = 0x7e851e54
     sp = 0x78a78438    pc = 0x77fe2523
    Found by: call frame info
 4  libcocos2dlua.so!cocos2d::FontFreeType::createFontObject [CCFontFreeType.cpp : 127 + 0x7]
     r4 = 0x78a785a4    r5 = 0x7d307558    r6 = 0x78a78450    r7 = 0x7e851e54
     sp = 0x78a78440    pc = 0x782c6565
    Found by: call frame info
 5  libcocos2dlua.so!cocos2d::FontFreeType::create [CCFontFreeType.cpp : 58 + 0x9]
     r4 = 0x7d307558    r5 = 0x00000000    r6 = 0x00000000    r7 = 0x00000000
     sp = 0x78a78470    pc = 0x782c665b
    Found by: call frame info
 6  libcocos2dlua.so!cocos2d::FontAtlasCache::getFontAtlasTTF [CCFontAtlasCache.cpp : 90 + 0x13]
     r0 = 0x78a785a4    r1 = 0x00000014    r2 = 0x00000000    r4 = 0x7877905c
     r5 = 0x78a784b4    r6 = 0x78a785a4    r7 = 0x78a784b4    sp = 0x78a78490
     pc = 0x782c22bd
    Found by: call frame info
 7  libcocos2dlua.so!cocos2d::Label::setTTFConfig [CCLabel.cpp : 438 + 0x3]
     r4 = 0x82d231a8    r5 = 0x7ceddca0    r6 = 0x78a785a4    r7 = 0x00000000
     sp = 0x78a78578    pc = 0x78249423
    Found by: call frame info
 8  libcocos2dlua.so!cocos2d::ui::Text::setFontName [UIText.cpp : 162 + 0x9]
     r3 = 0x78249415    r4 = 0x78a785a4    r5 = 0x7ceddca0    r6 = 0x82d234c0
     r7 = 0x00000398    sp = 0x78a78590    pc = 0x78203b41
    Found by: call frame info
 9  libcocos2dlua.so!cocostudio::TextReader::setPropsFromJsonDictionary [TextReader.cpp : 119 + 0x7]
     r4 = 0x7a0b1ec8    r5 = 0x7ceddca0    r6 = 0x78a78614    r7 = 0x78a78620
     sp = 0x78a785e0    pc = 0x781b42f1
    Found by: call frame info
{% endcodeblock %}

很明显，这是由访问非法内存地址0x0所引起的segmentation fault，下面再来看call stack中所提示的`CCFileUtils-android.cpp`中第273行：
  
{% codeblock lang:c start:247 mark:273 %}
        do
        {
            // read rrom other path than user set it
            //CCLOG("GETTING FILE ABSOLUTE DATA: %s", filename);
            const char* mode = nullptr;
            if (forString)
                mode = "rt";
            else
                mode = "rb";

            FILE *fp = fopen(fullPath.c_str(), mode);
            CC_BREAK_IF(!fp);

            long fileSize;
            fseek(fp,0,SEEK_END);
            fileSize = ftell(fp);
            fseek(fp,0,SEEK_SET);
            if (forString)
            {
                data = (unsigned char*) malloc(fileSize + 1);
                data[fileSize] = '\0';
            }
            else
            {
                data = (unsigned char*) malloc(fileSize);
            }
            fileSize = fread(data,sizeof(unsigned char), fileSize,fp);
            fclose(fp);

            size = fileSize;
        } while (0);
{% endcodeblock %}

第273行是调用`fread`函数，由于`fp`已经通过`CC_BREAK_IF(!fp);`做了检查，那么很可能便是`malloc`的buffer为`NULL`所致。

为了进一步验证，我们再来看call stack顶层：
```
 0  libc.so + 0x22284
     r0 = 0x00000000    r1 = 0x7a634048    r2 = 0x00001000    r3 = 0x5a007304
     r4 = 0x40090d9c    r5 = 0x01632924    r6 = 0x01632924    r7 = 0x40091334
     r8 = 0x01632924    r9 = 0x00001000   r10 = 0x7a634280   r12 = 0x00000035
     fp = 0x00001000    sp = 0x78a78390    lr = 0x00000280    pc = 0x4005b284
    Found by: given as instruction pointer in context
```

基本可以确定是访问r0（0x0）了，那么r0的庐山真面目究竟如何呢？既然crash log说崩溃的机型所用的cpu是arm架构，那么我们便可以查阅arm的文档[AAPCS（Procedure Call Standard for the ARM Architecture）](http://infocenter.arm.com/help/topic/com.arm.doc.ihi0042e/IHI0042E_aapcs.pdf)。其中Parameter Passing这一节便提到：
```
The base standard provides for passing arguments in core registers (r0-r3) and on the stack. For subroutines that
take a small number of parameters, only registers are used, greatly reducing the overhead of a call.
```

r0刚好对应了第一个参数，这在我们的例子中就是`fread`的`data`。当然，在arm中，r0不仅可以是参数寄存器（argument register），还可能是结果寄存器（result register）和临时寄存器（scratch register）。但是，在这个`fread`所引起的崩溃中，基本可以排除result register的情况，因为`fread`的结果不是需要被访问的内存地址；scratch register倒还是有可能的，如果能找到设备系统的libc.so来`objdump`看下相关的汇编代码可以更确定些。

基本确认原因后，改起来便很容易了。目前我已向cocos2d-x提交了一个patch[PR 14458](https://github.com/cocos2d/cocos2d-x/pull/14458)。

# 参考资料 #

[1][AAPCS](http://infocenter.arm.com/help/topic/com.arm.doc.ihi0042e/IHI0042E_aapcs.pdf)

[2][ARM to C calling convention, registers to save](http://stackoverflow.com/questions/261419/arm-to-c-calling-convention-registers-to-save)

检查`malloc`的返回值是否为`NULL`的必要性不必我多说，可以参考以下的SOF链接：

[3][Under what circumstances can malloc return NULL?](http://stackoverflow.com/questions/9101597/under-what-circumstances-can-malloc-return-null)

[4][Is there a need to check for NULL after allocating memory, when kernel uses overcommit memory](http://stackoverflow.com/questions/2248995/is-there-a-need-to-check-for-null-after-allocating-memory-when-kernel-uses-over)

关于fread函数：

[5][fread reference](http://www.cplusplus.com/reference/cstdio/fread/)
