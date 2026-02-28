Title: cocos2d-x实现打字特效
Date: 2015-02-01 02:36:00
description: Typewriting Effect in cocos2d-x
Tags: tech, CS, cocos2d-x, cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 特效, 打字特效, effect, typewriting, 游戏开发, 手游开发, mobile game, game devolopment
Category: tech
Slug: 20150201-label-typewriting-effect
这次分享一个在cocos2d-x中实现打字特效的小功能。

首先，cocos2d-x中label默认是utf8编码，quickx提供了一个`string.utf8len`接口，这里再加一个截取子字符串的函数：
```lua
function utf8str(str, start, num)
    local function utf8CharSize(char)
        if not char then
            return 0
        elseif char > 240 then
            return 4
        elseif char > 225 then
            return 3
        elseif char > 192 then
            return 2
        else
            return 1
        end
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
        local char = string.byte(str, idx)
        endIdx = endIdx + utf8CharSize(char)
        num = num - 1
    end
    return str:sub(startIdx, endIdx - 1)
end
```

第一种实现方式是一开始把每个字符scale到0，延迟一定时间后再scale到原大小：
```lua
-- textDelayTime为每个字显示的延迟时间
function typewriting(label, textDelayTime)
    string = label:getString()
	-- 这里考虑了label可能有换行的情况
    local totalLen = string.utf8len(string) + label:getStringNumLines()
    for i = 1, totalLen do
        local sprite = label:getLetter(i - 1)
        if sprite then
            sprite:setScale(0)
        end
    end
    local textAppear = cc.ScaleTo:create(0, 1)
    for i = 1, totalLen do
        local textDelay = cc.DelayTime:create(textDelayTime * (i - 1))
        local textActionSeq = cc.Sequence:create(textDelay, textAppear)
        local sprite = label:getLetter(i - 1)
        if sprite then
            sprite:runAction(textActionSeq)
        end
    end
end
```

这种实现的效果有跳入感，换一种方式，用visibility来控制：
```lua
-- textDelayTime为每个字显示的延迟时间
function typewriting(label, textDelayTime)
    string = label:getString()
	-- 这里考虑了label可能有换行的情况
    local totalLen = string.utf8len(string) + label:getStringNumLines()
    for i = 1, totalLen do
        local sprite = label:getLetter(i - 1)
        if sprite then
            sprite:setVisible(false)
        end
    end
    local textAppear = cc.Show:create()
    for i = 1, totalLen do
        local textDelay = cc.DelayTime:create(textDelayTime * (i - 1))
        local textActionSeq = cc.Sequence:create(textDelay, textAppear)
        local sprite = label:getLetter(i - 1)
        if sprite then
            sprite:runAction(textActionSeq)
        end
    end
end
```

这种效果也没好多少，最后本渣换了一种思路，不按一个字一个字来runAction了，改为把label作为整体来runAction，在action中去setString，这种方式的效果好多了：
```lua
-- textDelayTime为每个字显示的延迟时间
function typewriting(label, textDelayTime)
    string = label:getString()
	-- 这里考虑了label可能有换行的情况
    local totalLen = string.utf8len(string) + label:getStringNumLines()
	label:setString("")
    local textActions = {}
    for i = 1, totalLen do
        local textDelay = cc.DelayTime:create(textDelayTime)
        local textAppear = cc.CallFunc:create(function()
            label:setString(utf8str(string, 1, i))
        end)
        table.insert(textActions, textDelay)
        table.insert(textActions, textAppear)
    end
    local textActionSeq = cc.Sequence:create(textActions)
    label:runAction(textActionSeq)
end
```
