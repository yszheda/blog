---
layout: post
title: "用ab和wrk做压力测试"
date: 2016-07-07 11:22
comments: true
published: true
categories: [Linux, CS, tech]
keywords: ab, wrk, press test, test, 压力测试, 压测, 测试
description: ab and wrk Tips
---

之前一直在做cocos2d-x手游客户端开发，最近被组织上安排去做服务器开发了。虽然一开始接触`OpenResty`，遇到不少问题，但由于本渣重用了大量以前的代码，倒也很快就完成了一个可以正常运作的版本。只是本渣毕竟是新手，所做的功能也没有前人踩坑的经验，对自己代码的性能不放心，所以这段时间也在折腾压力测试，这次就来分享一些做压测的tips。

首先，`Apache`的`ab`可以很方便地产生大量（并发）的同一请求，`ab`上手也很容易，是做简单压测的首选工具之一。

使用`ab`需要注意几个选项：

- `-p`指定POST参数，与`curl`不同，`ab`的POST参数选项必须指定一个文件。

```
       -p POST-file
              File containing data to POST. Remember to also set -T.
```

- `-T`和`-H`指定HTTP Header（前者是`Content-type`）:


```
       -T content-type
              Content-type  header  to  use  for  POST/PUT  data,  eg.  application/x-www-form-urlencoded.  Default is
              text/plain.

       -H custom-header
              Append extra headers to the request. The argument is typically in the form of a valid header line,  con‐
              taining a colon-separated field-value pair (i.e., "Accept-Encoding: zip/zop;8bit").
```

像本渣压测时就用到了如下参数：

```
-H 'Accept-Encoding: gzip' -T 'application/x-www-form-urlencoded'
```

之前manual提到POST必须指定`-T`参数，但如果少了前面的`-H`参数，测出来的数据会和实际情况有偏差。指定`ab`的这些参数最好是和实际的客户端的HTTP header保持一致，个人建议采用`tcpdump`或`Wireshark`等工具来抓取实际的客户端访问服务器的HTTP请求。

- `-s`指定timeout时间，这个参数也最好与实际客户端的设置保持一致。

```
       -s timeout
              Maximum number of seconds to wait before the socket times out. Default is 30 seconds. Available in 2.4.4
              and later.
```

- 需要特别注意的是，`ab`默认不启用HTTP Keep-Alive，需要使用`-k`开启这一特性：

```
       -k     Enable  the  HTTP KeepAlive feature, i.e., perform multiple requests within one HTTP session. Default is
              no KeepAlive.
```

关于HTTP Keep-Alive，下面有两张直观的图说得很明白：

不采用HTTP Keep-Alive，请求某一网页的html和css会通过不同的TCP连接去完成：

{% img https://hpbn.co/assets/diagrams/84cf0f29175e4b11a2343e73105637c5.svg %}

同样的场景，采用HTTP Keep-Alive，就可以在同一TCP连接中请求尽可能多的资源，从而避免建立TCP连接的overhead：

{% img https://hpbn.co/assets/diagrams/cf6057a54f005a288d832d293965ee0d.svg %}

以上两张图是从Ilya Grigorik的[High Performance Browser Networking](https://hpbn.co/)引用过来的，如果你对HTTP Keep-Alive不熟悉的话，可以参考下这本书。

PS. 这里为了不把HTTP Keep-Alive和TCP keepalive混淆起来，本渣就不随Grigorik写做keepalive了。

- 还有另一个需要特别注意的地方，由于`ab`发起的请求都是一模一样的，所以`ab`认为服务器的返回也应该完全相同才对。如果服务器对相同请求的处理结果不同——像本渣做的功能恰好就是这种情况——需要再指定`-l`选项：

```
       -l     Do not report errors if the length of the responses is not constant. This  can  be  useful  for  dynamic
              pages. Available in 2.4.7 and later.
```

前面提到`ab`所产生的请求都是一样的，如果我们想用不同的testcase来做压测呢？这时候`ab`就无能为力了，好在还有其他强大的压测工具，例如[wrk](https://github.com/wg/wrk)。`wrk`支持`lua`编程，可以通过override`request`、`response`的全局函数来指定请求和响应的处理逻辑，这给本渣做压测带来不少便利，因为本渣之前不就是做客户端开发嘛，现在可以直接重用客户端的代码了XD

关于`ab`和`wrk`的具体用法和细节请参考下面的链接，本渣这里就不赘述了，毕竟把别人提过的东西又重复一遍就没什么意思了<del>其实就是懒癌XD</del>

# 参考资料 #

- 阿里云这篇文章[使用ab和wrk对OSS进行benchmark测试](https://yq.aliyun.com/articles/35251)挺好的，推荐一看

- 耗子叔的这篇博文也值得一看：[性能测试应该怎么做？](http://coolshell.cn/articles/17381.html)。在做压测之前应当考虑清楚，设计适当的testcase。

- `ab`的使用可以参考：

  * [Apache ab 压力测试](http://leepiao.blog.163.com/blog/static/485031302010234352282/)

  * [使用Apache Benchmark做压力测试遇上的5个常见问题](http://mo2g.com/view/50/)

  * [linux下ab网站压力测试命令 - post请求](http://www.cnblogs.com/bandbandme/p/3680542.html)

- `wrk`的使用可以参考：

  * [WRK - A HTTP benchmarking tool](http://charmyin.github.io/informationtechnology/2014/08/11/multiple-file-upload-express/)

  * [WRK the HTTP benchmarking tool - Advanced Example](http://czerasz.com/2015/07/19/wrk-http-benchmarking-tool-example/)

  * [wrk — 小巧轻盈的 http 性能测试工具](https://blog.satikey.com/p/5768.html)
