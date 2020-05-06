---
layout: post
title: "quick-cocos2d-x按钮补丁"
date: 2015-07-06 20:20
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, button, widget, 按钮, UI, 游戏开发, 手游开发, mobile game, game devolopment
description: patch for quick-cocos2d-x button
---
最近在处理一个略奇怪的问题：app在某些情况下点按钮会消失后又重新出现，报bug的童鞋们把现象描述得有些扑朔迷离，因此本渣在排查问题时花了不少时间，在查了一些不相关的问题之后最后终于确定了现象和原因（详情请参见本渣另一篇[博文](http://galoisplusplus.coding.me/blog/2015/01/04/quick-cocos2d-x-pitfalls/)）。本渣也发现了quickx的按钮类`UIButton`在实现上存在的一些问题，与其不改动其内部实现去做个workaround，还不如根除问题。于是本渣对相关类的内部逻辑重新做了些设计和实现，相关的改动可以通过`patch`命令来采用。

<!-- more -->

{% include_code StateMachine.lua.patch lang:lua %}

{% include_code UIButton.lua.patch lang:lua %}

{% include_code UIPushButton.lua.patch lang:lua %}

{% include_code UICheckBoxButton.lua.patch lang:lua %}

完整的代码请猛戳：
[yszheda/quickx-extensions](https://github.com/yszheda/quickx-extensions)
