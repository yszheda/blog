---
layout: post
title: "Learn branch prediction from SimpleScalar source (2)"
date: 2013-08-23 16:12
comments: true
published: false
categories: [Branch Prediction, SimpleScalar, Computer Architecture]
keywords: Branch Prediction, SimpleScalar, Computer Architecture, 分支预测, 体系结构, 计算机体系
description: Introduce basic branch prediction concept using the source code of SimpleScalar
---
## branch direction predictor ##

### dynamic branch prediction ###

#### correlated branch predictor ####
前面提到我们用一张被称为PHT（Pattern History Table）的hash table来存放branch指令的跳转历史，我们也解释了这张hash table的entry如何更新以及如何根据entry来作出相应的预测。
接下来的问题是使用什么hash function？
<!--
既然PHT的index是以branch指令的PC（Program Counter）的hash值，那么
-->
最自然的想法当然是以branch指令的PC（Program Counter）作为hash值。
这样的想法已经可以应对简单的branch，可是实际程序中的分支往往很复杂，导致这种简单的实现方式的正确率很低。
导致分支复杂性的一大原因是分支与分支之间存在关联（correlation），即其中某分支是否跳转取决于其他分支的结果。

以SPEC Benchmark中的eqntott程序的一段代码为例：
```c
if(aa == 2)			/*branch-1*/
	aa = O;
if(bb == 2)			/*branch-2*/
	bb = O;
if(aa != bb) {		/*branch-3*/
	...
}
```
branch-3的结果与branch-1和branch-2相关，这种相关性看了下面的branch tree便一目了然：


以branch指令的PC作为hash值的branch predictor无法准确预测像branch-3这种分支，因为这种predictor完全忽略了分支之间的关联性。
这种predictor（假设PHT的entry是2-bit saturating counter）的运作情况如下表所示：


由上表已很难看出branch-3的跳转历史与实际跳转行为的关系，但如果我们从branch path的角度来看，我们便不难发现branch-3实际跳转行为的规律性：


当我们考虑到branch之间的关联性后，我们就可以借助其他branch的跳转结果来预测当前branch指令会遵循什么模式（branch path）。而branch path只需采用一个shift register来记录最近其他branch的跳转结果。这个register的width取决于与该branch相关的分支数目。
以上例来说，由于与branch-3相关的有两个分支，所以这个shift register用2-bit即可。
这个shift register是correlated branch predictor的关键，我们把它称为Branch History Register (BHR)。


#### 2-level branch predictor ####
2-level branch predictor是对correlated branch predictor的进一步拓展。
BHR与PHT一样有三种模式：
- Global
- Per-set
- Per-address


#### gshare branch predictor ####


#### hybrid branch predictor ####


## Branch Target Buffer ##


## Return Address Stack ##

## 参考资料 ##

[1][McFarling S. Combining branch predictors[R]. Technical Report TN-36, Digital Western Research Laboratory, 1993.](http://www.hpl.hp.com/techreports/Compaq-DEC/WRL-TN-36.pdf)

[2][Pan S T, So K, Rahmeh J T. Improving the accuracy of dynamic branch prediction using branch correlation[C]//ACM SIGPLAN Notices. ACM, 1992, 27(9): 76-84.](http://users.ece.gatech.edu/~leehs/ECE6100/papers/Pan92.pdf)

[3][Yeh T Y, Patt Y N. Alternative implementations of two-level adaptive branch prediction[C]//ACM SIGARCH Computer Architecture News. ACM, 1992, 20(2): 124-134.](https://cs.binghamton.edu/~ghose/CS522/papers/yehpattISCA92.pdf)



