Title: 搭建Docker私有仓库折腾记
Date: 2016-08-02 02:13:00
description: Set Up a Private Docker Registry
Tags: cocos2d-x, Docker, CS, tech, Docker
Slug: 20160802-setup-private-docker-registry
Category: tech

最近折腾了一些Docker image，为了方便厂里其他人用，于是本渣还得折腾docker-registry搭个内网的Docker私有仓库~

本渣是照着[Docker —— 从入门到实践](https://yeasy.gitbooks.io/docker_practice/content/repository/local_repo.html)做的：

```
sudo apt-get install -y build-essential python-dev libevent-dev python-pip liblzma-dev
sudo pip install docker-registry
```

不过还需要再安装`swig`这个软件包才能正常安装`docker-registry`。

总算安装好了，但在push镜像时出现如下问题：

```
server gave HTTP response to HTTPS client
```

看了[Docker Github上这个issue](https://github.com/docker/distribution/issues/1874)和[SOF上这个问题](http://stackoverflow.com/questions/38695515/can-not-pull-push-images-after-update-docker-to-1-12)后才明白，是由于`Docker`服务默认是采用安全连接HTTPS的，对于我们来讲用HTTPS大可不必，可以照着以下步骤修改：

- 编辑`/etc/docker/daemon.json`:

```
{ "insecure-registries":["192.168.0.251:5000"] }
```

- 重启Docker服务：

```
sudo service docker restart
```

在拉取镜像的机器上也需要做这样的配置才能成功`docker pull`。
