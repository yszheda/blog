---
layout: post
title: "git-svn Tips"
date: 2014-07-25 11:22
comments: true
published: true
categories: [Linux, CS, tech]
keywords: git, svn
description: git-svn Tips
---

- 用`git` clone远端svn仓库（repo）：

```
$ git svn clone http://svn.example.com/project [-T trunk] [-b branches] [-t tags]
```

- 用`git-svn`从远端svn仓库拉取提交（commit）到本地：

```
$ git svn rebase
```

- 用`git-svn`把本地推送到远端svn仓库：

```
$ git svn dcommit
```

- 用`git-svn`checkout远端svn仓库的另一条svn支线（branch）到本地git支线：

假设我们要checkout的支线叫"another-branch"，首先在`.git/config`添加：

```
[svn-remote "another-branch"]
	url = http://svn.example.com/project/branches/another-branch
	fetch = :refs/remotes/another-branch
```

然后在命令行里执行：

```
$ git svn fetch another-branch
$ git checkout -b another-branch remotes/another-branch
```

- 使用`git-svn`来获取svn仓库的所有svn支线的改动：

```
$ git svn fetch --fetch-all
```

- 用`git-svn`某条svn支线复制提交到另一条svn支线：

我一开始想复杂了，写了下面的脚本，先在原来的支线上生成某一提交的patch，然后到另一支线打上该patch：

```
#!/bin/bash
if [ $1 == "-h" ]; then
    echo "Usage: "
    echo "$(basename $0) <git commit SHA1>"
    exit 0
fi

SHA1=$1

REPO_DIR=""
PATCH_DIR=""

SOURCE_BRANCH=master
DEST_BRANCH=dev

# cd ${REPO_DIR}
git stash
git checkout ${SOURCE_BRANCH}

patch_file=`git format-patch -1 ${SHA1} -o ${PATCH_DIR}`

git checkout ${DEST_BRANCH}
git svn rebase

# Apply patch for any svn repo:
# patch -p1 -i ${patch_file}
# In a git-svn repo, use `git am` instead:
git am ${patch_file}

# Check the commit manually
# tig

git svn dcommit

git checkout ${SOURCE_BRANCH}
git stash pop
```

后来发现`git-svn`checkout的svn支线其实和git支线没什么两样，用`git cherry-pick`就可以了。

- 将远端svn仓库的忽略文件列表加到git设置：

```
$ git svn show-ignore >> .git/info/exclude
```

# References #

[Adding a Branch to Git](https://blog.tfd.co.uk/2008/11/21/adding-a-branch-to-git/)

[Add an SVN remote to your Git repo](https://coderwall.com/p/vfop7g/add-an-svn-remote-to-your-git-repo)

[Add svn repo to existing git repo?](http://stackoverflow.com/questions/746151/add-svn-repo-to-existing-git-repo)

[Checkout remote branch using git svn](http://stackoverflow.com/questions/3239759/checkout-remote-branch-using-git-svn)

[Selective import of SVN branches into a git/git-svn repository](http://ivanz.com/2009/01/15/selective-import-of-svn-branches-into-a-gitgit-svn-repository/)