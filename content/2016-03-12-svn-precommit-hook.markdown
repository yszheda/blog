Title: svn pre-commit hook两三事
Date: 2016-03-12 10:26:00
description: svn pre-commit hook
Tags: Linux, CS, tech, svn, hook, lua, commit, luac, lua
Slug: 20160312-svn-precommit-hook
Category: tech

说起折腾svn hook这件事还是在去年年底。我厂向来木有Code Review等Quality Assurance流程，全赖老司机们各种强力输出。而当时我们项目的不少老司机要么去了其他部门要么离职了，新来的小鲜肉码农们似乎对Version Control一无所知。别的不说，单是commit不写comment，便让大家头疼不已，每次在merge时都得额外花不少时间来搞清楚commit的具体内容。虽然我自从投奔`git`阵营后基本都是用`git svn`，对`svn`生疏已久，但觉得加个`svn`提交限制应非难事，所以便额外花了点时间写了个pre-commit hook，对commit的comment中的非空白字符做计数，少于一定字数的不让提交。万万没想到，当时让SA大大部署上`svn`服务器后，就有人commit了一个“再试一下”orz...当时我的内心是崩溃的...在推上围脖上吐槽后不久，众位大神各种支招，例如巨硬的泉哥说再搞个语义分析器666...不过最受用的还是根爷所提到的用`cpplint`检查代码是否符合编码规范、是否能够编译通过。恰好那段时间小鲜肉们提交了一些带有语法错误的lua代码，偶们又木有review制度，结果不写程序的策划大大们`svn up`下来后——「什么鬼？肿么不能运行了？！好拙计啊！AAA，快来看bug啊！BBB，SOS！」——导致别人不得不停下手头的活、额外花时间排查。所以我便在pre-commit hook里用`luac`检查语法错误的代码，把这种坑队友的事扼杀在摇篮里。虽然不及`cpplint`那么强大，但也基本够用了。最近一次改这个脚本是因为前段时间有个小鲜肉做了一张4096x4096的图集，而cocos2d-x文档里写得清清楚楚，大多数手机所支持的最大纹理尺寸其实只有2048x2048...卧槽，干得漂亮啊，一上线就造成了不少crash...木有review制度好可啪，在发现这个问题之前其他人一直毫不知情...所以我还是干脆在svn hook里再加个限制吧～

好了，不碎碎念了，这便是我折腾的svn hook，主要做了这么几项功能：

- commit message非空白长度检查

- lua语法检查

- 禁止添加文件名带空格的文件

- 禁止被配在`PROHIBITED_FILES`的文件被修改

- 确保图片尺寸小于2048x2048

```
#!/bin/sh

# PRE-COMMIT HOOK
#
# The pre-commit hook is invoked before a Subversion txn is
# committed.  Subversion runs this hook by invoking a program
# (script, executable, binary, etc.) named 'pre-commit' (for which
# this file is a template), with the following ordered arguments:
#
#   [1] REPOS-PATH   (the path to this repository)
#   [2] TXN-NAME     (the name of the txn about to be committed)
#
#   [STDIN] LOCK-TOKENS ** the lock tokens are passed via STDIN.
#
#   If STDIN contains the line "LOCK-TOKENS:\n" (the "\n" denotes a
#   single newline), the lines following it are the lock tokens for
#   this commit.  The end of the list is marked by a line containing
#   only a newline character.
#
#   Each lock token line consists of a URI-escaped path, followed
#   by the separator character '|', followed by the lock token string,
#   followed by a newline.
#
# The default working directory for the invocation is undefined, so
# the program should set one explicitly if it cares.
#
# If the hook program exits with success, the txn is committed; but
# if it exits with failure (non-zero), the txn is aborted, no commit
# takes place, and STDERR is returned to the client.   The hook
# program can use the 'svnlook' utility to help it examine the txn.
#
# On a Unix system, the normal procedure is to have 'pre-commit'
# invoke other programs to do the real work, though it may do the
# work itself too.
#
#   ***  NOTE: THE HOOK PROGRAM MUST NOT MODIFY THE TXN, EXCEPT  ***
#   ***  FOR REVISION PROPERTIES (like svn:log or svn:author).   ***
#
#   This is why we recommend using the read-only 'svnlook' utility.
#   In the future, Subversion may enforce the rule that pre-commit
#   hooks should not modify the versioned data in txns, or else come
#   up with a mechanism to make it safe to do so (by informing the
#   committing client of the changes).  However, right now neither
#   mechanism is implemented, so hook writers just have to be careful.
#
# Note that 'pre-commit' must be executable by the user(s) who will
# invoke it (typically the user httpd runs as), and that user must
# have filesystem-level permission to access the repository.
#
# On a Windows system, you should name the hook program
# 'pre-commit.bat' or 'pre-commit.exe',
# but the basic idea is the same.
#
# The hook program typically does not inherit the environment of
# its parent process.  For example, a common problem is for the
# PATH environment variable to not be set to its usual value, so
# that subprograms fail to launch unless invoked via absolute path.
# If you're having unexpected problems with a hook program, the
# culprit may be unusual (or missing) environment variables.
# 
# Here is an example hook script, for a Unix /bin/sh interpreter.
# For more examples and pre-written hooks, see those in
# the Subversion repository at
# http://svn.apache.org/repos/asf/subversion/trunk/tools/hook-scripts/ and
# http://svn.apache.org/repos/asf/subversion/trunk/contrib/hook-scripts/

LOG="/tmp/svn.log"
touch ${LOG}

REPOS="$1"
TXN="$2"
echo "REPOS: $REPOS" > ${LOG}
echo "TXN: $TXN" >> ${LOG}

SVNLOOK=""

# lua compiler
LUAC=""
# lua file extension
LUA_EXT="lua"
# png file extension
PNG_EXT="png"

MSG_MIN_CHAR_NUM=3

MAX_PNG_SIZE=2048

PROHIBITED_FILES=(
)

TMP_DIR="/tmp/svn"
if [[ -d ${TMP_DIR} ]]; then
    rm -r ${TMP_DIR}
fi
mkdir -p ${TMP_DIR}

function check_lua_syntax {
local lua_file=$1
echo `${LUAC} ${lua_file} 2>&1`
}

function create_file {
local file_name=$1
# Create tmp file and copy content
tmp_file="${TMP_DIR}/${file_name}"
mkdir -p "$(dirname "${tmp_file}")" && touch "${tmp_file}"
${SVNLOOK} cat -t "${TXN}" "${REPOS}" "${file_name}" > ${tmp_file}
}

# Make sure that the log message contains some text.
commit_msg=`$SVNLOOK log -t "$TXN" "$REPOS" | sed 's/[[:space:]]//g'`
echo ${commit_msg} >> ${LOG}
if [[ `echo ${commit_msg} | wc -c` -lt ${MSG_MIN_CHAR_NUM} ]]; then
    echo "Please write a meaningful comment when committing" 1>&2
    exit 1
fi

changed_info_str=`${SVNLOOK} changed -t "${TXN}" "${REPOS}"`
IFS=$'\n' read -rd '' -a changed_infos <<<"${changed_info_str}"

lua_error_msg=""
png_error_msg=""
for changed_info in "${changed_infos[@]}"; do
    # Prevent commiting file that contains space in its filename
    echo ${changed_info} >> ${LOG}
    operation=`echo ${changed_info} | awk '{print $1}'`
    if [[ ${operation} = "A" ]] && [[ `echo ${changed_info} | awk '{print NF}'` -gt 2 ]]; then
        echo "Please do not commit file that contains space in its filename!" 1>&2
        exit 1
    fi
    file_name=`echo ${changed_info} | awk '{print $2}'`
    echo "operation: ${operation}, file: ${file_name}, ext: ${ext}" >> ${LOG}

    # Check prohibit-commit files
    for prohibited_file in ${PROHIBITED_FILES[@]}; do
        if [[ ${file_name} = ${prohibited_file} ]]; then
            echo "${file_name} is not allowed to be changed!" 1>&2
            exit 1
        fi
    done

    ext=`echo ${file_name} | awk -F"." '{print $NF}'`

    if [[ ${operation} = "U" ]] || [[ ${operation} = "A" ]]; then
        tmp_file="${TMP_DIR}/${file_name}"

        # Check lua syntax
        if [[ ${ext} = ${LUA_EXT} ]]; then
            echo "Check syntax of ${tmp_file}" >> ${LOG}
            create_file ${file_name}
            error_msg=`check_lua_syntax ${tmp_file}`
            if [[ `echo ${error_msg} | sed 's/\n//g'` != "" ]]; then
                lua_error_msg="${lua_error_msg}\n${error_msg}"
            fi
        fi

        # Check file size
        if [[ ${ext} = ${PNG_EXT} ]]; then
            create_file ${file_name}
            png_info=`file ${tmp_file} | sed 's/,//g'`
            png_width=`echo ${png_info} | awk '{print $5}' | bc`
            png_height=`echo ${png_info} | awk '{print $7}' | bc`
            if [[ ${png_width} -gt ${MAX_PNG_SIZE} ]] || [[ ${png_height} -gt ${MAX_PNG_SIZE} ]]; then
                png_error_msg="${png_error_msg}\n${file_name} is too large: ${png_width} x ${png_height}"
            fi
        fi
    fi
done

rm -r ${TMP_DIR}

if [[ ${lua_error_msg} != "" ]] || [[ ${png_error_msg} != "" ]]; then
    if [[ ${lua_error_msg} != "" ]]; then
        echo "lua error: ${lua_error_msg}" >> ${LOG}
        echo "Please fix the error in your lua program:${lua_error_msg}" 1>&2
    fi

    if [[ ${png_error_msg} != "" ]]; then
        echo "png error: ${png_error_msg}" >> ${LOG}
        echo "Please do not commit pictures which are larger than 2048 x 2048:${png_error_msg}" 1>&2
    fi

    exit 1
fi

# Check that the author of this commit has the rights to perform
# the commit on the files and directories being modified.
# commit-access-control.pl "$REPOS" "$TXN" commit-access-control.cfg || exit 1

# All checks passed, so allow the commit.
exit 0
```

PS. 聪哥说作为一位开发去搞svn hook怕被公司的其他开发喷越权管了运维的事，我厂倒是不存在这种问题的——人少活多时间紧，啥活都得揽啊，例如我一位舍友兼同事的大神以前开发手游可是客户端、服务器、策划、切图全都一人搞定，就差自己出美术图和特效了。最近我也在像运维一样写脚本自动化处理某些项目文件，发现我们开发各种混乱啊有木有！例如路径带空格，我的一些`awk`脚本就雪崩了——我在以上的`hook`脚本里也有同样的问题，其实把列计数方式改一下，例如`$7`改成`${NF-4}`，可以避免这种问题——而且还要把带空格的路径用`sed`替换成转义后的字符串。不过这种情况还算好的，还有些人用的单词有拼写错误，要是全错了倒也罢了，脚本hold得住，问题是有的对有的错...偶只能弃疗了...

# 后记 #

由于我们lua代码中存在不少没声明`local`而变成全局变量的bug，于是我把Openresty作者春哥的`lua-releng`工具也加进`hook`里做全局变量检查了。具体可以看[这个gist](https://gist.github.com/yszheda/6125a32e37834cc8ab75)。

