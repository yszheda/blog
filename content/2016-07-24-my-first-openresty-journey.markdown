Title: OpenResty折腾记
Date: 2016-07-24 11:22:00
description: My First OpenResty Journey
Tags: Linux, CS, tech, nginx, OpenResty, docker, cocos2d-x, 游戏开发, 手游开发, mobile game, game devolopment
Slug: 20160724-my-first-openresty-journey
Category: tech

前面几篇文章稍稍提到本渣最近接手了一个server端开发的活，这次就来碎碎念一下好了。虽然我们server端用`OpenResty`，和client端一样主要也是用`lua`开发，不过实在也不是本渣谦虚，本渣一个client端码农，肿么就被叫去写server端代码捏？<del>是因为组织上对本渣的信任。</del>是因为啊，我们server端想要实现战斗这块功能。而这块功能呢，恰好client端已经实现过。本渣嘛，又承担过不少战斗功能的开发工作。所以组织上说，既然你以前在client端挖过不少这种坑，那么server端的坑也由你来挖吧？于是本渣就<del>念了两句诗</del>接了这活。

本渣从一开始接手开始，就打定主意直接在server端重用client端的战斗功能代码。一方面是因为本渣很懒，已经实现过的轮子不想再造一遍；另一方面是因为我们client端的这块代码仍在迭代中，会不时上一些新类型的战斗玩法，如果server端再重新实现一遍，以后还得把client端新的改动也搬过来，这不仅不好维护，而且又是翻倍的工作量。最好就是把client端的战斗功能代码当做server端代码的一个submodule，client端有改动的话就直接pull下更新来使用。client端的这部分代码虽然也是`lua`写的，但要重用的话有个问题：我们client端用了`cocos2d-x`和`quick-x`，但server端只是个Web API Server，最好避免引入`cocos2d-x`和`quick-x`的`C++` API、以及`Node`之类的view（嗯，MVC的view）相关对象。好在最开始做战斗的大神设计得当，把战斗功能划分为战斗计算模块和战斗表现模块——前者计算出手先后、技能释放、buff和属性值改变等等，生成战报；后者再根据前者所生成的战报，播放相应的特效动画和人物动作——等到半年后本渣接手时，为了实现独立的战报播放功能，又把这块代码重构了，去掉了两个模块之间的耦合，所以战斗计算模块基本是独立于`cocos2d-x`和`quick-x`的`C++`代码、与view完全无关的纯`lua`实现。本渣只需要再补上`quick-x`中一些如`math.round`的全局函数的定义，很快就能在server端跑通了，但是新的问题又来了：

1. 有一定概率出现全局函数没有定义的错误，但是在代码里，这些全局函数在定义后并没有被修改。

2. 在用`nginx` start或reload的方式创建新的`nginx` worker进程后，第一次访问有很大概率会失败。

由于本渣是第一次接触`OpenResty`，这些问题一开始让本渣丈二和尚摸不着头脑，后来才渐渐理清了头绪。
前一个问题与`OpenResty`的code cache有关。本渣在`nginx`配置里打开了code cache：

```
lua_code_cache on
```

而全局函数的使用是通过`nginx` content阶段的`lua`代码`require`加载定义这些全局函数的文件的。根据`OpenResty`官方对于code cache的说明，只有最开始运行的LuaVM才会去真正加载这些文件，执行那些定义全局函数的代码，所以这些全局函数只有在该LuaVM所在的进程里是被定义的。此后，如果请求被同一个`nginx` worker处理，则可以正常使用之前定义的全局函数；但如果请求被分到不同的worker，就会出现变量没有定义的报错。

至于后一个问题，本渣观察到：在第一次访问时，`nginx` worker的CPU使用量飙升，一定概率导致server端响应时间超过设置的timeout时间，从而被client端认为是超时。
后来本渣继续缩小问题的排查范围，最后将它定位到client端读取并处理策划表的代码上。由于策划表的数据量大，所以这部分代码运行起来比较耗时倒也不奇怪。而前面提到code cache打开时，被`require`的文件只加载一次，这些处理策划表的代码也只有第一次才被真正运行，所以看到的现象就是第一次的请求会经常失败了。

前一个问题与全局函数有关，本渣看到不少`OpenResty`前辈提到[要避免使用全局变量](https://segmentfault.com/a/1190000004297908)：

> 一般来说，在ngx_lua的上下文中使用Lua全局变量真的不是什么好主意：
>
> 1. 滥用全局变量的副作用会对并发场景产生副作用，比如当使用者把这些变量看作是本地变量的时候；
>
> 2. Lua的全局变量需要向上查找一个全局环境（只是一个Lua表），代价比较高；
>
> 3. 一些Lua的全局变量引用只是拼写错误，这会导致出错很难排查。

其中一个重要原因是会对并发场景产生副作用，本渣以前入过并行程序的坑，对这一点是不能同意更多的。不过回头来看我们client端代码里的那些全局“变”量，其实都是全局常量，不仅值不会被改变，而且我们代码中只会对这些常量执行一次赋值操作（当且仅当它们被定义时），这就不存在并发的副作用问题了。对于全局变量访问开销大的问题，本渣写了个脚本，在代码文件开头对使用到的全局变量`local`化（例如`local XXX = require('XXX')`）。拼写错误引发的bug嘛，本渣之前在[svn hook](/2016/03/12/20160312-svn-precommit-hook.html)加了检查，所以在开发过程中提交代码就能及时发现问题。逐条分析下来，倒是命名空间污染不可避免，但是我们server端和client端的代码是完全独立的，命名空间污染并不会引发什么问题。当然严格一点，还是可以把client端涉及到的全局常量全部改成`local`的，写个脚本来处理所有代码也不难。<del>但处理问题要灵活嘛，既然在具体场景里无关紧要为啥还要迷信教条多此一举？嘿嘿，本渣就是这么懒XD</del>不过本渣考虑到client端这块代码仍在持续开发新的功能，这样做会给client端码农的开发带来限制：“喂，大熊弟，乃们的代码server端也要跑的哦，以后不能用全局常量了！”“WTF！”。这种节奏就不太理想了，本渣希望server端的代码重用对client端而言是透明的，client端的大熊弟在挖坑时可以完全无视server端战斗功能的存在：“server端关我鸟事，老子该干嘛还干嘛！”所以i呢，本渣放弃了去掉全局常量的治疗，最终选择在保留client端全局常量的前提下去解决它所带来的问题。

本渣最后解决前面提到的两个问题的黑科技是：把`require` client端代码的部分从`nginx`的content阶段，挪到了`nginx` lua module的init阶段：

![image](https://cloud.githubusercontent.com/assets/2137369/15272097/77d1c09e-1a37-11e6-97ef-d9767035fc3e.png)

init阶段会在`nginx` master进程加载`nginx`配置时执行，之后才由master进程clone出worker进程。全局常量放在这个阶段初始化，就不会有某些worker进程没有定义全局变量的报错；处理策划表的代码放在这个阶段执行，就把CPU开销转移到加载`nginx`配置上，不会增加请求的响应时间，可谓是一石二鸟。

有了一个可行的prototype，接下来本渣最关心的就是性能问题了：毕竟是第一次搞`OpenResty`，没啥经验，万一上线后server不堪重负挂了呢？不过我们做server端的老司机们都对自己开的车很自信，之前从没有写过测试代码，所以单接口压力测试还得本渣这server端小白自行琢磨啦。压测工具中，`Apache`的`ab`还是挺好上手的，输出的信息也很好分析。不过本渣也犯过傻：有一次正和小伙伴吹牛逼呢，说压测出来性能特别棒，一细看就打脸了，原来都是Non-200 response......HTTP code为啥不是200捏？原来本渣是通过写client端`lua`代码来获取POST参数的，本渣的这段代码有bug，导致POST的参数有误。后来bug改掉了，结果小伙伴一脸鄙夷：乃不是可以看server端的access log吗？干嘛非要在client端写代码获取POST参数？......好吧，开森就好......`ab`做压测有个问题，就是POST参数是固定的，但本渣想用不同的战斗来压测自己那块功能，需要让不同请求的POST参数各不相同。最后本渣找到了[`wrk`](https://github.com/wg/wrk)这个压测工具。`wrk`最吸引本渣的，是它支持`lua`编程，普大喜奔啊！本渣这个懒人又可以重用client端的`lua`代码了！XDD

压测结果有了，但要知道性能热点才好对症下药做优化啊。这个时候本渣找到了春哥写的[SystemTap脚本](https://github.com/OpenResty/nginx-systemtap-toolkit)和[火焰图工具](https://github.com/brendangregg/FlameGraph)，这套工具简直是profile神器啊有不有！本渣之前也折腾过cocos2d-x游戏client端的profiler，万万没想到还有内核trace这种玩法！借助春哥所介绍的On-CPU和Off-CPU火焰图，本渣改进了一些问题，例如某些不被`luajit`支持的函数，会被`luajit`解释执行，在火焰图中会有`lj_xxx`的frame。这时候可以看看这些函数能否换成`luajit`支持的函数，像本渣就发现我们client端代码里有不少用`pairs`的地方，其实应该把相应的`lua table`设计成array而非hash table，采用`ipairs`来遍历。

在做压测和做火焰图的时候还发生过意外，有次`nginx` worker进程占满CPU，把开发server卡死了。分析下来是因为某个testcase使client端的战斗计算一直没有达到结束条件，死循环了。这倒也不奇怪，因为我们client端的战斗按照策划大大们的需求就是支持无限回合的。那为虾米在client端不会出现战斗计算死循环导致机器卡死呢？前面提到client端有战斗计算模块和战斗表现模块，这是一个典型的producer-consumer模型：战斗计算模块是producer，生产出若干回合的战报交给战斗表现模块，然后挂起；战斗表现模块是consumer，“消费”当前尚未播放的战报，同时接收玩家的操作信息，转交给战斗计算模块进行新回合的计算。也就是说，这两者总是相继运行的。而server端不存在战斗表现模块，战斗计算模块全部算完后就返回所有回合的战报，所以server端会有卡死问题而client端木有。这个问题大家讨论下来，最后策划大大决定在server端战斗加上战斗最大回合数限制，避免死循环。现在理论上没问题了，但本渣还是不放心：万一哪天代码有个bug会触发死循环呢？一出现问题就搞个大新闻，影响到整台机器，后果很严重啊！本渣首先想到把server端拆成一般业务server和战斗server，把两者隔离开，万一战斗出现问题，其他业务仍可以正常运作；然后对战斗server的`nginx` worker进程要有资源限制，不能让它们拖垮整台机器。最后采用的大杀器也许你已经猜到了，那就是`Docker`！采用`Docker`可以很方便地用`namespace`做环境隔离、用`cgroups`做资源限制，而且`Docker` container本质上是host机的进程，不会有虚拟机的性能降级。

敲定了这一解决方案，接下来的挖坑工作就顺理成章分成了两块：一个是如何把我们server端`Docker`化，另一个是业务server和战斗server如何协作。前者可以被`Docker`化的有`OpenResty`的`nginx`进程、`MySQL`和`redis`实例，好在`OpenResty`、`MySQL`和`redis`都有现成的`Docker`镜像，只需要稍做修改，就可以用到我们这套server端代码上。
`Docker`的构建实在太方便了，本渣也趁着把server端`Docker`化的时候，简化搭建开发server的流程。中间为了解决自动化快速备份现有数据库数据作为开发server数据的问题，折腾了一阵，学到不少东西，不过像`MySQL` `InnoDB`等技术细节还是得找时间扫盲一下～
至于后者，由于一般业务server和战斗server采用的是同一套代码（只是`nginx`配置稍有不同，本渣折腾配置时还踩过`nginx` `if`的坑，[“if is evil”](https://moonbingbing.gitbooks.io/OpenResty-best-practices/content/ngx/if_is_evil.html)啊！），访问的是同样的`MySQL`和`redis`实例，所以只需要考虑这样一个问题：client端在连上一般业务server后，一般业务server如何把战斗相关的请求转给战斗server来处理？[《Openresty最佳实践》](https://moonbingbing.gitbooks.io/OpenResty-best-practices/content/OpenResty/how_request_http.html)介绍了两种最常见的HTTP接口调用方法：

1. `proxy_pass`

2. `cosocket`

这两种方式本渣都折腾过了，最后采用了`proxy_pass`的方式。因为本渣考虑到以后可能会出现战斗server集群的情况，采用`proxy_pass`可以方便在`nginx`配置的`upstream`中配置多个战斗server，做load balance，可拓展性更好。加上我们启动战斗server其实只需要创建新的`Docker`容器，这整套方案可以很容易scale上去。当然，我们游戏目前的访问量还远不需要集群去撑，考虑集群似乎有杀鸡用牛刀之嫌，不过梦想总是要有的，万一我们游戏火了呢XD

嗯，最近就做了这么一点微不足道的工作，本篇也没什么干货，谢谢大家！
