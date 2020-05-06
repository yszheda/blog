---
layout: post
title: "瓦片地图注意事项"
date: 2016-06-13 11:22
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment, tile, tiled, tiled map, 瓦片地图, staggered tiled map
description: Tips about Tiled Map in Quick-cocos2d-x
---

承接[上一篇文章](http://galoisplusplus.coding.me/blog/2016/06/03/math-in-staggered-tiled-map/)，再来聊聊一些coding方面的tips：

<!-- more -->

# `TileMapAtlas`、`FastTMX`和`TMXTiledMap`的选择 #

我们看到cocos2d-x提供了三个和TiledMap相关的类：`TileMapAtlas`、`FastTMX`和`TMXTiledMap`，那么应该采用哪个类呢？

- 首先，`TileMapAtlas`官方不建议使用。

- 剩下的两个`C++`类`FastTMX`和`TMXTiledMap`，分别绑定到`lua`的`ccexp.TMXTiledMap`和`cc.TMXTiledMap`。采用`FastTMX`的GL verts（顶点数）较少，可惜暂时不支持staggered类型。所以，staggered类型的Tiled Map只能用`TMXTiledMap`，其它类型的Tiled Map建议采用`FastTMX`。

```
-- NOTE: FastTMX doesn't support staggered tmx
-- ccexp.TMXTiledMap is faster, but the grid will not be displayed normally
local map = cc.TMXTiledMap:create("xxx.tmx")
```

# 如何判断tile坐标超出地图区域 #

`FastTMX`和`TMXTiledMap`提供了一个方法`getMapSize()`，需要注意的是这个函数和cocos2d-x其他`getXXXSize`的函数不同，返回的大小不是以像素值为单位，而是2D地图在两个维度的tile数目。

```
local function isTileInMap(map, tileCoord)
    -- NOTE: mapSize is measured in tile number
    local mapSize = map:getMapSize()

    return (tileCoord.x >= 0)
    and (tileCoord.x < mapSize.width)
    and (tileCoord.y >= 0)
    and (tileCoord.y < mapSize.height)
end
```

# 如何获取tile的标记 #

[上一篇文章](http://galoisplusplus.coding.me/blog/2016/06/03/math-in-staggered-tiled-map/)提到，对于不能放置在地图上禁止被编辑的区域，可以在相应的Tile做上标记。例如，我在Tiled Map里创建了一个叫"meta"的图层：

{% img /images/tiled-map/meta-layer.png %}

在TileSet Properties里设置一个标记"Collidable"，表示禁止被编辑：

{% img /images/tiled-map/tileset-properties.png %}

接下来就是用这个TileSet来刷图啦！

那么我们如何在代码中获取这个标记呢？`FastTMX`和`TMXTiledMap`提供了一个方法`getPropertiesForGID(GID)`来获取GID所对应的tile的属性。
那么新的问题又来了，`GID`这个索引又如何获取呢？还有另一个函数`getTileGIDAt()`，传入的参数就是[上次](http://galoisplusplus.coding.me/blog/2016/06/03/math-in-staggered-tiled-map/)所讲的tile坐标啦！
现在你应该明白之前本渣为何要在那套坐标系下解决判断区域相交的问题了吧？

```
local function isValidTile(map, tileCoord)
    local metaLayer = map:getLayer("meta")
    local flags = 0
    local GID, flags = metaLayer:getTileGIDAt(tileCoord, flags)
    if not GID or GID <= 0 then
        return true
    end

    local property = map:getPropertiesForGID(GID)
    if property and property["Collidable"] then
        return false
    else
        return true
    end
end
```

# 关于tile的坐标 #

[上回](http://galoisplusplus.coding.me/blog/2016/06/03/math-in-staggered-tiled-map/)提到Staggered Tiled Map的坐标系，其实这套坐标还和你的配置有关。本渣采用的配置是：

{% img /images/tiled-map/stagger-setting.png %}

如果改变上述参数，那么你所得到的坐标也会不同，你不妨多试试啦～

另外，即使上述参数不变，但如果你需要由某一点的坐标求出它所在tile的坐标的话，还需要注意Tiled Map的Y轴tile数目（之所以是Y轴，是因为上面`Staggered Axis`设置为`Y`）的奇偶性。这里也不解释了，直接上图最直观：

{% imgcap /images/tiled-map/odd-height-original-coord.png 'Y轴有奇数个tile（图中是五个），这里tile个数是这么算的：从最底端的tile沿斜线算与它有一条公共边的tile、一直算到最顶端的tile，例如从坐标(0, 4)(0, 3)(1, 2)(1, 1)到没有显示的(2, 0)' %}

{% imgcap /images/tiled-map/even-height-original-coord.png 'Y轴有偶数个tile（图中是六个）' %}

# 更多Tiled Map Properties配置 #

`Tile Layer Format`最好选择压缩的格式，这样生成的tmx文件比较小。

{% img /images/tiled-map/tile-layer-format.png %}

# 关于遮挡关系的排序函数 #

[上一篇文章](http://galoisplusplus.coding.me/blog/2016/06/03/math-in-staggered-tiled-map/)还提到建筑及装饰物之间的遮挡关系处理，本渣制定了一套规则来对建筑及装饰物做排序。需要注意的是，lua的`table.sort`要求排序函数是stable的，所以最好给每个要被比较的对象（这里就是建筑或装饰物）一个独一无二的id，对于两者“相等”这种情况就定义为比较id大小即可。

以下给出示例的伪代码，其中`building`就是被封装过的建筑或装饰物对象：

```
local function getLineOfBuildingRegion(building)
    return {
        left = building:getRegionLeftPos(),
        right = building:getRegionRightPos(),
    }
end

local function getDistX(line)
    return line.right.x - line.left.x
end

local function getLowerPoint(line)
    if line.left.y < line.right.y then
        return line.left
    else
        return line.right
    end
end

local function getHigherPoint(line)
    if line.left.y > line.right.y then
        return line.left
    else
        return line.right
    end
end

local function isPointEqual(posA, posB)
    return posA.x == posB.x and posA.y == posB.y
end

local function isLineEqual(lineA, lineB)
    return isPointEqual(lineA.left, lineB.left) and isPointEqual(lineA.right, lineB.right)
end

local function getSlope(line)
    return (line.right.y - line.left.y) / (line.right.x - line.left.x)
end

local function isLineParallel(lineA, lineB)
    return getSlope(lineA) == getSlope(lineB)
end

local function isLowerThanLine(point, line)
    local y = getSlope(line) * (point.x - line.left.x) + line.left.y
    if point.y == y then
        return y > getLowerPoint(line).y
    else
        return point.y < y
    end
end

local function updateBuildingsZOrder(buildings)
    table.sort(buildings, function(a, b)
        if not isValidBuilding(a) then
            return false
        elseif not isValidBuilding(b) then
            return true
        end

        local lineA = getLineOfBuildingRegion(a)
        local lineB = getLineOfBuildingRegion(b)

        if getDistX(lineA) > getDistX(lineB) then
            return isLowerThanLine(getLowerPoint(lineB), lineA)
        elseif getDistX(lineA) == getDistX(lineB) then
            if isLineEqual(lineA, lineB) then
                return a.id < b.id
            elseif isLineParallel(lineA, lineB) then
                if getLowerPoint(lineA).y == getLowerPoint(lineB).y then
                    return a.id < b.id
                else
                    return getLowerPoint(lineA).y > getLowerPoint(lineB).y
                end
            else
                if getLowerPoint(lineA).y > getLowerPoint(lineB).y then
                    return isLowerThanLine(getLowerPoint(lineB), lineA)
                elseif getLowerPoint(lineA).y == getLowerPoint(lineB).y then
                    if getHigherPoint(lineA).y > getHigherPoint(lineB).y then
                        return isLowerThanLine(getLowerPoint(lineB), lineA)
                    elseif getHigherPoint(lineA).y == getHigherPoint(lineB).y then
                        return a.id < b.id
                    else
                        return not isLowerThanLine(getLowerPoint(lineA), lineB)
                    end
                else
                    return not isLowerThanLine(getLowerPoint(lineA), lineB)
                end
            end
        else
            return not isLowerThanLine(getLowerPoint(lineA), lineB)
        end
    end)

    for i, building in ipairs(buildings) do
        building:setLocalZOrder(i)
    end
end
```
