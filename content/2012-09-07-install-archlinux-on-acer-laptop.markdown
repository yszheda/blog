Title: 在Acer笔电安装Archlinux小记
Date: 2012-09-07 20:20:00
description: Install Archlinux on Acer Laptop
Tags: linux, CS, tech, Archlinux, Linux, linux, acer, Acer, laptop, V3-571G, 安装, 宏基, 笔电, 笔记本电脑
Slug: 20120907-install-archlinux-on-acer-laptop
Category: tech
这是一篇12年的旧文，我从wordpress博客的草稿箱中挖出了这个坟，内容大体不变，只是用Markdown语法改了一下～

<!-- more -->

之前在家里的老台式上折腾过archlinux，arch的快速、轻量和高定制性给我很不错的印象。不过在自己笔电和实验室的台式上我还是主要用ubuntu，这个让我入门linux的发行版也伴我度过了两三年的时光。一个月前我入手了Acer的V3-571G，对于原装的正版win7我各种配置无力，于是再次装arch的念头越来越强，索性再次折腾起来，加入不折腾不死的Arch党XDD

# 前期 #

其实也没啥准备工作，预备好一个空白分区，照着万能的[Archwiki](https://wiki.archlinux.org/)做就可以了XD

不过，我比以前多做了一些配置，例如把root、home、swap等分区放到[LVM](https://wiki.archlinux.org/index.php/LVM)上。这是因为以前遇到过装了太多软件包、导致root分区空间不足的问题，而LVM可以动态调整分区大小，后来果然派上了用场。

# driver（驱动） #
现在到了安装驱动的时候了，这一步无疑是最耗时间的～

## 硬件一览 ##
先来大致看下这台笔电的配置：

Acer aspire V3-571G-53214G1TMakk:

- CPU: i5-3210M

- GPU: NVIDIA GeForce GT 640M + Intel HD Graphics 4000

- RAM: 4GB

- HD: 1T, 5400RPM

## Graphics（显卡） ##
我一开始只用Intel集显，便用了[Bumblebee](https://wiki.archlinux.org/index.php/Bumblebee)关掉了N卡。
后来我需要写CUDA程序，不得不用到N卡了，刚好看到[一篇博文](http://pavanky.com/archlinux-cuda-on-ivy-bridge-kepler/)介绍了如何在Ivy-Bridge架构CPU（Intel i7-3610QM）和Kepler架构GPU（NVIDIA GT650M）的arch上配置CUDA环境，我便照做了，目前仍可以正常编译和运行CUDA程序。

## Audio（声卡） ##
我试过[OSS (Open Sound System)](https://wiki.archlinux.org/index.php/Open_Sound_System)无效，于是用了[ALSA (Advanced Linux Sound Architecture)](https://wiki.archlinux.org/index.php/Advanced_Linux_Sound_Architecture)。

## Ethernet（有线网卡） ##
有线网卡是Broadcom BCM57785，无需特殊配置。

## Wi-Fi（无线网卡） ##
无线网卡是Broadcom BCM43228。博通的Linux无线网卡驱动素来“臭名昭著”——这可是Arch wiki的用词XD——不幸的是，Acer的这台笔电也是博通的无线网卡，而且也许是这张卡比较新，[Linux Wireless wiki](https://wireless.wiki.kernel.org/welcome)上尚未有对应的驱动信息，所以我只能照着arch wiki所提供的几个驱动一个个试过来，折腾了不少时间。
最后的结论是`b43`驱动不可用，需要用`broadcom-wl`（更新：目前已有dkms版`broadcom-wl-dkms`，推荐使用，否则内核每次更新都需要手动配置`wl`内核模块）。

另外，我还在`/etc/udev/rules.d/10-network.rules`文件中绑定了有线网卡和无线网卡的MAC地址：
```
SUBSYSTEM=="net", ATTR{address}=="", NAME="eth0"
SUBSYSTEM=="net", ATTR{address}=="", NAME="eth1"
```

## Webcam ##
linux-uvc驱动已经是kernel的一部分了，所以无需特殊配置。

## Touchpad ##
安装`xf86-input-synaptics`包，根据[wiki](https://wiki.archlinux.org/index.php/Touchpad_Synaptics)去调配置文件`/etc/X11/xorg.conf.d/10-synaptics.conf`的参数。我所用的配置如下：

```
Section "InputClass"
        Identifier "touchpad catchall"
        Driver "synaptics"
        MatchIsTouchpad "on"
        MatchDevicePath "/dev/input/event*"
        Option "TapButton1" "1"
        Option "TapButton2" "2"
        Option "TapButton3" "3"
        Option "VertEdgeScroll" "on"
        Option "VertTwoFingerScroll" "on"
        Option "HorizEdgeScroll" "on"
        Option "HorizTwoFingerScroll" "on"
        Option "CircularScrolling" "on"
        Option "CircScrollTrigger" "2"
        Option "EmulateTwoFingerMinZ" "40"
        Option "EmulateTwoFingerMinW" "8"
        Option "CoastingSpeed" "0"
EndSection
```

关于Synaptics的配置可以参考[PT桑的博文](http://blog.ptsang.net/configuring_laptop_synaptics_touchpad_in_linux)。

## 功能键 ##
这里先说明，我所用的桌面环境是KDE。

当我装了ALSA之后，调节音量的功能键（Fn+volume）就可以用了（或许是装了kmix？）。

至于调节屏幕亮度的功能键（Fn+brightness），则需要在`/etc/default/grub`的`GRUB_CMDLINE_LINUX`一项中加入
`acpi_backlight=vendor`，然后更新`grub.cfg`。


# 后记 #

我在以下BBS中分享了一些折腾驱动的经验，希望能帮助他人少走弯路～

[1]https://bbs.archlinux.org/viewtopic.php?pid=1150676#p1150676

[2]https://www.ptt.cc/bbs/Linux/M.1348061522.A.5D3.html

以下几位大牛恰好也在用Acer这个型号的笔电，也有选择Arch的折腾党同好呢！XD

[3]http://stianlagstad.no/running-linux-on-acer-aspire-v3-571g/

[4]http://yodalee.blogspot.tw/2012/08/blog-post_20.html
