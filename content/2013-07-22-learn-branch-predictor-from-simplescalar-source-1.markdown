Title: Learn branch prediction from SimpleScalar source (1)
Date: 2013-07-22 17:10:00
description: Introduce basic branch prediction concept using the source code of SimpleScalar
Tags: tech, CS, Branch Prediction, SimpleScalar, Computer Architecture, 分支预测, 体系结构, 计算机体系
Slug: 20130722-learn-branch-predictor-from-simplescalar-source-1
Category: tech
作为一名CSer，最好的学习方式之一无疑是tracing code，看源代码——
不知你此时是否与我一样想起了Linus那句名言「talk is cheap, show me the <del>fucking</del> code!」?
可是对计算机体系结构来说，很多技术直接是由硬件实现的，因而也被蒙上一层神秘的面纱。
好在还有一些模拟器（simulator）软件，例如SimpleScalar(http://www.simplescalar.com/)就是这样一套模拟处理器性能的工具集。
之前我有幸通过做一些project接触SimpleScalar并读了一些cache技术的源代码。
在此我借SimpleScalar源代码为工具介绍branch prediction技术，
也算是对几个月前折腾时光的一种整理吧~

首先先简单介绍下branch prediction是做神马。
branch是instruction sets里面十分常见的一类指令。
一般可以分为：

- conditional branch：只在某条件下才跳转。例如```MIPS```里的```beq```/```bne```等。

- unconditional branch（或简称jump）: 无条件跳转。例如```MIPS```里的```j```/```jr```等。

- 还有一类特殊的跳转指令，就是function call和return。

<!-- more -->

这类指令在一般程序里的出现频率是很高的，据说平均每4至5条指令就会出现一条branch指令，这也是为什么大多数```basic block```都很短的原因。
不幸的是，在我们CPU的pipeline中我们常常要在后面的stage才能得到branch的结果。
显然在fetch到branch指令与resolve出结果之间「漫长」的clock cycle中，我们希望能同时处理之后的指令。
那么在resolve之前我们怎么知道branch之后的指令是什么？
这时候我们就需要branch prediction了。

简单地说，branch prediction要预测的主要是两件事：

- direction：conditional branch是taken还是not taken？

- target：branch指令要跳转的目的地是哪里？除了conditional branch，这也包括function pointer和indirect jump，例如```MPIS```中的```jr```指令就需要在计算出```r31```的值后才知道跳转目标。

针对预测direction的有branch direction predictor；
针对预测target的有一般的BTB(Branch Target Buffer)，
还有针对call和return的RAS(Return Address Stack)。
在SimpleScalar中，branch predictor被定义为以下structure：
```c
/* branch predictor def */
struct bpred_t {
  enum bpred_class class;	/* type of predictor */
  struct {
    struct bpred_dir_t *bimod;	  /* first direction predictor */
    struct bpred_dir_t *twolev;	  /* second direction predictor */
    struct bpred_dir_t *meta;	  /* meta predictor */
  } dirpred;

  struct {
    int sets;			/* num BTB sets */
    int assoc;			/* BTB associativity */
    struct bpred_btb_ent_t *btb_data; /* BTB addr-prediction table */
  } btb;

  struct {
    int size;			/* return-address stack size */
    int tos;			/* top-of-stack */
    struct bpred_btb_ent_t *stack; /* return-address stack */
  } retstack;

  // 以下省略模拟用的状态计数器
}
```
以下我将针对各部分进行介绍。

## branch direction predictor ##

在SimpleScalar中定义了如下的direction predictor类别：
```c
/* branch predictor types */
enum bpred_class {
  BPredComb,            /* combined predictor (McFarling) */
  BPred2Level,			/* 2-level correlating pred w/2-bit counters */
  BPred2bit,			/* 2-bit saturating cntr pred (dir mapped) */
  BPredTaken,			/* static predict taken */
  BPredNotTaken,		/* static predict not taken */
  BPred_NUM
```
其中最后一项```BPred_NUM```只是取巧利用c语言中enum的性质得到predictor种类数目罢了（在c中enum的成员是可以被转化为int类型的，这在强调type safe的c++眼中当然很邪恶，为此c++还有enum class来杜绝这种事），```BPredTaken```和```BPredNotTaken```都属于static prediction，
除此之外的前面三个属于dynamic prediction。


### static branch prediction ###
static branch prediction无疑是最naive的direction predictor，不考虑程序runtime执行的动态信息，只根据当前看到的branch指令来做预测。
SimpleScalar采用了其中最简单的两种策略：

- always taken：总是预测branch不会跳转。

- always not taken：总是预测branch会跳转。

当然这二者预测的准确率就纯靠人品了。
还有稍微高级点的static branch predictor：

- 根据branch target和当前branch指令的pc之间的offset来决定。
如果target在branch指令之前则预测跳转，
如果target在branch指令之后则预测不跳转（backward taken, forward not taken）。
这样的策略是基于程序中常常出现的loop结构，在loop中branch的target通常是backward的。
例如以下这段C代码
```c
for (int i = 0; i < 100; i++) {
	...
}
```
被翻译成类似下面的汇编代码：
```
	addi r1, r0, 0
	addi r2, r0, 100
Lable_loop: ...
	addi r1, r1, 1
	bne r1, r2, Lable_loop
```
如果采用backward taken，则这个loop跑一遍只有最后一次是预测错误，前面九十九次都对了，这就提高了loop结构branch的预测准确率。

- 根据compiler的提示。一般是通过状态寄存器（status register，例如x86体系架构的FLAGS寄存器）来标记branch direction的结果。
（这种策略是把control dependency转化为data dependency。）

### dynamic branch prediction ###

#### counter predictor ####
<!--
最简单的dynamic branch predictor是counter-based predictor。
这种predictor的想法很简单，只要维护有关branch指令跳转与不跳转的历史，下次再遇到同一条指令时就可以根据该历史来做预测了。
-->
这种predictor的原始想法其实很简单，只要维护有关branch指令跳转与不跳转的历史，下次再遇到同一条指令时就可以根据该历史来做预测了。

一般用来存放跳转历史的数据结构是hash table，
hash table的index是以branch指令的PC（Program Counter）的hash值，
那么hash table的entry应该存什么呢？
最简单的想法就是保存该branch指令上一次是taken还是not taken的信息，显然这样的entry只需一个bit就够了。
当下次再遇到这条branch指令时，我们预测跳转的行为跟其历史是一致的。
我们可以认为hash table存放了供预测用的pattern，所以习惯上也把这张表称为PHT（Pattern History Table）。

还是以类似前面那段for循环的代码为例子，为了便于解释我把循环次数减少到5：
```c
for (int i = 0; i < 5; i++) {
	...
}
```
可以被翻译成如下汇编代码：
```
	addi r1, r0, 0
	addi r2, r0, 5
Lable_loop: ...
	addi r1, r1, 1
	bne r1, r2, Lable_loop
```
假设branch的跳转历史初始为Not Taken，则跑一遍上述for循环遇到bne指令的情况如下表：
<table border="1" table-layout:fixed>
	<tr>
		<td> r1的值 </td>
		<td> 1 </td>
		<td> 2 </td>
		<td> 3 </td>
		<td> 4 </td>
		<td> 5 </td>
	</tr>
	<tr>
		<td> branch历史 </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
	</tr>
	<tr>
		<td> 预测 </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
	</tr>
	<tr>
		<td> 实际情况 </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
	</tr>
	<tr>
		<td> 正确性 </td>
		<td> 错误 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 错误 </td>
	</tr>
</table>
于是跑完这个loop一遍的正确率为60%。

这个保存branch上一次是taken还是not taken的entry经常由一个1-bit saturating counter来实现，
这里的saturating是说当counter达到上限（对于1-bit的counter来说是1）时就不再递增，达到下限（对于1-bit的counter来说是0）时就不再递减。
（这也是为什么这种策略被称为counter-based，后面可以看到这也是一种可被拓展的做法。）
对于这种counter-based的实现方法来说，我们要解决的最关键问题是： 

- 如何根据实际的跳转来更新counter？

- 如何根据counter来预测下一次跳转？

假设我们的1-bit saturating counter为1时代表taken，为0时代表not taken，则我们可以这样回答上面两个问题：

- counter每遇到实际是taken的情况就做递增，反之则做递减。

- 如果counter的值为1，则预测下次是taken，否则，预测下次是not taken。

不难看出，这样的1-bit saturating counter忠实地模拟了我们之前所用的”branch历史“的行为。
整个方法的原理图如下图所示：

![image](/images/branch-predictor/bimodal.png)

另外，当我们审视1-bit saturating counter的update logic，我们会发现counter的更新值（新的状态）取决于counter的旧值（旧的状态）和当前branch实际的跳转情况（输入），这是一个finite-state Moore machine：

![image](/images/branch-predictor/FSM-LT.png)

接下来让我们来看看1-bit saturating counter会有什么问题。
假设我们之前例子中的循环体会被执行不止一次——这也是很常见的情况，例如在嵌套循环（nested loop）当中：
```c
for (int j = 0; j < 2; j++) {
	for (int i = 0; i < 5; i++) {
		...
	}
}
```
可以被翻译成如下汇编代码：
```
	addi r3, r0, 0
	addi r4, r0, 2
Outer_loop:	
		addi r1, r0, 0
		addi r2, r0, 5
	Inner_loop: ...
		addi r1, r1, 1
		bne r1, r2, Inner_loop
	addi r3, r3, 1
	bne r3, r4, Outer_loop
```
假设```bne r1, r2, Inner_loop```这条指令的跳转历史初始为Not Taken，同样跑一遍上述for循环遇到```bne r1, r2, Inner_loop```指令的情况如下表：
<table border="1" table-layout:fixed>
	<tr>
		<td> r1的值 </td>
		<td> 1 </td>
		<td> 2 </td>
		<td> 3 </td>
		<td> 4 </td>
		<td> 5 </td>
		<td> 1 </td>
		<td> 2 </td>
		<td> 3 </td>
		<td> 4 </td>
		<td> 5 </td>
	</tr>
	<tr>
		<td> counter </td>
		<td> 0 </td>
		<td> 1 </td>
		<td> 1 </td>
		<td> 1 </td>
		<td> 1 </td>
		<td> 0 </td>
		<td> 1 </td>
		<td> 1 </td>
		<td> 1 </td>
		<td> 1 </td>
	</tr>
	<tr>
		<td> 预测 </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
	</tr>
	<tr>
		<td> 实际情况 </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
	</tr>
	<tr>
		<td> 正确性 </td>
		<td> 错误 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 错误 </td>
		<td> 错误 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 错误 </td>
	</tr>
</table>

通过分析它的行为我们可以发现，由于该counter只根据上一次跳转的行为来做预测，所以在最后跳出循环后，我们的counter立即记下是not taken，这样在下次进入该循环体后我们就只能预测not taken，而一般第一次执行循环体都应该是taken，故而我们的predictor在这种naive的情况下还是mispredict了，那么该如何解决这个问题呢？
解决方案就是在预测时不止看一次历史跳转，而是综合多次历史记录。换言之，让我们的PHT entry不那么敏感（sensitive）。
最简单的一种拓展方式就是每个entry增加一个bit，成为一个2-bit saturating counter。
同样，我们不能避开那两个问题，以下是一种解答：

- counter每遇到实际是taken的情况就做递增，反之则做递减。

- 如果counter最高位（MSB）的值为1，则预测下次是taken，否则，预测下次是not taken。
我们可以相应地把2-bit saturating counter的值解释为：
<table>
	<header>
		<tr>
			<th>counter值</th>
			<th>含义</th>
		</tr>
	</header>
	<body>
		<tr>
			<td>00</td>
			<td>Strongly Not Taken</td>
		</tr>
		<tr>
			<td>01</td>
			<td>Weakly Not Taken</td>
		</tr>
		<tr>
			<td>10</td>
			<td>Weakly Taken</td>
		</tr>
		<tr>
			<td>11</td>
			<td>Strongly Taken</td>
		</tr>
	</body>
</table>


这时我们的finite state machine就如下图：

![image](/images/branch-predictor/FSM-2bit-0.png)

再跑一遍之前的例子。
假设```bne r1, r2, Inner_loop```这条指令的跳转历史初始为Weakly Not Taken，同样跑一遍上述for循环遇到```bne r1, r2, Inner_loop```指令的情况如下表：
<table border="1" table-layout:fixed>
	<tr>
		<td> r1的值 </td>
		<td> 1 </td>
		<td> 2 </td>
		<td> 3 </td>
		<td> 4 </td>
		<td> 5 </td>
		<td> 1 </td>
		<td> 2 </td>
		<td> 3 </td>
		<td> 4 </td>
		<td> 5 </td>
	</tr>
	<tr>
		<td> counter </td>
		<td> 01 </td>
		<td> 10 </td>
		<td> 11 </td>
		<td> 11 </td>
		<td> 11 </td>
		<td> 10 </td>
		<td> 11 </td>
		<td> 11 </td>
		<td> 11 </td>
		<td> 10 </td>
	</tr>
	<tr>
		<td> 预测 </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
	</tr>
	<tr>
		<td> 实际情况 </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Taken </td>
		<td> Not Taken </td>
	</tr>
	<tr>
		<td> 正确性 </td>
		<td> 错误 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 错误 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 正确 </td>
		<td> 错误 </td>
	</tr>
</table>

不难看出，由于2-bit saturating counter正确地处理了1-bit saturating counter在再次进入循环体的预测错误，使得正确率从60%提升到了70%。

值得一提的是，用2-bit counter来实现并非只有上述方法。以下这几种FSM同样可以，例如采用第一个FSM的话，则连续发生两次Not Taken时就设为Strongly Not Taken。

![image](/images/branch-predictor/FSM-2bit-1.png)
![image](/images/branch-predictor/FSM-2bit-2.png)
![image](/images/branch-predictor/FSM-2bit-3.png)

再拓展开去，PHT的entry可以是任意位（bit）的saturating counter，counter的位数（width）越多，predictor的更新就越不敏感。
不过实际上不会用到太多bit，2 bit和3 bit是最常见的（例如Alpha 21264就用的是3-bit saturating counter）。
不过，也许你已经发现了，我们的saturating counter的初始值是有讲究的。上例用的是Weakly Not Taken，其实Weakly Taken也可以，但是如果初始值设为Strongly (Not) Taken，效果就不如人意了。这是因为一开始我们的predictor没有任何历史的信息，让saturating counter变得敏感一些有助于记住正确的pattern。saturating counter的位数越多，设为敏感值的优势越多。

回到SimpleScalar的source code，SimpleScalar所实现的正是上文所讲的2-bit saturating counter（即source code中的```BPred2bit```）。

```c
/* create a branch predictor */
struct bpred_t *			/* branch predictory instance */
bpred_create(enum bpred_class class,	/* type of predictor to create */
	     unsigned int bimod_size,	/* bimod table size */
	     unsigned int l1size,	/* 2lev l1 table size */
	     unsigned int l2size,	/* 2lev l2 table size */
	     unsigned int meta_size,	/* meta table size */
	     unsigned int shift_width,	/* history register width */
	     unsigned int xor,  	/* history xor address flag */
	     unsigned int btb_sets,	/* number of sets in BTB */ 
	     unsigned int btb_assoc,	/* BTB associativity */
	     unsigned int retstack_size) /* num entries in ret-addr stack */
```

```c
/* create a branch direction predictor */
struct bpred_dir_t *		/* branch direction predictor instance */
bpred_dir_create (
  enum bpred_class class,	/* type of predictor to create */
  unsigned int l1size,	 	/* level-1 table size */
  unsigned int l2size,	 	/* level-2 table size (if relevant) */
  unsigned int shift_width,	/* history register width */
  unsigned int xor)	    	/* history xor address flag */
```

如前所述，SimpleScalar的branch direction predictor是一个```struct bpred_dir_t```，``` BPred2bit```的结构定义就在``` struct bpred_dir_t```中：

```c
    struct {
      unsigned int size;	/* number of entries in direct-mapped table */
      unsigned char *table;	/* prediction state table */
    } bimod;
```
```c
/* direction predictor def */
struct bpred_dir_t {
  enum bpred_class class;	/* type of predictor */
  union {
    struct {
      unsigned int size;	/* number of entries in direct-mapped table */
      unsigned char *table;	/* prediction state table */
    } bimod;
    struct {
      int l1size;		/* level-1 size, number of history regs */
      int l2size;		/* level-2 size, number of pred states */
      int shift_width;		/* amount of history in level-1 shift regs */
      int xor;			/* history xor address flag */
      int *shiftregs;		/* level-1 history table */
      unsigned char *l2table;	/* level-2 prediction state table */
    } two;
  } config;
};
```
其中代码注释中的prediction state table就是我们所说的PHT，size表示PHT的entries数目。

让我们先来看看```BPred2bit``` predictor的初始化。首先```bpred_create```函数被调用来创建branch predictor（即```bpred_t```结构），在该函数中```bpred_dir_create```函数被调用来创建direction branch predictor部分（即```bpred_dir_t```结构），```BPred2bit```的初始化就在函数```bpred_dir_create```的以下几行代码中：

```c
  struct bpred_dir_t *pred_dir;
  unsigned int cnt;
  int flipflop;
  // omit some code here...
  switch (class) {
  case BPred2bit:
    if (!l1size || (l1size & (l1size-1)) != 0)
      fatal("2bit table size, `%d', must be non-zero and a power of two", 
	    l1size);
    pred_dir->config.bimod.size = l1size;
    if (!(pred_dir->config.bimod.table =
	  calloc(l1size, sizeof(unsigned char))))
      fatal("cannot allocate 2bit storage");
    /* initialize counters to weakly this-or-that */
    flipflop = 1;
    for (cnt = 0; cnt < l1size; cnt++)
    {
	  pred_dir->config.bimod.table[cnt] = flipflop;
	  flipflop = 3 - flipflop;
    }

    break;
	}
```
这段代码先检查PHT的entries数目（即代码中的```l1size```）是否合法——这个数目取决于用来做index的寄存器的位数（width），如果我们取PC的某$M$位作为index，则entries数目只能是$2^M$。
如果```l1size```合法，则为PHT分配空间。
接下来把PHT的每个entry都初始化为Weakly Not Taken（对于2-bit saturating counter来说就是1）。


<!-- 
也就是branch应当为not taken时，我们的predictor仍然会预测 
-->

(待续)

#### correlated branch predictor ####

#### 2-level branch predictor ####

#### gshare branch predictor ####

#### hybrid branch predictor ####






## 参考资料 ##

[1][McFarling S. Combining branch predictors[R]. Technical Report TN-36, Digital Western Research Laboratory, 1993.](http://www.hpl.hp.com/techreports/Compaq-DEC/WRL-TN-36.pdf)

