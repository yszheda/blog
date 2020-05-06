---
layout: post
title: "检测quick-cocos2d-x游戏的lua内存泄漏"
date: 2015-08-19 11:53
comments: true
published: true
categories: [cocos2d-x, CS, tech]
# keywords: cocos2d-x quick-cocos2d-x lua memory leak
keywords: cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, game, mobile game, game devolopment, 内存泄露, memory leak, quick-cocos2d-x, quickx, quick-x, lua
description: detect lua memory leak in quick-cocos2d-x
---

虽然lua有垃圾回收机制，但在使用quick-cocos2d-x和lua开发游戏还是会有不恰当的实现方式所导致的lua内存泄露（例如对cocos2d-x的`Node`对象做了`retain`却没有`release`、把`local`变量定义成全局变量、没有根据instance的lifecycle去释放它所占有的资源等等）。最近看到云风大神写的lua内存泄露检查工具[lua-snapshot](https://github.com/cloudwu/lua-snapshot)，便萌发了将它集成到我们游戏开发中，作为quantity assurance中一环。

<!-- more -->

# 配置 #

`lua-snapshot`是用C实现的。我在网上看到不少人是把`lua-snapshot`编译成动态链接库、用`package.loadlib`来调用的，其实lua的`require`本身就能加载C库的。

首先在`cocos2d-x/external/lua/`目录下将lua-snapshot代码clone下来：

```
git clone https://github.com/cloudwu/lua-snapshot.git
```

在`cocos2d-x/cocos/scripting/lua-bindings/manual/lua-snapshot/`目录中添加如下文件：

{% include_code lua-snapshot/lua_snapshot_extensions.h lang:c %}

{% include_code lua-snapshot/lua_snapshot_extensions.c lang:c %}

{% include_code lua-snapshot/lua_cocos2dx_snapshot_manual.h lang:cpp %}

{% include_code lua-snapshot/lua_cocos2dx_snapshot_manual.cpp lang:cpp %}

然后找到`lua_module_register.h`文件，在`lua_module_register`函数中添加
```
    register_snapshot_module(L);
```
和头文件
```
#include "lua-snapshot/lua_cocos2dx_snapshot_manual.h"
```

{% include_code lua-snapshot/lua_module_register.h lang:cpp %}

# 使用 #

由于我们游戏的界面主要是窗口，所以之前实现时便在cocos2d-x引擎的`Scene`和`Layer`中间引入了一层`Window`，并用一个全局singleton的`WindowManager`对所有`Window`对象进行管理，对窗口的创建前、创建后、销毁前、销毁后等等行为做公共处理。这样的设计给我加入内存泄露检测带来了不少便利：我只需在创建窗口实例之前记录下当时的快照snapshot1，打开窗口后根据这个窗口的功能做一些操作——通常和测试功能一起进行，也和`WindowManager`的公共逻辑无关，所以不在代码做处理——在窗口销毁前记下snapshot2，在销毁后记下snapshot3，比较这三个快照，如果一个实例不在snapshot1中而存在于snapshot2和snapshot3中，则该实例属于这个窗口操作后造成的内存泄露。


# 参考资料 #

- [1][一个 Lua 内存泄露检查工具](http://blog.codingnow.com/2012/12/lua_snapshot.html)

- [2][游戏逻辑层在Lua中的内存泄漏与防范](http://colen.iteye.com/blog/588897)

- [3][lua内存泄漏查证](http://shavingha.blog.163.com/blog/static/10378336200822134554488/)

- [4][使用snapshot检测Lua中的内存泄露](http://www.codingart.info/snapshot-detect-Lua-memoryleak.html)
