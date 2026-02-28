Title: cocos2d-x中的auto-batching
Date: 2015-06-08 02:00:00
description: Auto-batching in cocos2d-x
Tags: cocos2d-x, CS, tech, cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20150608-auto-batch-in-cocos2d-x
Category: tech

本渣比较懒，就直接从工作邮件挑一部分放上来哈～

1.神马是GL calls？

GL calls也称batch，可以单纯理解成绘制次数，一般来说CPU向GPU发送batch会造成瓶颈，这个指标越小越好。

2.如何降低GL calls？

通常我们会在测试版的屏幕左下角看到一些指标，其中GL verts是需要绘制的总顶点数，一般是让每个batch的顶点数越多越好。cocosd-x引擎提供了auto batching的机制，在一定条件下，对于多个同一纹理（事实上是纹理、shader、blendFunc都需要一样）的`node`，只需要一次GL call。

3.auto batching原理？

引擎在绘制场景时会遍历每个`node`，调`node`的`draw`函数：以前`draw`函数会直接绘制`node`，但3.0之后的版本改为向一个叫`RenderQueue`的队列push绘制命令，并不马上渲染。在渲染时从该queue拿出命令，如果连续的命令都是纹理A，那么A只需要一个batch，但如果中间插入了一个纹理B，则无法只用一个batch。

例如：`RenderQueue`中是AAAAABAAAAA，则需要三个batches。

4.auto-batching/`RenderQueue`中连续的条件？

`node`在向`RenderQueue` push命令时会先对子节点排序（排序按照`localZOrder`，`localZOrder`一样就比较子节点添加的顺序），排完序再依次push相应子节点的绘制命令。`RenderQueue`会根据`globalZOrder`再排一次序。所以最后`RenderQueue`中顺序是先按`globalZOrder`、再按`localZOrder`、最后按子节点添加到父节点的顺序。

PS. `node`默认的`globalZOrder`和`localZOrder`都为0

5.现有的系统如何用auto-batching？

- 为同一纹理的UI元素都设同一个大于0的`globalZOrder`：可以保证一定只有一次batch。

- 为同一纹理的UI元素都设同一个大于0的`localZOrder`：推荐使用。`localZOrder`可以直接在UI编辑器里改，但有一定限制和技巧

    * 如果同一纹理的UI元素的parent都是同一个`node`，这种情况比较简单，直接在UI编辑器改即可（如果同一纹理的UI元素在编辑器中都放在一块添加，则也已经被auto batch了，不用改）。

    * 如果同一纹理的UI元素的parent不是同一个`node`（这种情况在各处用`UIListView`的地方很常见），不一定能被auto-batch到，要具体看在`RenderQueue`里是否连续。希望cocos2d-x引擎能继续优化auto-batching机制以方便处理这一情况。

6.如何判读改的东西被auto-batch？

代码中给它设一个专有的大于0的`globalZOrder`，看看GL calls是否减少。不变则说明之前的改动已被auto batch。

# 参考资料 #

- [1][COCOS2D V30 RENDERER PIPELINE ROADMAP](http://www.cocos2d-x.org/wiki/Cocos2d_v30_renderer_pipeline_roadmap)

- [2]“笨木头”大神这篇讲得挺好，安利一下[Cocos2d-x Auto-batching 浅浅的”深入分析”](http://www.benmutou.com/archives/1006)

- [3][COCOS2DX 3.0 优化提升渲染速度 Auto-batching](http://blog.csdn.net/kaitiren/article/details/30478695)

- [4][10行代码看自动Batch，10行代码看自动剔除](http://blog.csdn.net/fansongy/article/details/26968473)

- [5][cocos2dx auto culling 和 auto batching](http://blog.csdn.net/cloud95/article/details/40046697)

- [6][自动批处理（Auto-batching）](http://www.cocoachina.com/bbs/read.php?tid-200808.html)
