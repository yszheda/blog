Title: LaTeX Tips
Date: 2013-04-13 17:21:00
description: Tips for using LaTeX
Tags: tech, CS, LaTeX, LaTeX, latex, tex, BibTeX, mendeley, chapterbib, listings, minted, xypic, Graphviz, media9, bibtex2html, HEVEA, ocaml
Slug: 20130413-latex-tips
Category: tech
早先我用MS office或open source的[OOo](http://www.openoffice.org/)来编辑文档，后来渐渐转向google docs和LibreOffice，学会了$\LaTeX$后，由于$\LaTeX$所见即所得（WYSIWYG）的特征节省了我不少排版的时间，所以如今成为我撰写文档、幻灯片（beamer）的主要工具。以下主要是我折腾$\LaTeX$的点点滴滴，有些也许很少能被用到（例如插入u3d来显示3D物体），大部分与也主要是一些不错的辅助工具和如何解决我遇到的一些问题，如果你只是初学者、想系统地学习$\LaTeX$，那么我建议你看一下大名鼎鼎的[A (Not So) Short In­tro­duc­tion to $\LaTeX$](http://www.ctan.org/tex-archive/info/lshort/)；如果你看完这篇文章觉得有些工具不错、想继续深入了解，我想最科学的方式还是阅读官方文档、订阅官方的user maillist，当然也欢迎与我交流啦XD

<!-- more -->

## 关于参考文献 ##
我推荐使用BibTeX，尽管要编译四次，但维护一个文献数据库却常常能重用bib，省得下次要引用同样的文献时要加入重复的bibitem。目前我主要由[mendeley desktop](http://www.mendeley.com/)管理文献，也由它来产生.bib文件。

有时候我需要分章节来显示参考文献，这时候要用到[chapterbib](http://www.ctan.org/pkg/chapterbib)。加入：
```tex

\usepackage{sectionbib}{chapterbib} 

```
在对应的章节末尾加入平常在文章末尾加入的这两行代码即可（<bib-file>为.bib文件的名称）：
```tex

\bibliographystyle{plain}  
\bibliography{<bib-file>}

```
如果正文中没有出现引用而想把.bib文件的所有文献放到参考文献中，则需要在以上命令前加上：
```tex

\nocite{*}

```

## 关于代码高亮（source code highlight）##
我常常有需要在一些文档或幻灯片中加入代码，这时我希望代码在$\LaTeX$生成的目标文件中高亮而且我不需要修改要插入的代码（例如为关键字配置颜色）。

过去我用的是[listings](http://www.ctan.org/tex-archive/macros/latex/contrib/listings/)，不过default的listings显示出来并不如人意——尤其是在beamer产生的slides里，不进行一些配置会占空间而且很难看。

以下我用以前所用的一些显示shell代码的配置作为一个简单的示例：
```tex
% shell code highlight support  
% adapted from http://www.programmiersprachen.de/forum/board26-our-developer-boards/developer-lounge/7976-latex-shell-code-lstlisting/?s=03579afecc34ba7129d5a0145a93efeaabcfe45f  
\lstdefinestyle{Shell}{delim=[il][\bfseries]{BB}}  
\newcommand{\shellcmd}[1]{\\\indent\indent\texttt{\footnotesize\# #1}\\}  
\usepackage{xcolor}  
\usepackage{listings}  
\lstdefinestyle{BashInputStyle}{  
language=bash,  
basicstyle=\small\sffamily,  
numbers=left,  
numberstyle=\tiny,  
numbersep=3pt,  
frame=tb,  
columns=fullflexible,  
backgroundcolor=\color{yellow!20},  
linewidth=1.0\linewidth,  
xleftmargin=0.1\linewidth  
}  
```
效果如下：

![image](/images/listings.png)


后来我在Stack Overflow上看到了这个问答:
<http://stackoverflow.com/questions/1966425/source-code-highlighting-in-latex>
于是试用了下minted，感觉非常符合我的需要：支持的语法、显示的样式都很多。minted项目的主页是<http://code.google.com/p/minted/>，由于它用[pygments](http://pygments.org/)来做代码高亮，所以需要安装Python和pygments。

以下是我用minted显示的CUDA代码片段：

![image](/images/minted.png)

以上效果只需要在$\LaTeX$代码中将要显示的代码放在以下两行中间即可，非常方便：
```tex
\begin{minted}[frame=lines,linenos,mathescape]{c}  
\end{minted} 
```
另外需要注意的是：如果你用XeLaTeX的话，minted中代码的Tab会显示为^^I，当然你可以在编辑器中很容易将Tab替换掉（例如在vim中把Tab换为两个空格）：
```tex
:%s/^^I/  /g  
```
不过更好的方法是传入-8bit参数到xelatex指令里，编译tex源文件（\<tex-file\>）的完整命令是：
```tex
xelatex -shell-escape -8bit <tex-file>  
```
可参见stackexchange上的这个链接：
<http://tex.stackexchange.com/questions/36841/using-minted-and-tabs>

与listings相比，minted的一大缺点是无法自动换行和word warp，当然比较优雅的代码一般都不会把一行写得又臭又长，但毕竟写代码的屏幕和文档的宽度不同，还是会有一些行比较长、显示效果不佳的情况，这时候用minted的话需要自行调整。

PS.我的blog也是用Pygments来做代码高亮的。

## 关于画图 ##
我一直觉得直接用$\LaTeX$画图是一大硬伤，个人觉得画图远不像一般的文本WYSIWYG——只需要管好编辑，$\LaTeX$做好排版——而是经常需要编译出来看效果再回头调位置参数，麻烦得紧。

这方面，我早先试过用[xypic](http://xy-pic.sourceforge.net/)，xypic的\xymatrix已经基本能对付一般的关系图了，但我更看中的是它支持object。我也曾经用这一特性来画过一个parser输入输出的简单示意图：

![image](/images/xypic.png)

生成这张图的tex源代码如下：
```tex
\documentclass{article}
\usepackage[dvipdfm]{geometry}
\usepackage[dvips,arrow,curve]{xy}
\paperwidth 18 true cm
\paperheight 14 true cm
%----------------------------页边空白调整-------------------------------
\def\marginset#1#2{                      % 页边设置 \marginset{left}{top}
\setlength{\oddsidemargin}{#1}         % 左边（书内侧）装订预留空白距离
\iffalse                   % 如果考虑左侧（书内侧）的边注区则改为\iftrue
\reversemarginpar
\addtolength{\oddsidemargin}{\marginparsep}
\addtolength{\oddsidemargin}{\marginparwidth}
\fi

\setlength{\evensidemargin}{0mm}       % 置0
\iffalse                   % 如果考虑右侧（书外侧）的边注区则改为\iftrue
\addtolength{\evensidemargin}{\marginparsep}
\addtolength{\evensidemargin}{\marginparwidth}
\fi

% \paperwidth = h + \oddsidemargin+\textwidth+\evensidemargin + h
\setlength{\hoffset}{\paperwidth}
\addtolength{\hoffset}{-\oddsidemargin}
\addtolength{\hoffset}{-\textwidth}
\addtolength{\hoffset}{-\evensidemargin}
\setlength{\hoffset}{0.5\hoffset}
\addtolength{\hoffset}{-1in}           % h = \hoffset + 1in

\setlength{\voffset}{-1in}             % 0 = \voffset + 1in
\setlength{\topmargin}{\paperheight}
\addtolength{\topmargin}{-\headheight}
\addtolength{\topmargin}{-\headsep}
\addtolength{\topmargin}{-\textheight}
\addtolength{\topmargin}{-\footskip}
\addtolength{\topmargin}{#2}           % 上边预留装订空白距离
\setlength{\topmargin}{0.5\topmargin}
}
% 调整页边空白使内容居中，两参数分别为纸的左边和上边预留装订空白距离
\marginset{-55mm}{65mm}
\begin{document}
\[
\begin{xy}
  (0,-5)*+{\mbox{CREATE TABLE}}="v1";
  (0,-15)*+{\mbox{SQL assertion}}="v2";
  (0,-23)*+{\mbox{DELETE/UPDATE (multi-table)}}="v3";
  (0,-30)*+{\mbox{INSERT}}="v4";
  (0,-40)*+{\mbox{DELETE/UPDATE (single table)}}="v5";
  (50,0)*+{\mbox{module ...}}="v6";
  (52,-5)*+{\mbox{use import ...}}="v7";
  (65,-10)*+{\mbox{type tupleType\_...=\{$|~~$...$~~|$\} }}="v8";
  (67,-15)*+{\mbox{predicate $<$name$>$ $<$param$>$ =}}="v9";
  (45,-20)*+{\mbox{...}}="v10";
  (62,-25)*+{\mbox{let $<$name$>$ $<$param$>$ =}}="v11";
  (56,-30)*+{\mbox{\{$<$precondition$>$\}}}="v12";
  (45,-35)*+{\mbox{...}}="v13";
  (57,-40)*+{\mbox{\{$<$postcondition$>$\}}}="v14";
  (45,-45)*+{\mbox{end}}="v15";
  {\ar@{->} "v1";"v7"};
  {\ar@{->} "v1";"v8"};
  {\ar@{->} "v2";"v9"};
  {\ar@{->} "v3";"v10"};
  {\ar@{->} "v3";"v13"};
  {\ar@{->} "v3";"v14"};
  {\ar@{->} "v4";"v13"};
  {\ar@{->} "v5";"v13"};
  {\ar@{.} "v9";(97,-15)};
  {\ar@{.} (97,-15);(97,-30)};
  {\ar@{.>} (97,-30);"v12"};
  {\ar@{.} (97,-30);(97,-40)};
  {\ar@{.>} (97,-40);"v14"};
\end{xy}
\]
\end{document}
```
不难看出，用xypic来做object关系的设定非常简单，我大部分的编辑时间其实是耗在确定座标和页面设置的参数上。


另一种在$\LaTeX$中画图的方式也许要算MetaPost（类似于$\LaTeX$源于Knuth大牛的TeX，MetaPost衍生于Knuth的MetaFont）了，不过我没用过，据说比较偏底层（从wiki上的例子来看确实如此）。我在法国某实验室实习的时候倒是有幸接触到了一个相关的工具[mlpost](http://mlpost.lri.fr/)（OT一下，其中一名开发者恰好是与我同一组的researcher）——mlpost其实是对MetaPost的一层ocaml接口，也可以定义抽象层面的object，再对object进行操作。不过我最近有需要画图时，在archlinux上装了最新的mlpost后却跑出不少问题，怀疑是一些ocaml包的依赖没解决好的问题，有空再解决吧~


接下来推荐一下[Graphviz](http://graphviz.org/)的DOT语言。DOT对high level的画图支持得很好，而且极好上手，我大概花了不到半小时看了一下官网的tutorial和一些sample就可以着手用DOT画我想要的图。

例如下面这张图：

![image](/images/graphviz.png)

用DOT只需这么寥寥几行代码：
```dot
digraph GPUencode
{
rankdir=LR;
compound=true;
subgraph clusterCPU
{
node [style=filled];
shape=box;
label="CPU";
"hostMem"
[
shape=box
label="host memory"
]
}
subgraph clusterGPU
{
node [style=filled];
shape=box;
label="GPU\n\n2.generate encoding matrix\n3.encode";
"deviceMem"
[
shape=box
label="device memory"
]
}
hostMem -> deviceMem [label="1.copy k data chunks"];
deviceMem -> hostMem [label="4.copy encoding matrix as metadata"];
deviceMem -> hostMem [label="5.copy (n-k) code chunks"];
"n,k" -> deviceMem [lhead=clusterGPU];
}
```

DOT支持多种格式，我用的比较多的是ps，用下面的命令编译即可：
```bash
dot -Tps <dot-file> -o <ps-file>  
```


PS.最近试了一个在$\LaTeX$文档中画甘特（gantt）图的package：
<http://www.martin-kumm.de/tex_gantt_package.php>

还挺方便的XD


## 关于显示3D物体/图表 ##
这个问题我折腾了许久，其实折腾的起因原本也不是很重要——某个实验结果我已经用octave产生了一张3D的图，这张图完全可以说明我想阐述的结论，不过要旋转这张3D图到不同视角才可以看得很清楚，可是我懒得去产生几张2D图——想来我可以当作迁就「负心智动量（negative mental momentum）」（参见Ron Hale-Evans的《Mind Performance Hacks: Tips & Tools for Overclocking Your Brain 》）的典型了，好在结果还算蛮cool的。XD

我最早是在一份slides<http://www.math.canterbury.ac.nz/~s.zhu/other_files/wen_beamer2.pdf>中偶然发现[movie15](http://www.ctan.org/pkg/movie15)可以插入Matlab的u3d文件，生成的pdf在Adobe Reader中可以显示u3d的3d图。但现在movie15已不被维护，取而代之的是[media9](http://www.ctan.org/pkg/media9)。

安装media9比较麻烦的是需要安装好它所依赖的$\LaTeX$3的package，原本我想通过Arch下的TeXLive Local Manager来解决依赖问题，但AUR的texlive-localmanager-git已经是孤儿包（oraph package），安装出现各种问题，所以我最后是自行到[CTAN](http://www.ctan.org)去下依赖的sty到/usr/share/texmf-dist/tex/latex/\<package-name\>/*（这是Archlinux下的路径，不同发行版的路径可能不同！）再执行
```bash
mktexlsr
```
或
```bash
texhash
```

media9的使用倒还好，照着文档做就可以了。
当前我还不太满意的地方是：

- u3d只能用Matlab生成，无法在octave里产生。（如果octave可以，请告知偶一声哦，偶会很感激的~XD）

- 目前就我测试的结果，3d图只能在windows的Adobe Reader上才能播放，linux下的pdf阅读器（包括Adobe家的）都无法正常显示。（好象是flash的一些问题？）

- 3d图的座标轴文字无法显示。

## 关于$\LaTeX$转html ##
有时候用$\LaTeX$生成文档后常常想把它的内容直接作为一个网页（例如项目的介绍），我很早前就对这个很感兴趣，甚至想自己折腾一个～巧得很，在法国实习的时候，我所在的组里有两位大牛是[bibtex2html](https://www.lri.fr/~filliatr/bibtex2html/)的作者，其中一位researcher（当时还是我组里的vice leader）的个人主页就是用latex文档转成html生成的，也正是他的主页让我发现了之前寻觅已久的工具：[HEVEA](http://hevea.inria.fr/)（PS.如今这位researcher的主页已经改由[yamlpp](https://www.lri.fr/~filliatr/yamlpp.en.html)生成）。

由于法国人对Ocaml编程语言有着一种特殊偏好，HEVEA同样也是由Ocaml所写，可以处理公式、图片、表格、参考文献等等，现在还支持html5，效果不错。以下是我github page的一篇essay的转换效果：
<http://yszheda.github.com/2009-11-01-GBClassicalMusic.html>
PS.这篇essay是我以前写的一篇关于<del>大英腐国</del>大不列颠古典音乐发展的拙见~
