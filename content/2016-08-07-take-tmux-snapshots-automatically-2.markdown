Title: Take Tmux Snapshots Automatically (2)
Date: 2016-08-07 16:12:00
description: Take Tmux Snapshots Automatically
Tags: tmux, tech, CS, tmux, snapshots, cron, bash, shell, 脚本, Archlinux, linux, Linux, UNIX
Slug: 20160807-take-tmux-snapshots-automatically-2
Category: tech

还记得本渣以前写的[给tmux现场做备胎的脚本](http://galoisplusplus.coding.me/blog/2014/02/23/take-tmux-snapshots-automatically/)吗？其实后来本渣就没再去拓展[这个脚本](https://gist.github.com/yszheda/9138288)了，不是因为之前的脚本运行得够好不需要再改了，而是在写好那个脚本那年，有一个工具横空出世，让本渣觉得再也不用造轮子了——好了，不卖关子了，这个工具就是`tmux`的[resurrect插件](https://github.com/tmux-plugins/tmux-resurrect)！

resurrect官方有一个[使用录屏](https://vimeo.com/104763018)

<iframe src="https://player.vimeo.com/video/104763018" width="640" height="360" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
<p><a href="https://vimeo.com/104763018">Tmux Resurrect plugin</a> from <a href="https://vimeo.com/brunosutic">Bruno Sutic</a> on <a href="https://vimeo.com">Vimeo</a>.</p>

怎么样？狂拽酷炫屌！我们想要有的功能基本都有了吧！而且resurrect还部分支持[恢复panel里运行的程序](https://github.com/tmux-plugins/tmux-resurrect/blob/master/docs/restoring_programs.md)啊有木有！要知道这并不好实现，以前本渣写备胎脚本时也折腾过，当时还只能在恢复panel时给出上次运行程序的提示。
不过resurrect插件需要手动保存和恢复`tmux`现场，如果需要自动化的话，可以再配合[continuum插件](https://github.com/tmux-plugins/tmux-continuum)来使用。

好了，软文就写到这么多了，下面我们来看看如何安装使用。

首先查看`tmux`版本：

```
tmux -V
```

resurrect插件需要`tmux`1.9以上的版本。如果你的版本低于1.9，那么升级是必须的，其实把`tmux`升级到1.9以上还是蛮推荐的。

这里推荐安装[tpm (Tmux Plugin Manager)](https://github.com/tmux-plugins/tpm)做`tmux`插件管理，再通过`tpm`安装continuum等插件：

```
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

编辑`~/.tmux.conf`，在文件末尾加入以下几行:

```
# Set default shell to zsh
# set-option -g default-shell /bin/zsh

# Use the following line to fix OS X tmux problems
# set-option -g default-command "reattach-to-user-namespace -l zsh"

# List of plugins
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

# Other examples:
# set -g @plugin 'github_username/plugin_name'
# set -g @plugin 'git@github.com/user/plugin'
# set -g @plugin 'git@bitbucket.com/user/plugin'

# Enable automatic restore
set -g @continuum-restore 'on'

# Initialize TMUX plugin manager (keep this line at the very bottom of tmux.conf)
run '~/.tmux/plugins/tpm/tpm'
```

如果你的默认shell是`zsh`，请把这句的注释去掉：

```
set-option -g default-shell /bin/zsh
```

如果你用的是Mac OSX，把这句的注释也去掉：

```
set-option -g default-command "reattach-to-user-namespace -l zsh"
```

这主要是`tmux`在OSX下水土不服（更详细的问题描述可以看这篇文章：[Reattach-to-user-namespace: The Fix for Your Tmux in OS X Woes](http://www.economyofeffort.com/2013/07/29/reattach-to-user-namespace-the-fix-for-your-tmux-in-os-x-woes/)），需要用[reattach-to-user-namespace](https://github.com/ChrisJohnsen/tmux-MacOSX-pasteboard)黑科技，所以你最好也用[*MacPorts*][MacPorts]或者[*Homebrew*][Homebrew]装下这个工具：

```
port install tmux-pasteboard
```

```
brew install reattach-to-user-namespace
```

[MacPorts]: http://www.macports.org
[Homebrew]: http://brew.sh

在终端下执行以下命令更新`tmux`配置，运行`tpm`：
```
tmux source ~/.tmux.conf
```

最后在`tmux`下运行`prefix + I`（如果你没改键绑定的话就是`<Ctrl>-b + <Shift>-i`）安装插件。你还可以通过`prefix + U`（`<Ctrl>-b + <Shift>-u`）更新插件，用`prefix + <Alt> + u`删除插件。

安装完成之后，你可以在`~/.tmux/plugins/`里找到每个插件的代码目录。resurrect插件还有一个`run_tests`脚本用于检查是否安装正确，不过要运行这个脚本需要装上虚拟化神器[vagrant](https://www.vagrantup.com)。

如果安装正确，continuum插件会每隔15分钟产生一份备胎，我们也可以用`prefix + <Ctrl>-s`手动备份，用`prefix + <Ctrl>-r`手动恢复——vimer吐槽一记，这热键定义得好emacs风...

下面我们来看看resurrect插件产生的`tmux`环境备胎。在`tmux`环境备胎生成之后，在`~/.tmux/resurrect/`目录下就会有名为`tmux_resurrect_$(date).txt`的文本文件，同时会有一个叫`last`的软链接指向最新的`tmux_resurrect_$(date).txt`。那么这个神秘的txt文件里有啥呢？这里本渣随意贴上一份：

```
pane    0       0       :apt-fast       1       :*      0       :/home/ys    1       sudo  :sudo apt-fast install linux-image-3.13.0-70-generic-dbgsym
pane    0       1       :~      0       :       0       :/home/ys    1       zsh     :
pane    0       2       :~      0       :-      0       :/home/ys    1       zsh     :
window  0       0       1       :*      c51d,95x28,0,0,0
window  0       1       0       :       c51e,95x28,0,0,1
window  0       2       0       :-      c51f,95x28,0,0,2
state   0
```

啊哈，看起来思路和本渣[之前脚本](https://gist.github.com/yszheda/9138288)的[思路](http://galoisplusplus.coding.me/blog/2014/02/23/take-tmux-snapshots-automatically/)差不多嘛！只不过resurrect插件记录的信息更详细，还做了键绑定。resurrect的代码也不难懂，如果你对它的实现感兴趣的话可以去阅读一下啦～
