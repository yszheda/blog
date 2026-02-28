Title: MPI Debug Tips
Date: 2013-06-08 00:12:00
description: Tips for debugging MPI program
Tags: tech, CS, MPI, debug, MPI, valgrind, memcheck, padb, gdb, debug, parallel programming, 并行程序, 平行程式, 调试, 除錯
Slug: 20130608-mpi-debug-tips
Category: tech
debug一个并行程序（parallel program）向来是件很麻烦的事情（```Erlang```等functional programming language另当别论），
对于像MPI这种非shared memory的inter-process model来说尤其如此。

## 与调试并行程序相关的工具 ##

### 非开源工具 ###

目前我所了解的商业调试器（debugger）有：

- [TotalView](http://www.roguewave.com/products/totalview.aspx)
- [Allinea DDT](http://www.allinea.com/products/ddt/)

据说parallel debug的能力很屌，
本人没用过表示不知，
<del>说不定只是界面做得好看而已</del>。
不过我想大部分人应该跟本屌一样是用不起这些商业产品的，
<del>高富帅们请无视</del>。
以下我介绍下一些有用的open source工具：

### 开源工具 ###

#### - [Valgrind Memcheck](http://valgrind.org) #####

首先推荐```valgrind```的```memcheck```。
大部分MPI标准的实现（implementation）（如[openmpi](http://www.open-mpi.org/)、[mpich](http://www.mpich.org/)）支持的是C、C++和Fortran语言。
Fortran语言我不了解，但C和C++以复杂的内存管理（memory management）见长可是出了名的XD。
有些时候所谓的MPI程序的bug，不过是一般sequential程序常见的内存错误罢了。
这个时候用memcheck检查就可以很容易找到bug的藏身之处。
你可能会争论说你用了RAII（Resource Allocation Is Initialization）等方式来管理内存，
不会有那些naive的问题，
但我还是建议你使用memcheck检查你程序的可执行文件，
因为memcheck除了检查内存错误，
还可以检查message passing相关的错误，
例如：MPI\_Send一块没有完全初始化的buffer、
用来发送消息的buffer大小小于MPI\_Send所指定的大小、
用来接受消息的buffer大小小于MPI\_Recv所指定的大小等等，
<del>我想你的那些方法应该对这些不管用吧？</del>。

这里假设你已经安装并配置好了memcheck，例如如果你用的是openmpi，那么执行以下命令

```bash
ompi_info | grep memchecker
```
会得到类似

```bash
MCA memchecker: valgrind (MCA v2.0, API v2.0, Component v1.6.4)
```
的结果。
否则请参照[Valgrind User Manual 4.9. Debugging MPI Parallel Programs with Valgrind](http://valgrind.org/docs/manual/mc-manual.html#mc-manual.mpiwrap)进行配置。

使用memcheck需要在compile时下```-g```参数。
运行memcheck用下面的命令：
```
mpirun [mpirun-args] valgrind [valgrind-args] <application> [app-args]
```

<!-- more -->

#### - [Parallel Application Debugger](http://padb.pittman.org.uk/) ####

padb其实是个job monitor，它可以显示MPI message queue的状况。
推荐padb的一大理由是它可以检查deadlock。

## 使用gdb ##

假设你没有parallel debugger，不用担心，我们还有gdb这种serial debugger大杀器。

首先说说mpirun/mpiexec/orterun所支持的打开gdb的方式。

openmpi支持：
```
mpirun [mpirun-args] xterm -e gdb <application>
```
执行这个命令会打开跟所指定的进程数目一样多的终端——一下子蹦出这么多终端，神烦~——每个终端都跑有gdb。
我试过这个方式，它不支持application带有参数的[app-args]情况，
而且进程跑在不同机器上也无法正常跑起来——这一点[openmpi的FAQ](http://www.open-mpi.org/faq/?category=debugging)已经有<del>比较复杂的</del>解决方案。

mpich2支持：
```
mpirun -gdb <application>
```
但在mpich较新的版本中，该package的进程管理器（process manager）已经从MPD换为Hydra，这个```-gdb```的选项随之消失。
详情请猛戳这个链接(http://trac.mpich.org/projects/mpich/ticket/1150)。
像我机器上的mpich版本是3.0.3，所以这个选项也就不能用了。
如果你想试试可以用包含MPD的旧版mpich。

好，以下假设我们不用上述方式，只是像debug一般的程序一样，打开gdb，attach到相应进程，完事，detach，退出。
<!--- 使用gdb来debugMPI程序 --->
现在我们要面对的一大问题其实是怎么让MPI程序暂停下来。
因为绝大多数MPI程序其实执行得非常快——写并行程序的一大目的不就是加速么——很多时候来不及打开gdb，MPI程序就已经执行完了。
所以我们需要让它先缓下来等待我们打开gdb执行操作。

目前比较靠谱的方法是在MPI程序里加hook，这个方法我是在UCDavis的Professor Matloff的主页上看到的(猛戳这里：http://heather.cs.ucdavis.edu/~matloff/pardebug.html)。
不过我喜欢的方式跟Prof.Matloff所讲的稍有不同：

```c
#ifdef MPI_DEBUG
int gdb_break = 1;
while(gdb_break) {};
#endif
```

Prof. Matloff的方法没有一个类似```MPI_DEBUG```的macro。
我加这个macro只是耍下小聪明，让程序可以通过不同的编译方式生成debug模式和正常模式的可执行文件。
如果要生成debug模式的可执行文件，只需在编译时加入以下参数：
```
-DMPI_DEBUG
```
或
```
-DMPI_DEBUG=define
```
如果不加以上参数就是生成正常模式的可执行文件了，不会再有debug模式的副作用（例如在这里是陷入无限循环）。
不用这个macro的话，要生成正常模式的可执行文件还得回头改源代码，
这样一者可能代码很长，导致很难找到这个hook的位置；
二者如果你在「测试-发布-测试-...」的开发周期里，debug模式所加的代码经常要「加入-删掉-加入-...」很是蛋疼。

（
什么？你犯二了，在源代码中加了一句

```c
#define MPI_DEBUG
```
好吧，你也可以不改动这一句，只需在编译时加入
```
-UMPI_DEBUG
```
就可以生成正常模式的可执行文件。
）


这样只需照常运行，MPI程序就会在while循环的地方卡住。
这时候打开gdb，执行

```
(gdb) shell ps aux | grep <process-name>
```
找到所有对应进程的pid，再用
```
(gdb) attach <pid>
```
attach到其中某一个进程。

Prof. Matloff用的是
```
gdb <process-name> <pid>
```
这也是可以的。
但我习惯的是开一个gdb，要跳转到别的进程就用```detach```再```attach```。

让MPI程序跳出while循环：
```
(gdb) set gdb_break = 0
```
现在就可以随行所欲的执行设breakpoint啊、查看register啊、print变量啊等操作了。

我猜你会这么吐嘈这种方法：每个process都要set一遍来跳出无限循环，神烦啊有木有！
是的，你没有必要每个process都加，可以只针对有代表性的process加上（例如你用到master-slave的架构那么就挑个master跟slave呗~）。

神马？「代表」很难选？！
我们可以把while循环改成：
```c
while(gdb_break)
{
	// set the sleep time to pause the processes
	sleep(<time>);
}
```
这样在<time>时间内打开gdb设好breakpoint即可，过了这段时间process就不会卡在while循环的地方。

神马？这个时间很难取？取短了来不及，取长了又猴急？
好吧你赢了......

类似的做法也被PKU的Jinlong Wu (King)博士写的[调试并行程序](http://dsec.pku.edu.cn/~jinlong/gdb/gdb.html)提及到了。
他用的是：
```
setenv INITIAL_SLEEP_TIME 10
mpirun [mpirun-args] -x INITIAL_SLEEP_TIME <application> [app-args]
```
本人没有试过，不过看起来比改源代码的方法要优秀些XD。

## 其他 ##

假设你在打开gdb后会发现```no debugging symbols found```，
这是因为你的MPI可执行程序没有用于debug的symbol。
正常情况下，你在compile时下```-g```参数，
生成的可执行程序（例如在linux下是ELF格式，ELF可不是「精灵」，而是Executable and Linkable Format）中会加入DWARF（DWARF是<del>对应于「精灵」的「矮人」</del>Debugging With Attributed Record Format）信息。
如果你编译时加了```-g```参数后仍然有同样的问题，我想那应该是你运行MPI的环境有些库没装上的缘故。
在这样的环境下，如果你不幸踩到了segmentation fault的雷区，想要debug，
可是上面的招数失效了，坑爹啊......
好在天无绝人之路，只要有程序运行的错误信息（有core dump更好），
依靠一些汇编（assmebly）语言的常识还是可以帮助你debug的。

这里就简单以我碰到的一个悲剧为例吧，
BTW为了找到bug，我在编译时没有加优化参数。
以下是运行时吐出的一堆错误信息（555好长好长的）：
```
$ mpirun -np 2 ./mandelbrot_mpi_static 10 -2 2 -2 2 100 100 disable
[PP01:13214] *** Process received signal ***
[PP01:13215] *** Process received signal ***
[PP01:13215] Signal: Segmentation fault (11)
[PP01:13215] Signal code: Address not mapped (1)
[PP01:13215] Failing at address: 0x1123000
[PP01:13214] Signal: Segmentation fault (11)
[PP01:13214] Signal code: Address not mapped (1)
[PP01:13214] Failing at address: 0xbf7000
[PP01:13214] [ 0] /lib64/libpthread.so.0(+0xf500) [0x7f6917014500]
[PP01:13215] [ 0] /lib64/libpthread.so.0(+0xf500) [0x7f41a45d9500]
[PP01:13215] [ 1] /lib64/libc.so.6(memcpy+0x15b) [0x7f41a42c0bfb]
[PP01:13215] [ 2] /opt/OPENMPI-1.4.4/lib/libmpi.so.0
(ompi_convertor_pack+0x14a) [0x7f41a557325a]
[PP01:13215] [ 3] /opt/OPENMPI-1.4.4/lib/openmpi/mca_btl_sm.so
(+0x1ccd) [0x7f41a1189ccd]
[PP01:13215] [ 4] /opt/OPENMPI-1.4.4/lib/openmpi/mca_pml_ob1.so
(+0xc51b) [0x7f41a19a651b]
[PP01:13215] [ 5] /opt/OPENMPI-1.4.4/lib/openmpi/mca_pml_ob1.so
(+0x7dd8) [0x7f41a19a1dd8]
[PP01:13215] [ 6] /opt/OPENMPI-1.4.4/lib/openmpi/mca_btl_sm.so
(+0x4078) [0x7f41a118c078]
[PP01:13215] [ 7] /opt/OPENMPI-1.4.4/lib/libopen-pal.so.0
(opal_progress+0x5a) [0x7f41a509be8a]
[PP01:13215] [ 8] /opt/OPENMPI-1.4.4/lib/openmpi/mca_pml_ob1.so
(+0x552d) [0x7f41a199f52d]
[PP01:13215] [ 9] /opt/OPENMPI-1.4.4/lib/openmpi/mca_coll_sync.so
(+0x1742) [0x7f41a02e3742]
[PP01:13215] [10] /opt/OPENMPI-1.4.4/lib/libmpi.so.0
(MPI_Gatherv+0x116) [0x7f41a5580906]
[PP01:13215] [11] ./mandelbrot_mpi_static(main+0x68c) [0x401b16]
[PP01:13215] [12] /lib64/libc.so.6(__libc_start_main+0xfd) [0x7f41a4256cdd]
[PP01:13215] [13] ./mandelbrot_mpi_static() [0x4010c9]
[PP01:13215] *** End of error message ***
[PP01:13214] [ 1] /lib64/libc.so.6(memcpy+0x15b) [0x7f6916cfbbfb]
[PP01:13214] [ 2] /opt/OPENMPI-1.4.4/lib/libmpi.so.0
(ompi_convertor_unpack+0xca) [0x7f6917fae04a]
[PP01:13214] [ 3] /opt/OPENMPI-1.4.4/lib/openmpi/mca_pml_ob1.so
(+0x9621) [0x7f69143de621]
[PP01:13214] [ 4] /opt/OPENMPI-1.4.4/lib/openmpi/mca_btl_sm.so
(+0x4078) [0x7f6913bc7078]
[PP01:13214] [ 5] /opt/OPENMPI-1.4.4/lib/libopen-pal.so.0
(opal_progress+0x5a) [0x7f6917ad6e8a]
[PP01:13214] [ 6] /opt/OPENMPI-1.4.4/lib/openmpi/mca_pml_ob1.so
(+0x48b5) [0x7f69143d98b5]
[PP01:13214] [ 7] /opt/OPENMPI-1.4.4/lib/openmpi/mca_coll_basic.so
(+0x3a94) [0x7f6913732a94]
[PP01:13214] [ 8] /opt/OPENMPI-1.4.4/lib/openmpi/mca_coll_sync.so
(+0x1742) [0x7f6912d1e742]
[PP01:13214] [ 9] /opt/OPENMPI-1.4.4/lib/libmpi.so.0
(MPI_Gatherv+0x116) [0x7f6917fbb906]
[PP01:13214] [10] ./mandelbrot_mpi_static(main+0x68c) [0x401b16]
[PP01:13214] [11] /lib64/libc.so.6(__libc_start_main+0xfd) [0x7f6916c91cdd]
[PP01:13214] [12] ./mandelbrot_mpi_static() [0x4010c9]
[PP01:13214] *** End of error message ***
--------------------------------------------------------------------------
mpirun noticed that process rank 1 with PID 13215 
on node PP01 exited on signal 11 (Segmentation fault).
--------------------------------------------------------------------------
```

注意到这一行：
```
[PP01:13215] [10] /opt/OPENMPI-1.4.4/lib/libmpi.so.0
(MPI_Gatherv+0x116) [0x7f41a5580906]
```
通过（这跟在gdb中用disas指令是一样的）
```
objdump -D /opt/OPENMPI-1.4.4/lib/libmpi.so.0
```
找到MPI\_Gatherv的入口：
```
00000000000527f0 <PMPI_Gatherv>:
```
找到(MPI\_Gatherv+0x116)的位置（地址52906）：
```
   52906:       83 f8 00                cmp    $0x0,%eax
   52909:       74 26                   je     52931 <PMPI_Gatherv+0x141>
   5290b:       0f 8c 37 02 00 00       jl     52b48 <PMPI_Gatherv+0x358>
```
地址为52931的<PMPI\_Gatherv+0x141>之后的code主要是return，%eax应该是判断是否要return的counter。
现在寄存器%eax就成了最大的嫌疑，有理由<del> 相信 </del>猜某个对该寄存器的不正确操作导致了segmentation fault。
<del>好吧，其实debug很多时候还得靠猜，
记得有这么个段子：
「师爷，写代码最重要的是什么？」
「淡定。」
「师爷，调试程序最重要的是什么？」
「运气。」
</del>

接下来找到了%eax被赋值的地方：
```
   52ac2:       41 8b 00                mov    (%r8),%eax
```

这里需要了解函数参数传递（function parameter passing）的调用约定（calling convention）机制：

- 对x64来说：int和pointer类型的参数依次放在```rdi```、```rsi```、```rdx```、```rcx```、```r8```、```r9```寄存器中，float参数放在```xmm```开头的寄存器中。

- 对x86（32bit）来说：参数放在堆栈（stack）中。
此外GNU C支持：
```c
__attribute__((regparm(<number>)))
```
其中<number>是一个0到3的整数，表示指定<number>个参数通过寄存器传递，由于寄存器传参要比堆栈传参快，因而这也被称为#fastcall#。
如果指定
```c
__attribute__((regparm(3)))
```
则开头的三个参数会被依次放在```eax```、```edx```和```ecx```中。
（关于```__attribute__```的详细介绍请猛戳[GCC的官方文档](http://gcc.gnu.org/onlinedocs/gcc/Function-Attributes.html)）。

- 如果是C++的member function，别忘了隐含的第一个参数其实是object的```this```指针（pointer）。

回到我们的例子，
%r8正对应MPI\_Gatherv的第五個参数。
现在终于可以从底层的汇编语言解脱出来了，让我们一睹MPI\_Gatherv原型的尊容：
```c
int MPI_Gatherv(void *sendbuf, int sendcnt, MPI_Datatype sendtype, 
                void *recvbuf, int *recvcnts, int *displs, 
                MPI_Datatype recvtype, int root, MPI_Comm comm)
```
第五个参数是```recvcnts```，于是就可以针对这个「罪魁祸首」去看源程序到底出了什么问题了。
这里我就不贴出代码了，
bug的来源就是我当时犯二了，以为这个```recvcnts```是byte number，而实际上官方文档写得明白（这里的```recvcounts```就是```recvcnts```）：
```
recvcounts
integer array (of length group size) containing the number of elements that are received from each process (significant only at root)
```
其实是```the number of elements```啊有木有！不仔细看文档的真心伤不起！
也因为这个错误，使我的```recvcnts```比```recvbuf```的size要大，因而发生了access在```recvbuf```范围以外的内存的情况（也就是我们从错误信息所看到的```Address not mapped```）。

最后再提一点，我源代码中的```recvbuf```其实是malloc出来的内存，也就是在heap中，这种情况其实用```valgrind```应该就可以检测出来（如果```recvbuf```在stack中我可不能保证这一点）。所以，骚念们，编译完MPI程式先跑跑```valgrind```看能不能通关吧，更重要的是，写代码要仔细看API文档减少bug。

## 参考资料 ##

[1][Open MPI FAQ: Debugging applications in parallel](http://www.open-mpi.org/faq/?category=debugging)

[2][Using Valgrind's Memcheck Tool to Find Memory Errors and Leaks in MPI and Serial Applications on Linux](https://computing.llnl.gov/code/memcheck/)

[3][Valgrind User Manual 4. Memcheck: a memory error detector](http://valgrind.org/docs/manual/mc-manual.html)

[4][stackoverflow: How do I debug an MPI program?](http://stackoverflow.com/questions/329259/how-do-i-debug-an-mpi-program)

[5][Hints for Debugging Parallel Programs](http://heather.cs.ucdavis.edu/~matloff/pardebug.html)

[6][Compiling and Running with MPICH2 and the gdb Debugger](http://www.ncsa.illinois.edu/UserInfo/Resources/Hardware/CommonDoc/mpich2_gdb.html)

[7][调试并行程序](http://dsec.pku.edu.cn/~jinlong/gdb/gdb.html)
