---
layout: post
title: "小记Linux/UNIX下错删文件恢复"
date: 2016-02-02 22:43
comments: true
published: true
categories: [Linux, CS, tech]
keywords: Linux, linux, 文件恢复, recover, lsof, extundelete, debugfs, PhotoRec
description: How to Restore Deleted File in Linux
---

一个月前，我的洁癖犯了，想执行`find . -name "*~" -exec rm {} \;`清下某目录下由vim生成的~文件，不料漏打了`~`，把一些文件删掉了...好在有用`git`做版本控制，即使`.git/index`也被删没了，但也可以通过`git reset`恢复，之后再用`git`恢复版本管理中的其他被删文件即可。不料今天二月二号，我又犯二了，被做死历史`find . -name "*" -exec rm {} \;`坑了一把...这次被删的还有不少特意不放在版本控制的配置文件，这次不得不做文件恢复了。

最简单的情况是被删除的文件被某个进程打开，这个时候可以通过该进程在`/proc`下的文件描述符来恢复。首先由`lsof`找到打开文件的进程，有了`PID`和`FD`之后，就可以执行以下命令恢复文件：
```
cp /proc/<PID>/fd/<FD> <recovered-file>
```

不幸的是，我删的文件并没有被打开...所以不能用这种方式了。`df -T`查到被删文件所在的文件系统是ext4，于是可以试试ext的文件恢复方法。

ext3/ext4文件系统的恢复可以用`extundelete`，例如恢复被误删的目录可以用：
```
extundelete /dev/<device> --restore-directory <path>
```

恢复被误删的文件可以用：
```
extundelete --restore-file <path/to/deleted/file>
```

此外也可以用`debugfs`工具，相较`extundelete`，`debugfs`适用于ext2/ext3/ext4文件系统
```
debugfs -w /dev/<device>
```

在`debugfs`中用`lsdel`查找最近的删除操作，找到被删文件的inode：
```
debugfs: lsdel
```

接下来当然还是可以用`extundelete`：
```
extundelete --restore-inode <inode>
```

不过也可以用`debugfs`：
```
debugfs: dump <inode> <recovered-file>
```

不少资料还提到，可以先在`debugfs`中用：
```
debugfs: logdump -i <inode>
```
找到以下信息
```
Blocks: (<block id>): <block offset>
```
再通过`dd`命令恢复文件。

不过`extundelete`和`debugfs`可谓是段誉的六脉神剑，时灵时不灵的，我的问题竟也无法通过它们搞定，最后无奈只好动用[PhotoRec](http://www.cgsecurity.org/wiki/PhotoRec)“黑科技”了...PhotoRec恢复后的文件名好乱，好在我还有[ag](https://github.com/ggreer/the_silver_searcher)这种大杀器，找到被删的配置文件是分分钟的事XDD

哎，恢复文件真是麻烦，又想起了Zoom大妈的名言“冗余不做，日子甭过；备份不做，十恶不赦！”...

# 参考资料 #

[1][man proc](http://man7.org/linux/man-pages/man5/proc.5.html)

[2][Finding open files with lsof](http://www.ibm.com/developerworks/aix/library/au-lsof.html)

[3][Bring back deleted files with lsof](http://archive09.linux.com/feature/58142)

[4][How to recover deleted file if it is still opened by some process?](http://superuser.com/questions/283102/how-to-recover-deleted-file-if-it-is-still-opened-by-some-process)

[5]身为Arch党自然要安利一发Archwiki：[File recovery](https://wiki.archlinux.org/index.php/File_recovery)

[6][Recovering files from ext4 partition](http://www.tech-g.com/2014/01/27/recovering-files-from-ext4-partition/)

[7][man debugfs](http://linux.die.net/man/8/debugfs)

[8][Linux debugfs Hack: Undelete Files](http://www.cyberciti.biz/tips/linux-ext3-ext4-deleted-files-recovery-howto.html)

[9][Linux file deleted recovery](http://stackoverflow.com/questions/18197365/linux-file-deleted-recovery)

[10][undelete a just deleted file on ext4 with extundelete](http://unix.stackexchange.com/questions/122305/undelete-a-just-deleted-file-on-ext4-with-extundelete)

[11][Unix/Linux undelete/recover deleted files](http://unix.stackexchange.com/questions/80270/unix-linux-undelete-recover-deleted-files)

[12][debugfs总结](http://sundayhut.is-programmer.com/posts/50859.html)

[13][恢复Ext3下被删除的文件](http://coolshell.cn/articles/1265.html)

[14]这里有一些[脚本](http://www.cgsecurity.org/wiki/After_Using_PhotoRec)用来整理PhotoRec恢复的文件
