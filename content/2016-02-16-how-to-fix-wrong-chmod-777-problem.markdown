Title: 小记Linux/UNIX下错误权限恢复
Date: 2016-02-16 23:48:00
description: How to Fix Wrong chmod+777 Problem
Tags: Linux, CS, tech, chmod, sudo, pkexec, acl, linux, Linux, UNIX, 777, 恢复
Slug: 20160216-how-to-fix-wrong-chmod-777-problem
Category: tech

继我[不久前犯二](http://galoisplusplus.coding.me/blog/2016/02/02/how-to-restore-deleted-file-in-linux/)之后，今天一位同事小伙伴也逗逼了，给`/etc/sudoers`加了777权限...6666结果`sudo`就悲剧了：
```
sudo: /etc/sudoers is mode 0777, should be 0440
sudo: no valid sudoers sources found, quitting 
```

我一开始还想用`pkexec`恢复：
```
pkexec chmod 0440 /etc/sudoers
```
不料机器上木有装`PolicyKit`...

后来小伙伴找SA要root密码搞定了。不过这倒勾起了我的好奇心：这种悲剧除了`pkexec`、除了拿到root权限（包括重启系统进恢复模式）执行复原操作，难道只能GG了么？后来查到了[《sudo chmod 777 / 惨剧修复简单步骤》](https://gist.github.com/syxc/2822948)这篇文章，发现获取和设置UNIX文件Access Control List (ACL)的命令`getacl`/`setacl`还能有这种妙用，这便是我想找的另一套解决方案了。

不过，以后还是装上`PolicyKit`，以防不测吧...

# 参考资料 #

[http://superuser.com/questions/300743/sudo-chmod-r-777](http://superuser.com/questions/300743/sudo-chmod-r-777)

[Wrongly set chmod / 777. Problems?](http://unix.stackexchange.com/questions/12998/wrongly-set-chmod-777-problems)

[sudo error, is mode 0777, should be 0440](http://askubuntu.com/questions/50704/sudo-error-is-mode-0777-should-be-0440)

[Getting message “sudo: must be setuid root”, but sudo IS already owned by root](http://stackoverflow.com/questions/16682297/getting-message-sudo-must-be-setuid-root-but-sudo-is-already-owned-by-root)
