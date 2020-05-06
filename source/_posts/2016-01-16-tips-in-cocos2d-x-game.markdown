---
layout: post
title: "quick-cocos2d-x游戏的tips功能"
date: 2016-01-16 23:23
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, lua, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, game, mobile game, game devolopment
description: tips in cocos2d-x game
---

这次分享一个简单的小功能，在quick-cocos2d-x游戏中实现tips效果，以此作为[之前一篇博文](http://galoisplusplus.coding.me/blog/2015/05/01/quickx-tips/)的后续。tips的行为很简单：点击某个`node`（我们不妨称它为`target_node`）触发，当点击区域在`target_node`范围时出现`tips`，否则隐藏`tips`（有些情况需要指定有效点击范围不在某些node中，我们把这些node称为`exclude_nodes`）；当`target_node`位于屏幕左半边时，`tips`出现在`target_node`右侧；否则`tips`就出现在`target_node`左侧，`tips`和`target_node`有一个固定的水平间距（我们不妨定义为`DEFAULT_TIPS_DIST`）；`tips`和`target_node`底部对齐，但`tips`不能超过屏幕范围。

不废话，先上代码：

```lua
function setupTips(params)
    local targetNode = params.target_node
    local tips = params.tips
    local excludeNodes = params.exclude_nodes or {}

    local DEFAULT_TIPS_DIST = 10
    local TIPS_ZORDER = 1000

    if tolua.isnull(targetNode) or tolua.isnull(tips) then
        return
    end

    tips:setVisible(false)
    targetNode:setTouchEnabled(false)
    display.getRunningScene():addChild(tips, TIPS_ZORDER)

    targetNode:addNodeEventListener(cc.NODE_EVENT, function(event)
        if event.name == "exit" then
            local scene = display.getRunningScene()
            scene:performWithDelay(MyPackage.callbackWrapper({scene}, function()
                if not tolua.isnull(tips) then
                    tips:setVisible(false)
                end
            end), 0)

            local eventDispatcher = display.getRunningScene():getEventDispatcher()
            eventDispatcher:removeEventListenersForTarget(targetNode)
        end
    end)
    ------------------------------------------------------------
    local function setTipsPosition()
        local leftBottomPos = MyPackage.getPositionOfNode(targetNode, display.LEFT_BOTTOM)
        local targetNodePos = display.getRunningScene():convertToNodeSpace(targetNode:getParent():convertToWorldSpace(leftBottomPos))
        local targetNodeAnchorPoint = targetNode:getAnchorPoint()
        local tipsPos = targetNodePos
        local tipsAnchorPoint = cc.p(0, 0)
        local director = cc.Director:getInstance()
        local glView = director:getOpenGLView()
        local frameSize = glView:getFrameSize()
        local viewSize = director:getVisibleSize()

        if targetNodePos.x <= frameSize.width * 0.5 / glView:getScaleX() then
        	-- show tips on the right of the targetNode if the targetNode is on the left screen
            tipsPos.x = tipsPos.x + targetNode:getContentSize().width + DEFAULT_TIPS_DIST
        else
        	-- show tips on the left of the targetNode otherwises
            tipsPos.x = tipsPos.x - DEFAULT_TIPS_DIST
            tipsAnchorPoint.x = 1
        end

        if targetNodePos.y + tips:getContentSize().height > viewSize.height then
            tipsPos.y = viewSize.height
            tipsAnchorPoint.y = 1
        end
        if targetNodePos.y < 0 then
            targetNodePos.y = 0
        end

        tips:ignoreAnchorPointForPosition(false)
        tips:setAnchorPoint(tipsAnchorPoint)
        tips:setPosition(tipsPos)
    end
    ------------------------------------------------------------
    local function activeFunc()
        local scene = display.getRunningScene()
        -- NOTE: delay util the next frame in order to get the correct WorldSpace position
        scene:performWithDelay(MyPackage.callbackWrapper({scene, tips}, function()
            setTipsPosition()
            tips:setVisible(true)
        end), 0)
    end

    local function inactiveFunc()
        if not tolua.isnull(tips) then
            tips:setVisible(false)
        end
    end

    local function isTouchInNode(touch, node)
        if tolua.isnull(node) or tolua.isnull(touch) then
            return false
        end

        local localLocation = node:convertToNodeSpace(touch:getLocation())
        local width = node:getContentSize().width
        local height = node:getContentSize().height
        local rect = cc.rect(0, 0, width, height)
        return getCascadeVisibility(node) and node:isRunning() and cc.rectContainsPoint(rect, localLocation)
    end

    local function isActive(touch)
        local isExcluded = false
        for _, excludeNode in ipairs(excludeNodes) do
            isExcluded = isExcluded or isTouchInNode(touch, excludeNode)
        end
        return isTouchInNode(touch, targetNode) and not isExcluded
    end

    local function onTouchBegan(touch, event)
        if isActive(touch) then
            activeFunc()
            return true
        else
            return false
        end
    end

    local function onTouchMoved(touch, event)
        local scene = display.getRunningScene()
        scene:performWithDelay(MyPackage.callbackWrapper({scene}, function()
            if isActive(touch) then
                activeFunc()
            else
                inactiveFunc()
            end
        end), 0)
    end

    local function onTouchEnded(touch, event)
        local scene = display.getRunningScene()
        scene:performWithDelay(MyPackage.callbackWrapper({scene}, function()
            inactiveFunc()
        end), 0)
    end

    local listener = cc.EventListenerTouchOneByOne:create()
    listener:registerScriptHandler(onTouchBegan, cc.Handler.EVENT_TOUCH_BEGAN)
    listener:registerScriptHandler(onTouchMoved, cc.Handler.EVENT_TOUCH_MOVED)
    listener:registerScriptHandler(onTouchEnded, cc.Handler.EVENT_TOUCH_ENDED)
    listener:registerScriptHandler(onTouchEnded, cc.Handler.EVENT_TOUCH_CANCELLED)
    local eventDispatcher = display.getRunningScene():getEventDispatcher()
    eventDispatcher:removeEventListenersForTarget(targetNode)
    eventDispatcher:addEventListenerWithSceneGraphPriority(listener, targetNode)
end
```

关于`MyPackage.getPositionOfNode`、`MyPackage.callbackWrapper`等helper functions请参见[之前某篇博文](http://galoisplusplus.coding.me/blog/2015/05/01/quickx-tips/)。

上面的代码基本是很简单的，除了有几点需要额外说明一下：

1. 几处调用到`performWithDelay`的地方。这是因为我们用`target_node`的WorldSpace坐标来确定`tips`的位置，当`target_node`位于某个可滚动的node（如`ScrollView`）中时，需要延迟到下一帧才能拿到它正确的WorldSpace坐标，所以我们用了quickx定义的`Node:performWithDelay`来做延时。之所以用这个函数而不用scheduler，是因为它在Node的生命周期中，我们不需要担心如何去安全销毁scheduler所产生的handler。事实上我们只要看一下quickx定义在NodeEx.lua中的`Node:performWithDelay`就一目了然了：
```lua
function Node:performWithDelay(callback, delay)
    local action = transition.sequence({
        cc.DelayTime:create(delay),
        cc.CallFunc:create(callback),
    })
    self:runAction(action)
    return action
end
```

2. 我们指定`target_node`在收到`exit`事件时隐藏`tips`，这是因为`target_node`可能在某些`ClippingNode`（如`ScrollView`）中，当它超出区域不再显示时，`tips`也不应该被显示。

3. 当同一个位置有多个具有`tips`行为的`target_node`时，需要判断当前的`target_node`是否有显示，这需要回溯看父节点的`visibility`，`getCascadeVisibility`定义如下：

```lua
function getCascadeVisibility(node)
    if tolua.isnull(node) then
        return true
    end
    local visibility = node:isVisible()
    if visibility then
        local parent = node:getParent()
        visibility = visibility and getCascadeVisibility(parent)
    end
    return visibility
end
```
