---
layout: post
title: "Hello World"
date: 2013-04-12 22:19
comments: true
categories: [tech, CS, octopress]
keywords: octopress, gitcafe, github, pygments, Archlinux, blog, 博客, 个人博客, github pages, gitcafe pages
description: setup Octopress
---
*Octopress*確實是個好東東，花了半小時折騰了下，現在終於可以用*Markdown*來寫blog了！

不過偶還是被它自動生成的_Liquid_模板坑了555，吐嘈一下...

另一個要吐嘈的是在對嵌入的code做syntax highlight時總是無法```rake generate```成功。查到octopress是用_pygments_來做highlight的，但明明在```pygmentize -L```中有顯示的programming language（例如C）卻無法正確被highlight！這不科學！

後來看到這其實是python版本的問題，Archlinux下默認以python開頭的package都是python3的，而octopress所用的**pygments.rb**其實只支持python2！
我也看到octopress的github上有類似的issue，但是我merge了貌似已經fix bug的branch2.1，還是沒有解決問題。

還好之後看到了一個較好的workaround方法：
<http://www.wongdev.com/blog/2013/01/16/octopress-on-archlinux/>
主要是用virtualenvwrapper來產生不同版本python的虛擬環境，關於virtualenvwrapper詳細的介紹可以參見：
[1](http://virtualenvwrapper.readthedocs.org/en/latest/)
[2](https://pypi.python.org/pypi/virtualenv)
[3](https://wiki.archlinux.org/index.php/Python_VirtualEnv)

其實呢，粗暴地把**pygments.rb**中的```#!/usr/bin/env python```的python改成python2很可能也可以的...

PS.
## 关于在gitcafe部署octopress ##

gitcafe上等价于github的gh-pages分支的叫做gitcafe-pages，详见<a href="http://blog.gitcafe.com/116.html">gitcafe的官方blog</a>。
所以首先要改的是把Rakefile里面的所有的gh-pages改为gitcafe-pages。

另外一个要注意的是，第一次配置时会提示"Enter the read/write url for your repository"，那是在指定git remote add origin后边的url。gitcafe的url格式与github的不一样，应该是git@gitcafe.com:your_username/your_username.git，而非git@github.com:your_username/your_username.github.io.git （这个其实就是执行Rakefile里面setup_github_pages这个task，你可以把提示For example那一行修改掉）。

