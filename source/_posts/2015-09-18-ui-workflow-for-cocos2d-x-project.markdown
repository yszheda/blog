---
layout: post
title: "cocos2d-x前端开发UI流程"
date: 2015-09-18 23:22
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment, cocostudio, TexturePacker
description: UI Workflow for Cocos2d-x Client Development
---

手游前端开发中有一项很基础的流程，就是把美术资源拼成程序能用的UI界面。由于cocos2d-x并没有一套成熟的工具链，我们最开始是由美术大大们出效果图和切图资源，然后我们码农根据效果图，在`C++`代码中写设置位置、大小等界面逻辑。这种原始的人肉写界面代码的方法需要编译、链接、运行后才能看到最终的界面效果，如果效果不满意还需要重新来一遍，无疑大大降低了开发效率——说起来都是泪啊555......在经过一个多月挣扎之后，我们后来采用了`cocostudio` v1.0这个编辑器。虽然`cocostudio`还很不成熟，要让美术大大们上手也有难度，这项工作还是我们码农来做的，但相比之前好多了：`cocostudio` v1.0可以自动生成一个界面UI的配置json文件及其所需要的多张图集，免去了许多界面代码的编写和调试，而且将多张图片合并成图集可以减少draw calls开销。可是，随着系统越做越多，这一编辑器的弊端就越发明显。除了这个工具本身的bug导致各种所见非所得、给开发带来不便以外，由它自动生成的图集也带来了严重的问题：

一是我们无法指定图集里有哪些图片。这又引发了不同系统共用的图片被加到不同图集里的问题，因为我们无法把共用图片管理起来，去指定UI编辑器使用共用的资源、不要把共用图片和每个系统各自的图片放到同一张图集里。后来我们开始做多语言版本，无法管理图集里的图片资源这一问题就更为严重了。
<!--
：因为同一张图片多语言版本的，图片大小一变，由`cocostudio`切分的多张图集。
-->

二是该UI编辑器生成的图集对图片的packing算法并不理想，导致图集尺寸和文件大小偏大，而图片尺寸和大小一直是cocos2d-x游戏内存和存储空间占用的大头。

本渣虽然早就有心想针对这些问题去革新这套UI流程，无奈大家的开发工作一直繁重。最近正好运营市场的大大们不知怎么就拍脑袋要给我们游戏换皮，把目前所有的UI界面全部换掉。趁着这么个<del>劳民伤财的</del>机会，本渣研究出一套更好的UI流程，因此也被组里暂时<del>甩给这个烫手山芋</del>委以前端开发负责人的重任，带领大家在有限的时间内按照新流程去完成换皮......

<!-- more -->

# 目标(Goal) #

- 支持指定图集里的碎图，方便多语言版本开发。

- 优化图集大小，支持重用图片资源。

- 为了防止不同图集下有同名图片造成sprite frame名字冲突，最好要有类似namespace的机制。

- 尽可能便捷。

# 策略(Strategy) #

- 采用能支持指定图集碎图的`cocostudio` v2.1beta版本编辑器。v2.1beta版导出的不是之前v1.0版所生成的`json`文件，而是`csb``二进制文件，加载还会快一些。我们之所以不用v2.1正式版而用beta版，是因为该正式版还有一些v2.1beta版所没有的bug。

- 图集用`TexturePacker`生成，不采用`cocostudio`导出的图集。`TexturePacker`的packing显然比`cocostudio`要专业的多，而且也有更多选项和更丰富的功能。

- 为了防止不同图集下有同名图片造成sprite frame名字冲突，每一个图集都在sprite frame名字里加上独一无二的路径名。

- 确定了UI编辑器和图集生成工具后，只需要让`cocostudio`导出的csb知道正确的sprite frame、png和plist名称就可以了。

# 工具(Tools) #

- `TexturePacker`，用于生成图集。

- `cocostudio` v2.1beta，用于编辑UI界面。

- `Python2`或者`bash`环境，用于运行相关脚本。

  * `Python`环境需要安装`lxml`库：先安装`pip`，然后运行`pip install lxml`。

# 流程(Workflow) #

1.最开始，我们首先创建两个文件夹`tp_proj`和`cs_proj`，分别作为`TexturePacker`和`cocostudio`项目和资源文件的目录。因为我们需要做多语言版本，这两个目录底下再根据语言种类创建一系列目录：`en`、`fa`、`de`等等。这些目录都要做版本控制。

2.由本渣把被多个系统共用的资源整理出来——呼呼，幸好UI主美大大是个很有条理的大好人，帮本渣整理了绝大部分，发张好人卡嘻嘻——拷到公共资源目录（例如`tp_proj/${lang}/common1/common1`）下，每个人把各自要做的系统资源也拷到单独的目录下（例如武将系统的拷到`tp_proj/${lang}/hero1/hero1`）。

- __注意：由于`TexturePacker`导入资源的需要，这里必须是两级目录！__第二个`common1`决定了`TexturePacker`生成的sprite frame名称遵循`common1/${spriteFrameName}`的格式，这就是之前所提到的防止名字冲突的做法。

- 同理，同一目录下的文件当然不能同名。

- 至于为何需要`common1`、`hero1`后面的数字下面会提到。

3.在`TexturePacker`中将第一级目录（例如`tp_proj/${lang}/common1`）拖进右边的Sprites栏，导出的plist和png指定到项目的目标资源目录下。plist和png的命名还是按规范来（例如上例就是`common1.png`和`common1.plist`）。这时候点击Publish按钮就可以生成图集了。

{% img /images/ui-workflow/1_1_tp.png %}

{% img /images/ui-workflow/1_2_tp.png %}

- __注意：在`TexturePacker`的"Size constraints"选项里选Any Size，不要选择默认的POT！__

- `TexturePacker`的tps项目文件统一放到第一级目录（例如`tp_proj/${lang}/common1`）下，和图片一起提交到版本控制里。

- 至于图集的最大尺寸（"Max Size"）下面会再讨论。

- 最好保存下`TexturePacker`项目文件tps，将它加到版本控制中。

4.新建`cocostudio`项目，导入资源时选择之前放图片的二级目录（例如`tp_proj/${lang}/common1/common1`）：

{% img /images/ui-workflow/2_1_import.png %}

{% img /images/ui-workflow/2_2_import.png %}

{% img /images/ui-workflow/2_3_import.png %}

5.新建合图(Sprite Sheet)文件，注意文件名必须是之前`TexturePacker`所导出的图集名字：

{% img /images/ui-workflow/3_1_csi.png %}

{% img /images/ui-workflow/3_2_csi.png %}

{% img /images/ui-workflow/3_3_csi.png %}

6.在合图文件中把相应的导入资源拖进去：

{% img /images/ui-workflow/4_1_csi.png %}

这时资源左上角会有记号：

{% img /images/ui-workflow/4_3_csi.png %}

- _注意：右侧的设置（如“最大尺寸”）要与`TexturePacker`的设置一致。_

{% img /images/ui-workflow/4_2_csi.png %}

- _注意：如果你之前的plist和png文件的实际资源目录和cocos资源搜索路径不同（比方说实际资源目录是资源搜索路径下的atlases目录），做好合图文件后需要在`cocostudio`新建一个atlases文件夹，把所有合图文件移到atlases下。只是因为目前项目搜索路径不包括atlases，需要把这一相对路径写入对应的csb里，否则`cocos2d-x`的`SpriteFrameCache`将无法正确找到图集。_

7.现在可以新建Node/Layer/Scene来做具体某个系统的界面了，资源都是直接用导入的图片，接下来都是平常做UI的流程了。不过最好别引入`cocostudio`默认的UI资源，例如按钮默认的图片，把按钮三种状态的图都填了：

{% imgcap /images/ui-workflow/5_1_button.png '这是cocostudio默认的按钮三种状态的图' %}

{% imgcap /images/ui-workflow/5_2_button.png '[不推荐的方式]没有指定按钮disabled状态的图片' %}

{% imgcap /images/ui-workflow/5_3_button.png '[推荐的方式]指定按钮三种状态的图片' %}

- 关于`cocostudio` v2.1beta使用注意事项，之后会继续谈。

8.点击Publish，这时候我们只需要把`cocostudio`项目目录中res下的csb文件拷到资源目录下面就可以啦！

{% img /images/ui-workflow/6_2_publish.png %}

当然，别忘了把`cocostudio`项目相关的图片、ccs、csd、csi等文件都加到版本控制里。

{% img /images/ui-workflow/6_1_proj.png %}

9.对于多语言版本，一般很少需要做编辑UI界面的改动，只需要更新对应`tp_proj/${lang}`下的图片资源，生成相应的图集即可。

# Q&A #

- __Q. 图集做多大？__

- A:
根据cocos2d-x的[官方说法](http://www.cocos2d-x.org/wiki/Max_size_of_textures_in_cocos2d-x_depends_on_each_platform)，一般是2048x2048，除非需要支持龊设备才用1024x1024。


- __Q. 做某个系统UI的图集超过上述最大尺寸肿么办？__

- A:

  + 其实`TexturePacker`是支持分多张图集的，但我们不采用，否则在`cocostudio`中做合图文件必须保证合图文件和图集的sprite frame名字完全一致，这对于这种方案很麻烦。

  + 当图集超尺寸时就把多出的图放到新目录下（例如`tp_proj/${lang}/common2/common2`，这就是需要加数字的原因啦！），直到每个目录做的图集都在最大尺寸内为止（其实就是bin packing问题哈，不过反正我们做UI又不需要求最优解是吧？XD）。以后加新资源都先往数字最大的目录下加，图集超尺寸就继续建新目录。

- __Q. UI图片资源有更新肿么办？__

- A:

  - 更新图集目录（例如`tp_proj/${lang}/common2/common2`）的图片再重新生成图集就可以了。

    - 如果图集变大超过尺寸参考上一个问题。

  - 如果想在`cocostudio`看到最新的改动，需要再重新导入资源，因为`cocostudio`会把资源拷贝一份到自己项目目录下的`cocostudio`目录。这可能麻烦一点，但本渣已经帮你想好了，为此写了个`bash`脚本用`rsync`把`TexturePacker`项目的图片都同步到指定的或者所有`cocostudio`项目的`cocostudio`目录，你先把`cocostudio`关了，运行同步脚本就好。神马？你用的是windows不支持shell脚本？哎唷大熊弟，干嘛用渣win这种系统啊......好吧，本渣终于找到了个能用的`Python`的仿`rsync`库，现在也有`Python`版脚本啦！

- __Q. 我做的系统里一些图片资源以前被其他系统用到，我不想把它们放入新的图集，如何找到它们放在哪个图集里？__

- A:
图片同名自然好找的啦，那样你就不用问了。如果不同名呢？嘿嘿，本渣早就想到了，写好了[脚本](https://gist.github.com/yszheda/05382886bdbd3abd279a)，支持搜索与指定的文件内容相同的文件、以及搜索所有与指定目录里文件内容相同的文件：

{% include_code find_texture.py lang:python %}

- __Q. 我想把一些图片资源从一张图集里移到另一张图集里，或者把某些图片删掉，会影响到用到这些资源的`cocostudio`项目，该怎么办？__

- A:
在`cocostudio`里手动操作？当然可以啊，但是神烦！
本渣也考虑到了，好在`cocostudio`项目文件不过就是些`XML`嘛，果断写了一些自动化脚本。
你只需要把`cocostudio`下的资源整理好（例如移动或删除）——相信聪明的你已经想到：只需要把`TexturePacker`项目所管理的图片资源整理好，运行下前面提到的同步脚本就可以，不用再在`cocostudio`项目里再整理一遍——运行下`refresh_cocostudio_proj.sh`就可以了：

{% include_code cocostudio/bash/refresh_csi.sh lang:bash %}

{% include_code cocostudio/bash/refresh_csd.sh lang:bash %}

{% include_code cocostudio/bash/refresh_ccs.sh lang:bash %}

{% include_code cocostudio/bash/refresh_cocostudio_proj.sh lang:bash %}

肿么又是shell？用渣win的筒子们，本渣没有放弃你们，有`Python`版！还好，这些写起来可没有之前找`rsync`的`Python`库那么麻烦......
这些脚本都放到了[这里](https://github.com/yszheda/cocostudio_scripts)

对了，你们最后还是需要打开`cocostudio`发布一下csb的，因为`cocostudio`代码没公开，本渣不造它是肿么生成二进制文件的，否则早就想放脚本里了......

- __Q. 每次往图集项目目录里添加或修改图片后都要打开`TexturePacker`点publish吗？__

- A:
不用，因为`TexturePacker`有命令行工具，本渣又写好了脚本......你懂的。

- __Q. 之前提到`TexturePacker`有一些选项（例如"Size constraints"选项）不能用默认值，如果我忘了改怎么办？__

唉，本渣造你们和我一样懒啦，早就写了批量更新`TexturePacker`的tps项目文件的[脚本](https://gist.github.com/yszheda/655d565e832b38beeb098ccfca68b684)。另外，本渣还发现，tps里记录的是文件的相对路径，由于一些人放的相对路径与项目版本控制主线里的相对路径不一致产生了问题，有的甚至还带有中文路径，脚本里也做了相应的检查和处理。

{% include_code refresh_tps.py lang:python %}

# Future Works #

本渣看到sunjiahua大神写了把`Photoshop`的psd文件转化成`cocostudio`的csd文件的[工具](https://github.com/sunjianhua/PhotoshopLayerToCocosStudioCSD)，如果针对上述流程也有一套psd2csd的工具，那么将会进一步简化流程，提升工作效率。不过大神的工具暂时无法直接拿来用，psd脚本竟然是用混乱邪恶的`js`，还是等本渣有空以后再继续折腾吧......
