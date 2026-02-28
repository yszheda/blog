Title: quick-cocos2d-x踩坑记——问题与解决方案
Date: 2015-01-04 02:00:00
description: Traps and Pitfalls in quick-cocos2d-x
Tags: cocos2d-x, CS, tech, cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20150104-quick-cocos2d-x-pitfalls
Category: tech
本渣最近一个月来开始接触quick-cocos2d-x，用lua开发比c++要快些，但也因为quickx目前的一些坑——当然有些其实应该算是2dx引擎本身的坑——让本渣折腾了不少时间。在此做点记录，希望能让别人少走些弯路。本文将不时更新。

<!-- more -->

## quickx的uiloader只能解析CocoStudio v1.5（windows版）的json ##
### 现象 ###
CocoStudio的Mac版v1导出的json用uiloader解析有问题，另外cocostuio v2暂无导出json的功能，而uiloader只能解析json格式。

### 建议 ###
- 如果大量使用quickx的ui类，还是用CocoStudio v1.5为好。
- 如果不想切换UI编辑器，可以直接用cocos2d-x的CSLoader，但要小心与quickx的ui类混用的情况（下文会提及）。
- 如果不怕折腾，可以研究下CocoStudio v1.5的json格式，改quickx的源代码。

## quickx独立的触摸响应与cocos2d-x的存在不兼容问题 ##
### 现象 ###
在同时使用cocos2d-x的Widget类和quickx的ui类时，quickx的ui类没有接受响应事件。
在此仅举一个典型例子，在quickx的UIScrollView中加入一个CSLoader解析的Widget，则UIScrollView无法滚动。
照理说，Widget的触摸事件的priority是0（graph priority），quickx的LuaEventNode的priority是-1（fixed priority），应该是LuaEventNode先接收touch进行处理才对，
但是Widget是单点触摸，而LuaEventNode是多点触摸，再加上cocos2d-x是先处理单点再处理多点的，所以触摸事件反而是先到了Widget了。
不幸的是Widget默认是swallow touch的，所以触摸事件不会到LuaEventNode。

### 建议 ###
- 彻底杜绝此类混用。但由于之前提到的uiloader的问题，可能无法完全使用quickx的ui类。
- [workaround]如果不需要多点触摸，可以把LuaEventNode改成单点触摸。

## quickx的UIScrollView/UIListView的bug ##
老实说，这两个ui类确实不够成熟。

- 用local node space坐标与world space坐标做比较。引起的问题有：没有惯性滚动；`UIListView`的item没完全移除viewRect就被remove掉等等。本渣向quickx提交了两个PR：前一个[PR#348](https://github.com/dualface/v3quick/pull/348)过了几周才被处理，代码有conflict，最后还是开发者再提了新的PR去merge了；后一个[PR#407](https://github.com/dualface/v3quick/pull/407)很快就被merge了。所以目前更新代码就可以了。
- `UIListView`若是所设的item size小于item的`cascadeBoundingBox`大小，滚动时会有死循环，反复load item和remove item。开发者后来加了个[patch](https://github.com/dualface/v3quick/commit/c233f785019200033f767e15073392c221b1c48f)，该bug重现变少了，但还是存在的。本渣trace源代码后发现，死循环的根源在于`UIListView:increaseOrReduceItem_`函数。本渣实在无法理解quickx开发者为何要把这个每帧会被调用到的函数设计成这么一个计算量很大的递归函数，这不是作死地拉低FPS拉低性能么...于是本渣就把递归调用那部分去掉了...
- `UIScrollView`的惯性滚动行为很不用户友好，于是本渣仿照2dx中`CCScrollView`的做法实现了这部分逻辑。

## LuaEventNode崩溃 ##
### 现象 ###
点击crash，是cocos2d-x C++的内存管理报错。
已有人向quickx报过[bug](https://github.com/dualface/v3quick/issues/318)，但开发者回复中提到的patch被没有解决问题。

### 建议 ###
在`LuaEventNode`的构造函数时retain参数node，在析构函数中release。

_*更新*：又有与该issue相关的新patch，或许该bug已经被修好了。_

## CocoStudio的文字标签加描边后字体颜色会改变 ##
### 现象 ###
给CocoStudio的`UIText`对象加上描边后字体颜色也变掉了。
这个bug其实是2dx引擎的`CSLoader`的bug，`CSLoader`在解析包括`UIText`的UI组件、并设置它们相应的颜色时，调用的都是`node`的`setColor`，而非调用`Label`自身的`setTextColor`接口，这就导致了描边颜色和node颜色的混合。

### 建议 ###
我用了如下的workaround去拿到编辑器中设置的字体颜色，并重置node本身的颜色：

```lua
function MyPackage.formatUIText(label, formatFunc)
    local color = label:getColor()
    color.a = 255
    label:setColor(cc.c3b(0xff, 0xff, 0xff))
    label:setTextColor(color)
    formatFunc(label)
end
```

这样就可以用来正常设置描边了，例如：
```
MyPackage.formatUIText(testLabel, function(label)
label:setOutline(cc.color.BLUE, 2)
end)
```

当UI的字体较多时，对每一个`UIText`都调用一遍`MyPackage.formatUIText`去加同样的描边显然不现实，所以我又加了一个接口：

```lua
--[[
format all labels under root layout
]]
function MyPackage.formatAllLabels(layout, formatFunc)
    local children = layout:getChildren()
    local childCount = layout:getChildrenCount()
    if childCount < 1 then
        return
    end
    for i = 1, childCount do
        if tolua.type(children[i]) == "ccui.Text" then
            MyPackage.formatUIText(children[i], formatFunc)
        end
        MyPackage.formatAllLabels(children[i], formatFunc)
    end
end
```

_NOTE:关于`MyPackage`请参见[另一篇博文](http://galoisplusplus.coding.me/blog/2015/05/01/quickx-tips/)_


## quickx按钮显示异常 ##
### 现象 ###
quickx的按钮在某些清理`TextureCache`/`SpriteFrameCache`的情况下（例如在app切换到后台/收到内存警告时调用`removeUnusedSpriteFrames`/`removeUnuserdTextures`）会出现显示问题，一种常见的问题便是按钮的点击状态和正常状态的图片不同，在点击时按钮会消失不见。
这个现象的原因是quickx的`UIButton`实现只`addChild`了当前状态的`sprite`，其他状态的`sprite`未曾被`retain`，只是在状态切换时才动态生成，这就导致了非当前状态的Texture/SpriteFrame很可能会因为`reference count`（关于何为`reference count`可以参考本渣另一篇博文[cocos2d-x V3.x内存管理分析](http://galoisplusplus.coding.me/blog/2014/07/30/memory-management-in-cocos2d-x-v3/)）不大于1而被清理出内存。

### 建议 ###
本渣改了quickx `UIButton`的内部实现，采用了类似2dx中`Widget`类`ccui.Button`的方式，保证在初始化按钮时它的每个状态的`sprite`都被`retain`过。
本渣的改动请参考[另一篇博文](http://galoisplusplus.coding.me/blog/2015/07/06/patch-for-quickx-button/)。
