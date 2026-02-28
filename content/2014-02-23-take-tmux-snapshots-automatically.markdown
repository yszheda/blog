Title: Take Tmux Snapshots Automatically
Date: 2014-02-23 16:12:00
description: Take Tmux Snapshots Automatically
Tags: tmux, cron, tech, CS, tmux, snapshots, cron, bash, shell, 脚本, Archlinux, linux, Linux, UNIX
Slug: 20140223-take-tmux-snapshots-automatically
Category: tech
前段时间学校的EECS楼发生火灾，最近隔三差五停电检修，打断我在server上跑的实验。
而且我习惯上用tmux开多个session和window，一遇到停电我的tmux现场就悲剧了。
复电重开机之后要把tmux现场手动重新建好也很麻烦，于是我就挤出一点时间琢磨着写个简单的script去自动保存和重载tmux的副本。

<!-- more -->

首先我对tmux现场的定义其实还蛮简单的——我希望能记录tmux的session和window的名称、每个pane当前在什么路径以及在跑什么程序。
这些在tmux的man page中都有相应的内建变量（Variable）可以提供，这里谨列举如下：
<table border="1" table-layout:fixed>
	<tr>
		<td> session_name </td>
		<td> Name of session </td>
	</tr>
	<tr>
		<td> window_name </td>
		<td> Name of windown </td>
	</tr>
	<tr>
		<td> pane_current_path </td>
		<td> Current path if available </td>   	
	</tr>
	<tr>
		<td> pane_current_command </td>
		<td> Current command if available </td>
	</tr>
</table>

有了这么给力的内建变量，我们很快就可以写出保存tmux现场的命令了：
```
$ tmux list-windows -a -F"#{session_name} #{window_name} #{pane_current_command} #{pane_current_path}"
```

简单解释一下，tmux的```list-windows```命令顾名思义就是列举窗口，其后可以接以下参数：
```
list-windows [-a] [-F format]  [-t target-session]
```
[-a]自然是指所有窗口；[-F]指定输出格式，我上面那条命令是依次列出session名、window名、pane当前执行程序和pane当前路径，并以空格隔开；[-t]指定输出在哪个session，默认是当前的session，这里我没有用，反正输出结果最后是要被重定向到文件的。

那么有了tmux现场的snapshot之后，我们应该如何恢复现场呢？

首先当然是解析snapshot中的信息，得到\${session\_name}、\${window\_name}、\${pane\_current\_command}、\${pane\_current\_path}的信息。

接下来是把各个session和window恢复好。

tmux稍显繁琐的地方是：用```new-window```创建新的window时必须指定现有的session，假如session不存在，该命令不会创建session，而会报错结束。
所以，当我们恢复每次恢复一个window时，需要先知道它所在的session是否存在：如果存在，则用```new-window```直接在该session上创建window；如果不存在，则需要用```new-session```来创建session，session创建后会有一个默认的窗口，我们就把所要恢复的窗口的环境设定到默认窗口上。

判断session是否存在可以用tmux的```has-session```命令：
```
has-session [-t target-session]
                   (alias: has)
             Report an error and exit with 1 if the specified session does not exist.  If it does exist,
             exit with 0.
```
如果session存在，上述命令的退出码为0，否则则为1。这在bash中只需执行：
```
$ tmux has-session -t "${session_name}" 2>/dev/null
```
之后判断```$?```即可。

假如session不存在，则我用以下命令创建新session，并设默认窗口名为当前所要恢复的窗口的名称：
```
$ tmux new-session -d -s "${session_name}" -n ${window_name}
```

假如session已存在，则我用以下命令在该session上恢复原来的窗口：
```
$ tmux new-window -d -t ${session_name} -n "${window_name}"
```

下面我们要让每个pane都回到原来的路径，我的想法是直接把一个```cd```的shell命令送到当前的pane，并执行这条命令。
在tmux中的解决方案稍微有点小技巧，关键是用```send-keys```命令把该shell命令和一个ENTER送到该窗口，这种方式就像直接在窗口输入上述shell命令再按回车键执行。
以下是跳转回原来路径的tmux完整命令：
```
$ tmux send-keys -t "${session_name}:${window_name}" "cd ${pane_current_path}" ENTER
```

恢复每个pane原来在执行的命令也可以用上述同样的方法。
可惜的是，tmux尽管提供了\${pane\_current\_command}的内建变量，但这个变量却无法提供精确的信息。例如执行的命令是类似```exe arg1 arg2```带参数的形式，\${pane\_current\_command}只会给出```exe```而无法检测到任何参数。因此，当我们重载tmux现场时直接执行\${pane\_current\_command}可能会带来问题。我采取的方案很简单，在每个终端窗口用\${pane\_current\_command}给一个提示，让使用者自行判断恢复后应该执行什么命令。
给出提示的tmux命令可以和之前恢复原路径的命令合并在一起：
```
$ tmux send-keys -t "${session_name}:${window_name}" "cd ${pane_current_path}; echo \"Hint: last time you are executing '${pane_current_command}'.\"" ENTER
```

最后，我想把这个script加到crontab中，所以我需要让它自动判断当前应该做snapshots还是从snapshots恢复tmux现场。
我采用的方式也比较简单，通过```ps```看看当前有没有```tmux```进程：没有的话说明需要恢复，此时先执行```tmux start-server```；有的话则进行snapshots的保存。

完整的脚本如下（或者参考我的[gist](https://gist.github.com/yszheda/9138288)）：
```
#!/bin/bash
tmuxSnapshot=/.tmux_snapshot
tmuxEXE=/usr/local/bin/tmux
save_snap()
{
        ${tmuxEXE} list-windows -a -F"#{session_name} #{window_name} #{pane_current_command} #{pane_current_path}" > ${tmuxSnapshot}
}

restore_snap()
{
        ${tmuxEXE} start-server
        while IFS=' ' read -r session_name window_name pane_current_command pane_current_path
        do
                ${tmuxEXE} has-session -t "${session_name}" 2>/dev/null
                if [ $? != 0 ]
                then
                        ${tmuxEXE} new-session -d -s "${session_name}" -n ${window_name}
                else
                        ${tmuxEXE} new-window -d -t ${session_name} -n "${window_name}"
                fi
                ${tmuxEXE} send-keys -t "${session_name}:${window_name}" "cd ${pane_current_path}; echo \"Hint: last time you are executing '${pane_current_command}'.\"" ENTER
        done < ${tmuxSnapshot}
}

ps aux|grep -w tmux|grep -v grep
if [ $? != 0 ]
then
        restore_snap
else
        save_snap
fi
```

我设了如下的crontab：
```
* * * * * echo "`date`: tmuxEnvSaver is running" >> /tmp/cron-tmux.log 2>&1
* * * * * /home/shuai/tmuxEnvSaver.sh >> /tmp/cron-tmux.log 2>&1
@reboot /home/shuai/tmuxEnvSaver.sh >> /tmp/cron-tmux.log 2>&1
```

这样就可以自动保存和重载简单的tmux现场了。

当然，tmux还有很多内建变量，因此这个简单的脚本还可以继续改进，让snapshots的信息更丰富，偶还是等下次有空再折腾吧XD

## 后续 ##
我搜到一些相关的文章，有用perl来写类似脚本的，可供大家参考：

[1][Preserving (some) session state with tmux and bash](http://blog.edsantiago.com/articles/tmux-session-preserve/)

[2][Resurrecting tmux Sessions After Reboot](http://brainscraps.wikia.com/wiki/Resurrecting_tmux_Sessions_After_Reboot)
