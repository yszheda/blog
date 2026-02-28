Title: Nginx Tips
Date: 2016-07-19 11:22:00
description: Nginx Tips
Tags: Linux, CS, tech, nginx
Slug: 20160719-nginx-tips
Category: tech

最近在做server端开发，需要熟悉nginx，本渣也就在这里记录下自己遇到的一些问题。其实都比较小白，纯粹当作自我扫盲啦XD 本文将不定期更新。

# nginx: [emerg] bind() to \<ip\>:\<port\> failed (98: Address already in use) #

```
nginx: [emerg] bind() to <ip>:<port> failed (98: Address already in use)
```

端口被占用，可以用查看使用文件或socket的命令`fuser`来杀掉占用端口的进程：

```
$ sudo fuser -k <port>/tcp
```

此外，如果使用IPv6还可能出现如下报错：

```
nginx: [emerg] bind() to [::]:<port> failed (98: Address already in use)
```

这是由于`nginx`配置中有`listen <port>;`，又有`listen [::]:<port>;`所致。
根据[nginx文档](http://nginx.org/en/docs/http/ngx_http_core_module.html#listen)的描述：

> By default, nginx will look up both IPv4 and IPv6 addresses while resolving. 

也就是说，`listen [::]:<port>;`会同时监听IPv4和IPv6的流量，所以`listen <port>;`是重复配置，将它删掉即可。
如果只想使用IPv6可以采用：

```
listen [::]:<port> ipv6only=on;
```

## 参考 ##

[(SOF) nginx - nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)](http://stackoverflow.com/questions/14972792/nginx-nginx-emerg-bind-to-80-failed-98-address-already-in-use)


# worker_connections are more than open file resource limit: 1024 #

这是因为nginx worker的用户打开的文件超过上限。

如果nginx配置中有`worker_rlimit_nofile`参数，则打开的文件数量上限由`worker_rlimit_nofile`决定（nofile=number of open files）。
那么`worker_rlimit_nofile`应该配多少呢？

在nginx配置的core module中找到`worker_processes`数量：

```
worker_processes  4;
```

在event module中找到`worker_connections`数量：

```
events {
    worker_connections  1024;
}
```

那么最大总连接数是`worker_connections * worker_processes`，每个active connection都会占用一个文件描述符（file descriptor），所以`worker_rlimit_nofile`最好大于`worker_connections * worker_processes`。

## 参考 ##

[nginx worker_rlimit_nofile文档](http://nginx.org/en/docs/ngx_core_module.html#worker_rlimit_nofile)

[(SOF) understanding max file descriptors for linux and nginx, and best value for worker_rlimit_nofile](http://serverfault.com/questions/208916/understanding-max-file-descriptors-for-linux-and-nginx-and-best-value-for-worke)

[(SOF) How can I observe what nginx is doing? (to solve: “1024 worker_connections are not enough”)](http://serverfault.com/questions/209014/how-can-i-observe-what-nginx-is-doing-to-solve-1024-worker-connections-are-n)

如果nginx配置中没有`worker_rlimit_nofile`参数，则采用系统默认的打开的文件数量上限。那么如何查看并修改这一上限呢？

首先在nginx配置的core module中找到nginx worker进程的用户：

```
user nginx;
```

在终端登入这一用户：

```
$ sudo su - nginx
```

查看文件描述符的硬上限：

```
$ ulimit -Hn
```

查看文件描述符的软上限：

```
$ ulimit -Sn
```

这里硬上限是严格不能超过的上限，不能增加。软上限属于警告性质的上限，可以调高，但也不能超过硬上限。

在`/etc/sysctl.conf`中修改下述数值：

```
fs.file-max = 65536
```

使用以下命令加载新的配置：

```
$ sysctl -p
```

检查是否已更新：

```
$ cat /proc/sys/fs/file-max
```

一些资料提到修改`/etc/security/limits.conf`中nofile的软上限和硬上限：

```
* soft     nofile         65535
* hard     nofile         65535
root soft     nofile         65535
root hard     nofile         65535
```

这种方式至少需要nginx worker进程重启才能生效。

## 参考 ##

[ulimit manual](http://ss64.com/bash/ulimit.html)

[通过 ulimit 改善系统性能](http://www.ibm.com/developerworks/cn/linux/l-cn-ulimit/index.html)

[What does “soft/hard nofile” mean on Linux](http://stackoverflow.com/questions/3107476/what-does-soft-hard-nofile-mean-on-linux)

[ulimit: difference between hard and soft limits](http://unix.stackexchange.com/questions/29577/ulimit-difference-between-hard-and-soft-limits)

[limits.conf manual](http://ss64.com/bash/limits.conf.html)

[Making changes to /proc filesystem permanently](http://www.cyberciti.biz/faq/making-changes-to-proc-filesystem-permanently/)

[nginx uLimit 'worker_connections exceed open file resource limit: 1024'](http://serverfault.com/questions/640976/nginx-ulimit-worker-connections-exceed-open-file-resource-limit-1024)

[do changes in /etc/security/limits.conf require a reboot?](http://unix.stackexchange.com/questions/108603/do-changes-in-etc-security-limits-conf-require-a-reboot)

[How to configure linux file descriptor limit with fs.file-max and ulimit](http://serverfault.com/questions/165316/how-to-configure-linux-file-descriptor-limit-with-fs-file-max-and-ulimit)

[How to increase maximum file open limit (ulimit) in Ubuntu?](http://stackoverflow.com/questions/21515463/how-to-increase-maximum-file-open-limit-ulimit-in-ubuntu)

[Nginx: 24: Too Many Open Files Error And Solution](http://www.cyberciti.biz/faq/linux-unix-nginx-too-many-open-files/)

# an upstream response is buffered to a temporary file #



# proxy_temp failed (13: Permission denied) while reading upstream #