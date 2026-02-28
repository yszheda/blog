Title: Upgrading Compilers on CentOS
Date: 2013-11-21 00:45:00
description: upgrading compilers on CentOS-6
Tags: tech, CS, CentOS, clang, llvm, gcc, gdb, 编译器, tmux, cuda
Slug: 20131121-upgrading-compilers-on-centos
Category: tech
这篇日志应该叫「六美分历险记」的，「六美分」顾名思义嘛，自然是指CentOS-6。

下面扯扯为何对本屌来说是「历险」和为虾米要「历险」：
偶对red hat系的向来无爱。当偶还是linux小白时，就曾在虚拟机里折腾过高大上的fedora，没用过多久就遇到了kernel panic啊有木有！差点把小白吓退散了有木有！
后来很长一段时间都是随大众用Ubuntu，接触了Debian系的_dpkg_就果断和_rpm_阵营分道扬镳啊，直到又重新折腾起「中立邪恶」的Arch，现在玩的是非主流的吃豆人(pacman)——<del>还是能把系统滚死的吃豆人哦，刺激吧XD</del>。
在Arch的蛊惑下，偶走向了「追新」的sb之路，不隔三差五来一次upgrade享受之后「咦，居然没挂」的快感简直就像少了什么——<del>何弃疗</del>。
阔素捏，实验室的机器偏偏全是六美分，服务器嘛，要稳定才是王道，这偶也素明事理滴（想起前几天看到<a href="http://www.zhihu.com/question/21421588">知乎某问题</a>，Arch党表示躺中啊XD）。
但是......本屌一看gcc还是4.4.7就不爽啊，package要老至少也要对c++11支持好点吧......
于是一不做二不休，发挥在Arch下折腾的本事，手动更新gcc，顺带把clang也装上。

<!-- more -->

## tmux ##

在折腾gcc和clang之前，偶先把好用的_tmux_装上。
结果```yum install tmux```后六美分就抱怨装不上了，
于是偶直接源代码安装省事。
执行tmux又跑不起来，说是找不到```libevent```的动态链接库。
「这坑爹的」偶暗暗咒骂了句，继续源代码安装libevent-2.0.21-stable。
我执行
```
echo $LD_LIBRARY_PATH
```
查看了下这个系统路径，在执行libevent的```configure```时加上```--prefix=/lib```参数把它安装到```$LD_LIBRARY_PATH```中的```/lib```。```tmux```就搞定了。

## llvm ##

接下来先说说装llvm和clang。照着<a href="http://llvm.org/docs/GettingStarted.html">官方文档</a>做还是挺顺的，没有出现什么问题。
```
# 我把llvm源代码放到~/llvm下
$ cd
$ mkdir llvm
$ cd llvm
# checkout源代码（co是checkout的简写），这是编译器后端部分。
$ svn co http://llvm.org/svn/llvm-project/llvm/trunk llvm
# 再把clang的源代码checkout出来，clang是编译器前端。
$ cd llvm/tools
$ svn co http://llvm.org/svn/llvm-project/cfe/trunk clang
# runtime compiler其实可以不装，我没有安装。
# $ cd ../llvm/projects
# $ svn co http://llvm.org/svn/llvm-project/compiler-rt/trunk compiler-rt
# test suite是可选的，我也没有装。
# $ svn co http://llvm.org/svn/llvm-project/test-suite/trunk test-suite
# 把可执行文件放到一个新建的build目录以免「污染」源代码目录
$ cd ~/llvm
$ mkdir build
$ cd build
# 我把llvm和clang装到/usr/local下
$ ../llvm/configure --prefix=/usr/local
# CPU有16-core就是爽啊！
$ make -j16
$ make install
```

## gcc ##

gcc的安装就没有那么顺了。我装的是4.8.1，一开始执行```./configure```就碰到没有GMP、MPFR和MPC这三个库的抱怨。
好在<a href="http://gcc.gnu.org/install/prerequisites.html">官网的Installing GCC: Prequisites</a>提供了这些库的下载地址，我就去下载源代码编译安装了（用```tmux```同时开几个窗口跑真心爽啊XD）。
好吧，这在<a href="http://gcc.gnu.org/wiki/InstallingGCC">官方文档</a>中是不推荐的，但偶总觉得比装六美分的rpm要靠谱呢。
其实在```./configure```时指定好```--prefix=/lib```参数，动态链接库就可以被系统找到了（只要在```$LD_LIBRARY_PATH```的都可以）。
倒不用像官方文档中吐嘈的需要在执行gcc的```configure```时设置
```
--with-gmp=/some/silly/path/gmp --with-mpfr=/some/silly/path/mpfr --with-mpc=/some/silly/path/mpc
```
并修改```LD_LIBRARY_PATH```。

接下来就是执行```make```了，我遇到了一个错误：
```
error: gnu/stubs-32.h:No such file or directory
```
求助万能的StackOverflow，果然找到了<a href="http://stackoverflow.com/questions/7412548/gnu-stubs-32-h-no-such-file-or-directory">答案</a>。把```glibc-devel```和```libstdc++-devel```这两个软件包装上就行，这次我用的是```yum install```。

PS. 我后来查history发现还执行了
```
sudo yum install glibc-static
```
不太清楚不装这软件包会不会给gcc的安装带来困扰——折腾党们可以自行尝试XD

## 后续 ##

用cuda-gdb调试我的程序时host端的函数出现「symbol not found」的问题（我编译时已经加了```-g```与```-G```参数），运行了以下命令：
```
debuginfo-install glibc libgcc libstdc++ zlib
```
六美分又出现了很多类似的抱怨：
```
Could not find debuginfo pkg for dependency package 
```
把```/etc/yum.repos.d/CentOS-Debuginfo.repo```中的```enabled=0```改为```enabled=1```，再执行一遍```debuginfo-install```就可以了。

可是原本的问题依旧存在，于是怀疑是gdb和4.8.1的gcc合不来。
查了下六美分上的gdb版本，是7.2-50.el6，而最新的已经有7.6.1了。
果断继续源代码更新gdb！

奇怪的是，gdb更新完了，```cuda-gdb -v```还是显示的7.2：
```
NVIDIA (R) CUDA Debugger
5.5 release
Portions Copyright (C) 2007-2013 NVIDIA Corporation
GNU gdb (GDB) 7.2
Copyright (C) 2010 Free Software Foundation, Inc.
（以下省略文字若干）
```
我怀疑是```cuda-gdb```没绑定到最新版的host端gdb，请教了下实验室的SA大大，她直接帮我重装了CUDA5.5的Toolkit，结果还是不行。查了一下Toolkit的官方文档，5.5还不支持gcc4.8.1，杯具，之前的折腾变成挖坑了......好在我把新版的都装到/usr/local/下，/usr/bin/里面的还是六美分原本的老掉牙版本，没有被覆盖......
