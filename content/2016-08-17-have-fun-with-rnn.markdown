Title: RNN(Recurrent Neural Networks)的有趣实验
Date: 2016-08-17 10:12:00
description: Have Fun With RNN
Tags: CS, tech, RNN, machine learning, data mining
Slug: 20160817-have-fun-with-rnn
Category: tech

前段时间fracting兄分享了[Andrej Karpathy一篇介绍RNN(Recurrent Neural Networks)的文章](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)，我看了之后觉得非常有趣，也用作者Andrej Karpathy写的[char-rnn](https://github.com/karpathy/char-rnn)跑了一些实验玩玩。

# 代码实验 #

作为码农，我最开始自然地想到用`rnn`来训练代码啦！

## lua源代码 ##

我把lua-5.2.3的代码都写到一个文件里作为训练数据。`lua`的代码实在是太精炼了，竟然1M不到，只有544K！我没有更改`char-rnn`的默认参数，跑完了所有的50个`epoch`。取样时我一下就把`temperature`设为1（`temperature`是一个0到1的参数，越大随机性越高，设为1也就是机器原创性最好的条件了），结果还是比我想象中的好很多：

```
LUA_API const char *lua_string(lua_State *L, int toidx);
LUAI_FUNC void luaV_op (lua_State *L);

LUA_API void  (lua_setloge) (lua_State *L, lua_Degrawiol) set) {
  int i;
  for (i = n - "indininple")";
  for (p = luaL_int(func, nup+n, nup), &winzed);
  return ts;
}


LUA_API void lua_touserdata (lua_State *L, int nargp) {
  lua_CFunction fo = h->next;  /* path list of `must the stack is string */
  while (p->cactconul == NA_JUMP) {  /* remove result back */
      lua_xmove(L, 1);  /* remove functions in empty liblering */
      if (!(!ass_epp(lua_Number)(e) - 1))
        lua_pop(L, 1, 1, i, o2);  /* remove it informed is name */
      else {
        lua_getuserval(L, idx2a(L), nvalue(o));
      lua_pushvalue(L, unsupvalue);
          return finuserode(L, nargs, ns);
          finit = strchr(*(s, p, lewvalues));
        lua_pushliteral(L, "tobove");
        tb = uv->u.l.pastpvarsing; i++)  /* logits avoid strings */
        lua_Number k = luaL_checkint(L, 2, 1), lua_isnumber(L, idx) != 0)
                            const char *p, expdesc v, int skiZc, L->clock, int);
      if (lua_getisteop(L, i) != LUA_REGERMADDER) {  /* no move
(followed framaling) */
        L->oldpc = size_t, L->stack + G(L)->currentline;
      checknext(ls, TK_EOS, NO_JUMP);
    i >= casch_k == NO_ORTENS sizeof(char + 1));
    switch (ls->cause)
      luai_writh(g));
    j->basstring = NOPribig/ gch(o)->marked;  /* an open unsigned
instect tocome */
    lua_pushvalue(L, -1);  /* put to use name */
  }
  else {
    int nvars[i] = g->gcvalue[g-- < data = orr.in_PAXTABL;
lua_pushbouceran(L, v2);  /* value stack */
        sav_char_(luaL_optint(L, strfrot));
  c = sig_meth (level) {
      prongc = (**s == '-');
      else {
        break;
    }
    case GCSsweep = mode;  /* skip liblare `next' */
    if (gnodead(t, a)) {  /* called old return */
      lua_pushstring(L, name);
      setnilvalue(o);
  }
  else {
    while (l < l)
      closeL;
      return NULL;
    }
    ttydebuffield(L, LUA_FINTFOCLEN);  /* signed invalid of capture is
a sunpting */
    setsvalue2s(L, L, luaL_checkinteger)(L, 1), LUA_TFuLLEA) +
(L->size = LUA_RIDS);  /* elual library operand matched (filencat) */
    if (stmp) res = rowninizers[i]; i-valid */
    makes = 0;
    }
    if (l <= i < args) {
    luaL_addchar(&b, collectar(s, n, 1));
    if (lua_isnoneornil(L, 2))  /* not noting thave arguments */
      /* stat -> == L->ci->nexps - '?' */
      if (fermst = 1) {
      if (luaS_eqstr(luaL_checknumber(L, 1))) {
        if (*(s != k >> 2] || ttisstring(g->GCasbertocaum(L)) != 0 &&
!luaD_freall(L, hvars(luaL_len(p, 0));
      break;
    }
    case LC_LOADG2(L); lua_pushcclosure(L, idx12x(f));
    setobj2s(L,
                 "L_callint " function");
                                               singleballstatis);
  shrint (lua_tointeger(L, 1), luaT_gettmotableark, (lua__collok(L, 1,
0, 2))) == l2);
  return 1;
}


static int db_setret (lua_State *L) {
  int status = lua_load(L, lua_tointeger(L, L, "cnonal "-") " too pvarial be
* with number of yi-valid function");
  (func == LUA_TFUNCTI NUM: baset2(obj2gco(k));
  checkStaceenstarn(l, nvalue(o));
  api_incr_top(L);
  lua_unlock(L);
}


LUA_API const char *lua_pushstring (lua_State *L, int n, const char *e) {
  const char *msg = lua_tolstring(L, -1, &ls);
  lua_unlock(L);
  if (status == LUA_OK) dectal(SeEMASK);
  return 1;
}


static void pushfunccall (lua_State *L) {
  Labell check;
   lua_assert(argv[i] == LUA_TTABLE);  /* table to compert */
}
```

采样结果比较像的是：

- 结构体和函数命名。有相当一部分和`lua`源代码是一样的，例如`LUA_API`、`LUAI_FUNC`、`lua_State`、`lua_pushvalue`、`luaL_checkint`等等。即使是rnn自造的，也有一些挺符合规范的，例如`lua_string`、`luaV_op`，几乎可以以假乱真。一个稍微差一点的例子是`luaT_gettmotableark`，尽管末尾造的词看不出意义，但仍然符合`lua`源代码里API的命名规则：`lua${一个大写字母表示API类型}_${方法名}`（例如`lua`源代码里，`table`类型的API叫做`luaT_xxx`，`string`类型的叫做`luaS_xxx`，`lua`虚拟机的API叫做`luaV_xxx`）。

- `lua` API中经常用状态机结构体指针作为参数传递，`rnn`采样的结果中，也经常以`lua_State *L`作为函数定义的第一个参数，在调用函数时也常常以`L`作为第一个传入的参数。

比较不理想的是：

- 括号、双引号不成对而引起的语法错误。

- 上下文的语义相关性差，例如上面那段代码最后的函数`pushfunccall`，传入参数`L`是没有被用到的，里面用到的`argv`并没有被声明。

## cocos2d-x源代码 ##

我用`cocos2d-x`的源代码做了实验。`cocos2d-x`的代码就臃肿得多了，合起来有32M。由于数据较大，我训练时就把`rnn_size`调高，设了700，`num_layers`设了2。一开始用CPU训练，特别慢，中途我就弃疗了。后来把OpenCL配置好，用集显来训练，比原来大概快了一倍——毕竟是集显没多少核，所以无法达到10倍的加速比，要是能用以前实验室的K20X跑就好了。

这个实验跑得特别慢，我中间机器还重启过，重跑了`train.lua`，目前只跑了11.32个`epoch`。所以采样结果就不太理想了，要么是一大段注释，要么各种语法错误，这应该跟`cocos2d-x`的代码风格和采用`C`、`C++`、`lua`、`Python`、`Objective-C`等多种语言也有关系。我把`temperature`设为0.5才出来下面东拼西凑得稍微像样的结果：

```
/* </key> TE'Casting C++ Transfer SQLite core constraints.

 */

typedef struct SPender {

    /*! The return code for the content of the content of the control
object may be passed to the first character. "

                                              no tileset -- called
requested to not support android definitions are allocated as the ba

ckup processed to any this

        * directory.

     */

    std::string getControllerDataBits() const;



    /** @brief Retrieves a GLProgram with the specified name of the
current position of the container.

     * @param vector The new z-order of the key of this node below.

     *  @param contains The integer key for the key.

     *  @return the integer key for setting the key to write to the
key for the key.

     *  @param[in]          the number of the key of the key.

    */

    virtual void visit(const char* target, int defaultValueCount);



    /** create a new function with an automatic code from a loader to
the ceater's container with a dictionary, the format of the first

 in the writer. The tile did the

        types since they are not supported

    */

    bool onFloat;

    /*! The cropping to allow the third particular after the width, in
screen coordinates. The value must be the offset to the interfac

e to disk.

     */

    void setUniformValue(const std::string &url);

    /** @brief Returns the number of tilesets the one node's container
window, it means the default world set is the standard orientati

on, the director will be returned.

     *  @return The number of elements also returns NULL.

     *  @return An autorelease object pointer, or a NULL pointer.

    */

    inline const char* getTileGID() const { return _restoreOriginalFrame; };

    inline Vec2 _projection;

    std::string _subStepping;

```

# 自然语言实验 #

## 英文文章 ##

我写了个很简单的爬虫去爬一个[英文音乐网站](http://www.musicweb-international.com/)上的乐评文章，完整地爬了1.8G，但后来我发现：这个网站的样式有改版，而我是通过`css`去筛选乐评的，导致里面有些数据有问题。这个网站上的乐评基本是碟评，我最开始也想到把碟的标题、曲目和乐评都抓出来一起训练，但后来也是因为网页样式不够统一而作罢，只抓了乐评的内容。最后用的数据大概只有两千多篇乐评文章，12M，所有的内容我都过了一遍，删掉了其中有问题的数据——因为当时不知道有问题的数据大概长啥样，只用正则表达式很简单地筛掉了完全没有出现英文字符的数据，所以这两千多条数据我竟然是很蠢地人肉看的orz...

训练时把`rnn_size`设到了300，一共训练了50个`epoch`。采样时我传了一些音乐家的名字作为`-primetext`参数，不过奇怪的是，产生的文本并不是我所想的“命题作文”，里面包含我所设定的音乐家名字的很少。

下面是`temperature`为0.8时产生的一些文本：

```
                    John Eliot Gardiners' music has been recorded by Machiavey
                Brahms and the Telarc hand. Here, though it seems the
‘death’ with Ian Walton in the soloist
                        sounds truly resigned as Bartók in . The
                      assurance composer brings to the narrative evocation
                      climax. There’s much lovely theme for Mass
                    and of the Boris. All composers look forward to
her cycles, and the notes that sticed him much snob-is off-air points
out.  The detailed and the Canzonetta (Sheher
                    is in the collective for distribution for the
                      father to the and spirit of the composer’s voice from DG
                    many Greeks.
                  The last piece is rather than true to the programme
                    for their top recommendation. Add to Ireland’s
                      first performance has one of the most slight lovely small
                      performances of Parama Mozdianic’s music as well
as composer and should
                        write and there is little of its own
individual aspects. The recording of both the recording by Royal Eleno
Stevens, the disc
                      () “…Better and far criticised into the second
movement – most popular of a composer
                        to summarise what was able to depict the way
through it with
                    introspective substance to the rest of the most
                      enjoyable theme. It is worth a major prelude, he
had been a versatile, subdued violinist who points out with
                    the end of the Sarah and of the Roman concerto for
                    a performance in the late CD arrangement of the
soloist which make the strange
                    music that tells the sounds to create in the
                      change of rare and warm long, romantic partnership.
                      So too much of it all recently is perfectly
contradictoned, for me,
                      but the harmonies are in the more prominent
                music at the start to “Goldsmith” because
                    the result is not as if not merely moving in the
first two sessions. From there  were my repeat that one may seem like
a position appear to be listening to my beef?” Protestating the
                concert-half and the same text – making “destinal” the
use of the innocent
                performances in the pleasure of the piece,
                      but there was a time to convince the ‘allegro
                    from the shameful of the experience as the price
of the piece’ (the
                      most movement of Byrd
                    John Carroll) and his own sights of the first movement from
                      his opera too. This was the earlier half of the
text. So this is long realised
                    from one of the best deserts projects which work very well
                    as like yourself, I should even prevent the
correct paces on a prejudice and clear that can also work certainly
                    - a compelling performance as principal force and
his live performers in
                    the shadow of the work. This is the disc of the talking.
                      This was a well-used recording …. Yet for this
                      recording has more intense from a disc amasted
the Roman Bale’s choir,
                        a pastoral player from the following ‘Composer’ (tr.
                      8) the first slow piece all low delicate and
intense and stunning and then chosen music.
```

```
These are composers that would say that John Williams has said that
happily should be struck by the singers of the score for a sequel
evocative and character of several Scarlatti.
  The score is also released and with the price of the separately
sopranctic piece and making a case of practical distinction with the
'methoy of information a tragically devout and distant and generally
small exploration).  Strobbe injustice that the sound is subtly but
distanced over flat illustrate scores by the score by Glennie twistens
and the preceding musicians who are uncommonly detailed with much of
the original MGM track. Debney writes down the score, it is, as this
classic opera, Supermulation player
  of Bernard Herrmann and the writing of the Sinfonia (Herberton Koon
& Glyniform Graham) where he wrote some composers, and is a pleasant
work for very little before I think I am of completely different
settings of the score it is, in the background forty band of score for
 and , one of the most original excerpts only a revelation to warning
you without
computer use I don’t certainly is
be creating a small sound. Morricone’s ‘Discovery’ is all the same
passages featuring luxurial taste. \rAOr tradition and Victoria’s
sampled confusion from the cinema setting.
His admirable period of recognizably derivatives recalling its
subject. Highly recommended.
```

整篇还是比较前言不搭后语，但是单看句子还是比较通顺的，也用了不少音乐家的名字（Gardiner、Brahms、Scarlatti）、厂牌名（Telarc、DG）和音乐术语（Canzonetta、Sinfonia）。

## 中文古诗词 ##

我觉得中国古诗词是极好的数据集：

- 我对把文学作品当做机器学习的数据集也很感兴趣，很好奇最后会产生什么样的“作品”。

- 个人认为机器对于处理structed data更为在行，而在文学中，古典诗词无疑是很有规律的。相比之下，散文、小说等现代文学总归是太散了些。

- 还有其他一些规律性很强的文体，例如日本的俳句和川柳，但我朝的古诗词起码我们能看得懂——字啊！

接下来就是从哪里获得数据的问题了。虽然电子书网站不少，不难下载到这方面文本的txt，但这种txt有些问题我不太满意：

- 会把某些字拆开，例如把“勖”写成“冒力”。

- 会插入一些注解，但我并不想把注释加到训练数据里面。

后来我发现[Chinese Text Project](http://ctext.org/)上有一些资源，而且并没有上述问题，所以我也写了一个简单的[爬虫](https://github.com/yszheda/ctext_crawler)去爬《全唐诗》。不过该网站禁止使用自动下载软件，我最开始忘了调爬虫的`DOWNLOAD_DELAY`参数，所以在爬了一些数据后就被封了...后来又用代理继续爬，总共爬了2.7M（4794首诗），每首诗按照如下格式存成了json文件：

```
   {
      "title" : "《寄溫飛卿箋紙》",
      "content" : "\n三十六鱗充使時，數番猶得裹相思。\n待將袍襖重抄了，盡寫襄陽播掿詞。",
      "author" : " 段成式著"
   },
```

我用`char-rnn`训练了50个`epoch`，诗人`rnn`在脾气最大（`temperature`为1）时所作的大作如果集结出版，就叫它[《循神网诗选》](https://coding.net/u/GaloisPlusPlus/p/galoisplusplus/git/raw/source/source/downloads/code/rnn/quantangshi-sample.json)（循神网=循环神经网络=Recurrent Neural Networks=RNN）吧XDD

《循神网诗选》中，标题和署名是模仿得最难以分辨的，能一眼看出是机器胡诌的极少——例如有一则标题很长的诗。但是诗的内容总体就是胡言乱语了。不过还有一些有意思的句子：“萬里曙山牢”，用“萬里”“牢”形容山，很形象啊；“春風寒酒憔悴殺”，用的词“寒”“憔悴”意象很相近啊。不过由于前言不搭后语，整联写得好的比较少，《循选》读下来，似乎就“秋水燕蘭樹，春暉漫柳霧”还有对仗工整之处。不过刚刚学诗的循神网来说也是个奇迹，循神网真是骨骼精奇啊！

另外要说明一下，`char-rnn`目前是以byte而非utf8的一个word来处理的，神奇的是我几乎没在采样中发现有不符合utf8编码的情况——191首诗里仅有三四首不能正确解码——看来`rnn`竟然很好地掌握了utf8编码的规律。`json`格式就更不在话下啦！

`char-rnn`上也有一些utf8 word的[PR](https://github.com/karpathy/char-rnn/pull/12)，但因为兼容性问题没被接受，我也照着他们改的地方写了个patch，还有点问题，等调好了之后再跑古诗词的实验，应该会有更有趣的结果。

# 其他structed data #

此外，我想到网络数据包也是一种可以用来训练的structed data，所以也用`tcpdump`抓了一些包做实验。不过需要按照[这个issue](https://github.com/karpathy/char-rnn/issues/51#issuecomment-129625032)所说的，稍微改下`char-rnn`的代码。目前还没跑完训练，等训练完50个`epoch`后，再来看看采样生成的数据能用`tcpdump`读取的正确率有多高。


说到非文本的structed data，我还想到了图片、语音和音乐，其中我最感兴趣的还是音乐——各位应该也猜到本乐渣想对音乐下手了吧XD。但是用`rnn`来训练音乐有一些问题，这也使得它暂时还处于我的脑洞阶段：

- 最能反映音乐“原貌”的恐怕还是音频，但是音频文件有不同格式的编解码，并不符合`rnn`的character-level language model。就好比[Andrej Karpathy那篇博文](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)里所举的“hello”的例子：如果“hello”这个文本被加密过，那么两个连续的“l”很可能被加密函数映射成不同的字符，诸如字母"h"后较大可能跟的是字母“e”这种规律也将失效。音频虽然对聆听者而言最能反映音乐“原貌”，但音频文件本身与音乐“原貌”还相距甚远，或许需要从中提取有用的特征作为数据集，才能体现音乐中的有规律之处。

- 不能直接用音频文件，只能退而求其次了。你应该想到一种很古老的将音乐图像化的方式——乐谱——了吧？不过乐谱在我看来还主要是作曲家记谱的工具，用于还原音乐演奏会失真。例如钢琴乐谱上虽然会有踏板记号，但实际演奏时踏板应该踩多深、踩多久？此外乐谱也没有记录下演奏者手指所用的力度等细节，而这些细节往往又是庸才与大师之间的鸿沟。后来我想到一种比乐谱更为精确的方式，那就是[纸卷录音](https://en.wikipedia.org/wiki/Piano_roll)。不过目前虽然不乏用纸卷放在自动钢琴上重放而录制的录音，但纸卷本身却很难在网上找到。

- 即使有了纸卷这种能较精确还原音乐的载体，还有一个关键问题，那就是如何把这种图像转化成文本，而且这种编解码转换应该是可逆的。我发现，就算对于精确度稍逊的乐谱来说，这种要求也很难实现。Andrej Karpathy那篇博文里提到一篇采用rnn训练音乐的[文章](https://highnoongmt.wordpress.com/2015/05/22/lisls-stis-recurrent-neural-networks-for-folk-music-generation/)，里面用了一种很简单的[ABC记谱法](http://abcnotation.com/blog/2010/01/31/how-to-understand-abc-the-basics/)来把乐谱转成文本，再把`rnn`生成的文本转成midi。不过这种记谱法实在是太简陋了，连和弦都无法表示，更遑论多声部的旋律了。


说到编解码，我还想到上个月听的巴西生物艺术家[Eduardo Kac](http://ekac.org/)的一场讲座。其中他早年的一件作品[Genesis](http://www.ekac.org/geninfo2.html)给我的印象很深：Kac从《圣经》里摘了一句话“Let man have dominion over the fish of the sea, and over the fowl of the air, and over every living thing that moves upon the earth.”，把它转成莫尔斯码，又把莫尔斯码转换成ACTG序列。他将这段序列植入细菌中，然后邀请观众对细菌施以紫外光照，让细菌产生变异。在展览结束后，Kac把这段变异后的DNA重新转成莫尔斯码，最后再转成英语（编解码过程和结果可以看[这个网页](http://www.ekac.org/genseries.html)的前两张图）。 Kac的这个作品给了我一些启发，我也由此开下脑洞：如果把某段DNA序列拿给rnn做训练，采样得到新的DNA序列，那么后者将合成什么样的蛋白质、表现出怎样的性状？这想法太疯狂啦，还好我不是biohacker XD
