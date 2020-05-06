---
layout: post
title: "quick-cocos2d-x tips"
date: 2015-05-01 14:00
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x quick-cocos2d-x quickx cocos2d cocos game gameDev 游戏开发 游戏 手游开发 手游 手机游戏
description: quick-cocos2d-x tips
---
承接[上一篇](http://galoisplusplus.coding.me/blog/2015/01/04/quick-cocos2d-x-pitfalls/)，这篇主要谈谈本渣在quickx用的一些脚本或自己折腾的一些定制，本文也将不时更新。

如无特殊说明，相关函数放在一个`MyPackage`的lua global table中：

```lua
MyPackage = MyPackage or {}
```

<!-- more -->

## UI组件 ##
### 滚动列表相关 ###

```lua
--[[--
Refresh UIListView at the current postion.
NOTE: only needed in async mode
]]
function MyPackage.refreshUIListView(listView)
	if not listView.bAsyncLoad then
        listView:reload()
        return
    end

    if #listView.items_ <= 0 then
        listView:reload()
        return
    end

    local originPos = MyPackage.getOriginPosOfUIListView(listView)
    -- index of the previous beginning item
    local beginIdx = listView.items_[1].idx_

    listView:removeAllItems()
    listView.container:setPosition(0, 0)
    listView.container:setContentSize(cc.size(0, 0))

    MyPackage.drawUIListViewFromIdx(listView, beginIdx, originPos.x, originPos.y)
end

--[[--
NOTE: only needed in async mode
]]
function MyPackage.getOriginPosOfUIListView(listView)
	if not listView.bAsyncLoad then
        return
    end

    local getContainerCascadeBoundingBox = function (listView)
        local boundingBox
        for i, item in ipairs(listView.items_) do
            local w,h = item:getItemSize()
            local x,y = item:getPosition()
            local anchor = item:getAnchorPoint()
            x = x - anchor.x * w
            y = y - anchor.y * h

			if boundingBox then
				boundingBox = cc.rectUnion(boundingBox, cc.rect(x, y, w, h))
			else
				boundingBox = cc.rect(x, y, w, h)
			end
		end

		local point = listView.container:convertToWorldSpace(cc.p(boundingBox.x, boundingBox.y))
		boundingBox.x = point.x
		boundingBox.y = point.y
		return boundingBox
	end

	local cascadeBound = getContainerCascadeBoundingBox(listView)
--	local cascadeBound = listView.scrollNode:getCascadeBoundingBox()

    local localPos = listView:convertToNodeSpace(cc.p(cascadeBound.x, cascadeBound.y))

    local originPosX = 0
    local originPosY = 0
    if cc.ui.UIScrollView.DIRECTION_VERTICAL == listView.direction then
        -- ahead part of view
        originPosY = localPos.y + cascadeBound.height - listView.viewRect_.y - listView.viewRect_.height
    else
		-- left part of view
		originPosX = - listView.viewRect_.x + localPos.x
    end

    return cc.p(originPosX, originPosY)
end

--[[--
Draw UIListView from the `beginIdx`th item at position (`originPosX`, `originPosY`).
NOTE: only needed in async mode
]]
function MyPackage.drawUIListViewFromIdx(listView, beginIdx, originPosX, originPosY)
	if not listView.bAsyncLoad then
        listView:reload()
        return
    end

    listView:removeAllItems()
    listView.container:setPosition(0, 0)
    listView.container:setContentSize(cc.size(0, 0))

    local beginIdx = beginIdx or 1
    local originPosX = originPosX or 0
    local originPosY = originPosY or 0

    local count = listView.delegate_[cc.ui.UIListView.DELEGATE](listView, cc.ui.UIListView.COUNT_TAG)
    listView.items_ = {}
    local itemW, itemH = 0, 0
    local item
    local containerW, containerH = 0, 0
    for i = beginIdx, count do
        item, itemW, itemH = listView:loadOneItem_(cc.p(originPosX, originPosY), i)
        if cc.ui.UIScrollView.DIRECTION_VERTICAL == listView.direction then
            originPosY = originPosY - itemH
            containerH = containerH + itemH
        else
            originPosX = originPosX + itemW
            containerW = containerW + itemW
        end
        if containerW > listView.viewRect_.width + listView.redundancyViewVal
            or containerH > listView.viewRect_.height + listView.redundancyViewVal then
            break
        end
    end

	if cc.ui.UIScrollView.DIRECTION_VERTICAL == listView.direction then
		listView.container:setPosition(listView.viewRect_.x,
			listView.viewRect_.y + listView.viewRect_.height)
	else
		listView.container:setPosition(listView.viewRect_.x, listView.viewRect_.y)
	end

    listView:increaseOrReduceItem_()
end

function MyPackage.elasticMoveUIScrollView(scrollView, scrollToBottom, scrollToRight)
	local cascadeBound = scrollView:getScrollNodeRect()
	local disX, disY = 0, 0
	local viewRect = scrollView:getViewRectInWorldSpace()

	if cascadeBound.width < viewRect.width then
        if scrollToRight then
			disX = viewRect.x + viewRect.width - cascadeBound.x - cascadeBound.width
        else
            disX = viewRect.x - cascadeBound.x
        end
    else
        if cascadeBound.x > viewRect.x then
            disX = viewRect.x - cascadeBound.x
        elseif cascadeBound.x + cascadeBound.width < viewRect.x + viewRect.width then
            disX = viewRect.x + viewRect.width - cascadeBound.x - cascadeBound.width
        end
    end

	if cascadeBound.height < viewRect.height then
        if scrollToBottom then
            disY = viewRect.y - cascadeBound.y
        else
            disY = viewRect.y + viewRect.height - cascadeBound.y - cascadeBound.height
        end
    else
        if cascadeBound.y > viewRect.y then
            disY = viewRect.y - cascadeBound.y
        elseif cascadeBound.y + cascadeBound.height < viewRect.y + viewRect.height then
            disY = viewRect.y + viewRect.height - cascadeBound.y - cascadeBound.height
        end
    end

	if 0 == disX and 0 == disY then
		return
	end

    local posX, posY = scrollView.scrollNode:getPosition()
    scrollView.position_ = cc.p(posX + disX, posY + disY)
    scrollView.scrollNode:setPosition(scrollView.position_)
end
```

_*更新*：以上改动已挪到[yszheda/quickx-extensions](https://github.com/yszheda/quickx-extensions)的UIScrollView或UIListView中。_


## lua语言相关 ##
### bool转数字 ###

```lua
function MyPackage.bool2number(bool)
    return bool and 1 or 0
end
```

### table相关 ###

```lua
function MyPackage.removeValueFromArray(array, value)
    local idx
    for i, v in ipairs(array) do
        if v == value then
            idx = i
            break
        end
    end
    if idx then
        table.remove(array, idx)
    end
end

function MyPackage.hasValueInArray(array, value)
    local hasValue = false
    for i, v in ipairs(array) do
        if v == value then
            hasValue = true
            break
        end
    end
    return hasValue
end
```

### UTF8字符串 ###
cocos2d-x的label默认为UTF8编码，一般场景下主要需要以下两个功能：

- 字符串长度

- 截取子串

原先本渣用cocos2d-x时写了个C++函数来求长度：
```cpp
long long utf8StringSize(const std::string& str)
{
    char* charArray = new char[str.length() + 1];
    strcpy(charArray, str.c_str());
    char* s = charArray;
    /*-----------------------------------------------------------------------------
     *  References: http://stackoverflow.com/questions/4063146/getting-the-actual-length-of-a-utf-8-encoded-stdstring
     *-----------------------------------------------------------------------------*/
    long long len = 0;
    while (*s) len += (*s++ & 0xc0) != 0x80;
    delete [] charArray;
    return len;
}
```

cocos2d-x `Helper`也提供了接口来做字符串截取：
```cpp
static std::string getSubStringOfUTF8String(const std::string& str,
                                   std::string::size_type start,
                                   std::string::size_type length);
```

在lua方面，quickx已经提供`string.utf8len`来求字符串长度，本渣仿照其实现写了个截取子串的函数：
```lua
function MyPackage.utf8str(str, start, num)
    local function utf8CharSize(char)
        local size = 0

        local arr = {0, 0xc0, 0xe0, 0xf0, 0xf8, 0xfc}
        local size = #arr
        while arr[size] do
            if char >= arr[size] then
                break
            end
            size = size - 1
        end

        return size
    end

    local startIdx = 1
    while start > 1 do
        local char = string.byte(str, startIdx)
        startIdx = startIdx + utf8CharSize(char)
        start = start - 1
    end

    local endIdx = startIdx
    while num > 0 do
        if endIdx > #str then
            endIdx = #str
            break
        end
        local char = string.byte(str, endIdx)
        endIdx = endIdx + utf8CharSize(char)
        num = num - 1
    end

    return str:sub(startIdx, endIdx - 1)
end
```

不过目前lua5.3已经有UTF8库，可以不用自行造轮子了。另外，关于其他UTF8相关的lua问题可以参考[Lua Unicode](http://lua-users.org/wiki/LuaUnicode)。

## 其他Helper Functions ##

### 更新view的callbackWrapper ###

我们经常碰到如下的情景：
游戏向后端请求数据，在拿到数据之后执行某个callback去更新某个view。
这种网络请求通常是异步的，如果所请求的数据回来时相关的view被释放，则执行操作该view的callback会导致问题（例如访问非法内存地址）。
这时候我们可以用`tolua.isnull`来判断相关的view对象是否被释放。
由于每个这种类型的callback都有必要加上这样的guard code，所以本渣干脆做了如下的接口：

```lua
function MyPackage.callbackWrapper(views, callback)
    return function(...)
        for _, view in pairs(views) do
            if tolua.isnull(view) then
                return
            end
        end
        if callback ~= nil then
            callback(...)
        end
    end
end
```

### 拿到一个node九个端点的坐标 ###

```lua
--[[--
get the nine positions of a node (the following variables are defined in display.lua of quickx):
display.CENTER
display.LEFT_TOP
display.CENTER_TOP
display.RIGHT_TOP
display.CENTER_LEFT
display.CENTER_RIGHT
display.BOTTOM_LEFT
display.BOTTOM_RIGHT
display.BOTTOM_CENTER
]]
function MyPackage.getPositionOfNode(node, alignType)
    if not node or tolua.isnull(node) then
        return
    end

    local size = node:getContentSize()
    if size.width == 0 and size.height == 0 then
        size = node:getCascadeBoundingBox()
    end

    local pos = cc.p(node:getPosition())
    local anchorPoint = cc.p(node:getAnchorPoint())

    if alignType == display.LEFT_TOP or
        alignType == display.LEFT_CENTER or
        alignType == display.LEFT_BOTTOM then
        pos.x = pos.x - size.width * anchorPoint.x
    elseif alignType == display.CENTER_TOP or
        alignType == display.CENTER or
        alignType == display.CENTER_BOTTOM then
        pos.x = pos.x - size.width * anchorPoint.x + size.width * 0.5
    elseif alignType == display.RIGHT_TOP or
        alignType == display.RIGHT_CENTER or
        alignType == display.RIGHT_BOTTOM then
        pos.x = pos.x - size.width * anchorPoint.x + size.width
    end

    if alignType == display.BOTTOM_LEFT or
        alignType == display.BOTTOM_CENTER or
        alignType == display.BOTTOM_RIGHT then
        pos.y = pos.y - size.height * anchorPoint.y
    elseif alignType == display.CENTER_LEFT or
        alignType == display.CENTER or
        alignType == display.CENTER_RIGHT then
        pos.y = pos.y - size.height * anchorPoint.y + size.height * 0.5
    elseif alignType == display.TOP_LEFT or
        alignType == display.TOP_CENTER or
        alignType == display.TOP_RIGHT then
        pos.y = pos.y - size.height * anchorPoint.y + size.height
    end

    return pos
end
```

### 在某个container中加入sprite，可指定根据container大小进行缩放及对齐方式 ###

```lua
function MyPackage.displaySpriteOnContainer(sprite, container, scaleToFit, alignType)
    if tolua.isnull(container) then
        return
    end
    
    -- default settings
    local scaleToFit = (scaleToFit ~= false)
    local alignType = alignType or display.CENTER
    
    if not tolua.isnull(sprite) then
        local originSize = sprite:getContentSize()
        if originSize.width == 0 or originSize.height == 0 then
            originSize = sprite:getCascadeBoundingBox()
        end
    
        local targetSize = container:getContentSize()
        if targetSize.width == 0 or targetSize.height == 0 then
            targetSize = container:getCascadeBoundingBox()
        end
    
        if scaleToFit then
            sprite:setScale(targetSize.width / originSize.width, targetSize.height / originSize.height)
        end
    
        -- NOTE: ignore container's anchor point
        local pos = MyPackage.getPositionOfNode(container, alignType)
        local leftBottomPos = MyPackage.getPositionOfNode(container, display.LEFT_BOTTOM)
        local posX = pos.x - leftBottomPos.x
        local posY = pos.y - leftBottomPos.y
        display.align(sprite, alignType, posX, posY)
        container:addChild(sprite)
    end
end
```
