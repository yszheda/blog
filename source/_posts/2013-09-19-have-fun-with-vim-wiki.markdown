---
layout: post
title: "have fun with vim wiki"
date: 2013-09-19 15:31
comments: true
categories: [tech, CS]
keywords: vimwiki, github pages, systemd, cron, crontab, github, wiki, 个人wiki, pathogen, cronjob, Archlinux, linux
description: my experience of using vimwiki
---
写blog确实是一种消化和深入理解知识的方式，但往往要整理一个完整的主题相当的耗时间。
平时我也想记一记一些有用然而散乱的tips，慢慢积累起来。
作为一位Vim忠实粉，我理所当然找到了大名鼎鼎的Vim插件[Vimwiki](http://www.vim.org/scripts/script.php?script_id=2226)，
并开始借此搭建我的个人wiki。

用[pathogen](https://github.com/tpope/vim-pathogen)这个管理Vim插件的插件把Vimwiki安装上后，需要在.vimrc中加入一些设置，其中最重要的是指定你所写的wiki源文件的路径和要发布的html文件的路径：
```
let g:vimwiki_list = [{'path': '~/my_site/', 'path_html': '~/public_html/'}]
```
接下来就可以在你所指定的'path'下创建.wiki文件，编辑完后是用以下Vim命令
```
:Vimwiki2HTML
```
Vimwiki插件就会自动将该.wiki文件转化为同名的html页面（例如topic.wiki生成的是topic.html）并把html放到你所指定的'path_html'下。
如果要转化所有条目可以用以下的Vim命令：
```
:VimwikiAll2HTML
```
<!-- more -->

有了html页面，自然想发布到某网站上。我选择了提供pages服务的业界良心Github，创建一个名为wiki的新repo(https://github.com/yszheda/wiki)，把'path_html'上的html文件托管到上面，并通过gh-pages分支发布我的Project pages(http://yszheda.github.io/wiki/)。
页面的样式我偷懒直接使用了Github官方提供的Architect主题，为了让该主题应用到所有Vimwiki生成的html页面上，需要修改Vimwiki插件目录下的```autoload/vimwiki/default.tpl```模板文件：
{% include_code lang:html default.tpl %}

接下来要折腾的就是自动发布Vimwiki生成的html页面了。
我写了一个简单的auto-deploy.sh脚本：
{% include_code auto-deploy.sh %}
再把它设置为定时作业，可以用经典的```crontab```，例如```crontab -e```后加入：
```
* 20 * * * /<path>/auto-deploy.sh
```
设置每日晚上八点自动发布。

不过作为一名Arch user，很早之间就<del>当小白鼠</del>从sysvinit迁移到了systemd，自然要试试这个高大上的```systemd```。
systemd也支持定时作业，以我的例子来讲，我希望每日定时发布，可以从创建一般的daily event开始。

编辑```/etc/systemd/system/timer-daily.timer```文件：
```
[Unit]
Description=Daily Timer

[Timer]
OnBootSec=10min
OnUnitActiveSec=1d
Unit=timer-daily.target

[Install]
WantedBy=basic.target
```

编辑```/etc/systemd/system/timer-daily.target```文件：
```
[Unit]
Description=Daily Timer Target
StopWhenUnneeded=yes
```

创建以下目录，作为接下来要被执行的具体的定时作业的服务设置文件的路径：
```
mkdir /etc/systemd/system/timer-daily.target.wants
```

在该目录下添加具体要被执行的定时作业的服务设置文件```/etc/systemd/system/timer-daily.target.wants/syn-vimwiki.service```：
```
[Unit]
Description=syn vimwiki

[Service]
Nice=19
IOSchedulingClass=2
IOSchedulingPriority=7
ExecStart= /<path>/auto-deploy.sh
```

最后执行
```
systemctl enable timer-daily.timer && systemctl start timer-daily.timer
```
即可。

设置按小时或按星期定时发布也是可以的,
万能的[Arch wiki](https://wiki.archlinux.org/index.php/Systemd/cron_functionality)上都有详细的说明。

关于systemd再多啰嗦几句，迁移到systemd后自然还是可以用原来的```cron```服务的，如果某一天你打了鸡血，突然变激进了，想把cron撤掉换成纯systemd（Arch发行版就经常干这种事XD），在执行
```
systemctl stop cronie && systemctl disable cronie
```
之前，别忘了加入```logrotate```、```man-db-update```、```mlocate-update```、```verify-shadow```这些服务的配置文件。
至于具体的内容，万能的[Arch wiki](https://wiki.archlinux.org/index.php/Systemd/cron_functionality)也早为不折腾不死的你准备好了XD
