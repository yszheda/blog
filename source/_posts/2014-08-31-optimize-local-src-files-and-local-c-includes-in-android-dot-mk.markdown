---
layout: post
title: "如何自动设好Android.mk的LOCAL_SRC_FILES和LOCAL_C_INCLUDES"
date: 2014-08-31 15:30
comments: true
published: true
categories: [cocos2d-x]
keywords: cocos2d-x, cocos, cocos2d, Android, Android.mk, makefile, Makefile, shell, LOCAL_SRC_FILES, LOCAL_C_INCLUDES, 游戏开发, 手游开发, mobile game, game devolopment
description: discussion about LOCAL_SRC_FILES and LOCAL_C_INCLUDES in Android.mk
---
用cocos2d-x开发Android游戏时，需要在Android.mk文件中，为LOCAL_SRC_FILES变量指定要编译的源代码，以及为LOCAL_C_INCLUDES变量指定头文件。当项目文件越来越多时，这种手动修改很浪费时间。好在Android.mk其实就是一个makefile，我们可以借助makefile语法来自动完成这部分工作。

<!-- more -->

# 使用外部命令 #
最简单的方式就是调用shell外部命令。首先我们指定要搜索的源文件根目录，设为SRC_ROOT这个变量。LOCAL_C_INCLUDES变量直接就是用`find <path> -type d`命令去搜索根目录下的目录。LOCAL_SRC_FILES稍微复杂一些，首先我们先用`find <path> -type f`得到所有的普通文件路径，再指定源代码文件名的匹配模式（例如我用的是c++，所以我指定了变量SRC_SUFFIX存放一般c++源代码文件的后缀名），用filter命令筛选出所有的源代码文件路径。

完整的代码如下：
```
# WARNING: Shell command is used, it is only works on a UNIX-like OS.
# Replace it with Makefile rules if you want to run on Windows.
SRC_SUFFIX := *.cpp *.c 
SRC_ROOT := $(LOCAL_PATH)/../../Classes
ALL_FILES := $(shell find $(SRC_ROOT) -type f)
SRC_FILES := $(filter $(subst *,%,$(SRC_SUFFIX)),$(ALL_FILES))
LOCAL_SRC_FILES := hellocpp/main.cpp
LOCAL_SRC_FILES += $(SRC_FILES:$(LOCAL_PATH)/%=%)

SRC_DIRS := $(shell find $(SRC_ROOT) -type d)
LOCAL_C_INCLUDES := $(SRC_DIRS)
```

# 使用纯Makefile语法 #
使用外部命令是最简单实用的解决方案，但正如上面的代码注释所提及的，这种方式只能在Unix系统上才能用，对于需要跨平台适用的情况，还是需要采用纯Makefile语法才行。

我们知道，Makefile的[wildcard](http://gnu.april.org/software/make/manual/make.html#Wildcard-Function)命令可以部分实现类似`find`的功能，例如找到当前目录下的.c文件可以用`$(wildcard *.c)`，可惜`wildcard`毕竟不够强大，该命令的结果并不包含子目录以下的.c文件。想要实现这一功能，我们可以借用StackOverflow上大神用纯Makefile语法写的递归`wildcard`：

```
# recursive wildcard
rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d)))
```

该`rwildcard`命令传入两个参数，第一个参数`$1`是目录，第二个参数`$2`是匹配模式。该命令首先用`$(wildcard $1*)`得到目录下的所有文件和一级子目录，再遍历一遍：对于当前`$d`变量是目录的情况，对`$d/`目录递归调用`rwildcard`；对于`$d`是普通文件的情况，递归调用会因为`$(wildcard $d/*)`找不到匹配而终止，接下来便调用`filter`函数对`$2`的模式进行筛选。

完整的代码如下：
```
SRC_SUFFIX := *.cpp *.c 
SRC_ROOT := $(LOCAL_PATH)/../../Classes
# recursive wildcard
rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d)))
SRC_FILES := $(call rwildcard,$(SRC_ROOT)/,$(SRC_SUFFIX))
LOCAL_SRC_FILES := hellocpp/main.cpp
LOCAL_SRC_FILES += $(SRC_FILES:$(LOCAL_PATH)/%=%)
```

# 筛除不需要编译的源代码文件 #
上面介绍的方法有一个适用的前提，那就是`$SRC_ROOT`下每个源代码文件都需要被编译。而有时候这个条件并不成立，像本渣所在项目中就用到了一些外部库，这些库的源代码是不用被编译的（例如设为ASIO_HEADER_ONLY的Asio库）。这个时候就需要把这部分源代码排除在LOCAL_SRC_FILES之外。

## 第一种方法：filter-out ##
第一种方法是用Makefile的[filter-out](http://gnu.april.org/software/make/manual/make.html#index-filter_002dout)：

```
# ASIO library is set as ASIO_HEADER_ONLY, so it will be excluded from source code
EXCLUDE_SRC_FILES := $(SRC_ROOT)/3rdParty/Asio/asio/impl/%.cpp
EXCLUDE := $(filter $(EXCLUDE_SRC_FILES),$(SRC_FILES))
SRC_FILES := $(filter-out $(EXCLUDE_SRC_FILES),$(SRC_FILES))
```

这种方式虽然可行，但是`filter-out`无法用于多级目录的模式匹配，所以这种方法暴露了太多关于外部库源代码路径的细节。有没有可能指定要排除的库名或关键字，再根据这个信息去筛除匹配的源代码文件呢？

## 第二种方法：改进rwildcard ##
第二种方式是在rwildcard中加入一个判断用于筛除：如果当前的目录/文件名匹配到所要筛除的关键字，则什么都不做；否则就继续递归调用和执行`filter`命令。

```
# ASIO library is set as ASIO_HEADER_ONLY, so it will be excluded
EXCLUDE_LIB := Asio
# recursive wildcard
rwildcard = $(foreach d,$(wildcard $1*),$(if $(findstring $(EXCLUDE_LIB),$d),,$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d)))
SRC_FILES := $(call rwildcard,$(SRC_ROOT)/,$(SRC_SUFFIX))
```

这种方式是好一些了，而且直接在递归`wildcard`搜索时就进行了排除，不过`rwildcard`变得更复杂了，可读性不佳。

## 第三种方法：FILTER_OUT_PATTERN ##

最后的方法也来自于StackOverflow大神用纯Makefile语法改造过的`filter-out`，不过本质上和第二种方法的实现是类似的，这里就不详细解释了：

```
# ASIO library is set as ASIO_HEADER_ONLY, so it will be excluded from source code
EXCLUDE_SRC_PATTERN := asio
FILTER_OUT_PATTERN = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
SRC_FILES := $(call FILTER_OUT_PATTERN,$(EXCLUDE_SRC_PATTERN),$(SRC_FILES))
```

## 进一步拓展 ##

假如需要剔除的库有很多，我们当然希望能在`FILTER_OUT_PATTERN`中加入所有要剔除的库的关键字。一种方式是拓展上述第二种方法，加个`foreach`，但个人不太喜欢；另一种方式是拓展第三种方法：

```
# The key names of excluded lib here are just used for illustration.
EXCLUDE_SRC_PATTERN := asio asio1 asio2 asio3
FILTER_OUT_PATTERN = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
define FILTER_FUN
SRC_FILES := $(call FILTER_OUT_PATTERN,$(1),$(SRC_FILES))
endef
$(foreach p,$(EXCLUDE_SRC_PATTERN),$(eval $(call FILTER_FUN)))
```

这里不外乎是用`eval`做宏展开，具体请参见[The eval Function](http://gnu.april.org/software/make/manual/make.html#Eval-Function)。
