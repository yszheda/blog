---
layout: post
title: "BMFont字体生成脚本"
date: 2014-09-02 01:22
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment, BMFont, FNT, 字体
description: BMFont Generator
---

最近我们游戏需要用到`BMFont`字体，但又没有好的免费工具给美术大大们生成字体所需要的图集和`fnt`文件。
好在本渣在网上找到了一份详尽的`fnt`格式[说明文档](http://www.angelcode.com/products/bmfont/doc/file_format.html)，我们三位前端开发者都是用Mac，所以本渣就用自己熟悉的bash写了一个生成`BMFont`的脚本。
我们只需要让美术大大们出好字体里每个字符的图片png，将图片命名成字符的名字（例如数字0的图片需要命名成“0.png”），放到某个目录下，执行脚本，指定图片目录（也就是脚本里的`<inputPath>`）和`BMFont`字体的名字（也就是脚本里的`<prefix>`）就可以了。最后这个脚本会在图片目录下创建一个叫做`output`的目录，里面就有图集`<prefix>.png`和配置文件`<prefix>.fnt`。

```sh
#!/bin/bash
# Generate BMFont fnt and atlas from the image files of each character.

if [ $1 == "-h" ]; then
    echo "Usage: "
    echo "$(basename $0) <inputPath> <prefix>"
    echo "generate png and fnt under <inputPath>/output"
    echo "<inputPath>: path containing images"
    echo "<prefix>: prefix of output file names"
    exit 0
fi

inputPath=$1
prefix=$2
outputPath="./output"
if [[ $3 ]]; then
    outputPath = $3
fi

localPngFile=${prefix}.png
pngFile=${outputPath}/${localPngFile}
fntFile=${outputPath}/${prefix}.fnt
pngFileList=($(ls ${inputPath} | grep png | sort))

charWidth=$(ls ${inputPath} | grep png | head -1 | xargs file | awk -F',' '{print $2}'| awk '/x/{print $1}')
charHeight=$(ls ${inputPath} | grep png | head -1 | xargs file | awk -F',' '{print $2}'| awk '/x/{print $3}')

imageNum=$(find ${inputPath} -d 1 -name "*.png" | wc -l)
# remove leading whitespace
shopt -s extglob
imageNum=${imageNum##*( )}
shopt -u extglob


clean ()
{
    if [[ -d ${outputPath} ]]; then
        rm ${outputPath}/*
    else
        mkdir ${outputPath}
    fi
}


mergePngs ()
{
    if ! type convert > /dev/null; then
        echo "You need to install [ImageMagic](http://www.imagemagick.org/)."
    else
        # ATTENTION: if you are using BSD/Mac, use the following command:
        find ${inputPath} -d 1 -name "*.png" | sort | tr '\n' ' ' | xargs -J % convert % +append ${pngFile}
        # ATTENTION: if you are using UNIX/GNU Linux, use the following command instead:
        # find ${inputPath} -d 1 -name "*.png" | sort | tr '\n' ' ' | xargs -I % convert % +append ${pngFile}
    fi
}

##################################################
# Reference Document:
# http://www.angelcode.com/products/bmfont/doc/file_format.html
##################################################
# info: This tag holds information on how the font was generated.
##################################################
# face    This is the name of the true type font.
face="Arial"
# size    The size of the true type font.
size=32
# bold    The font is bold.
bold=0
# italic  The font is italic.
italic=0
# charset The name of the OEM charset used (when not unicode).
charset=""
# unicode Set to 1 if it is the unicode charset.
unicode=0
# stretchH    The font height stretch in percentage. 100% means no stretch.
stretchH=100
# smooth  Set to 1 if smoothing was turned on.
smooth=1
# aa  The supersampling level used. 1 means no supersampling was used.
aa=1
# padding The padding for each character (up, right, down, left).
paddingUp=0
paddingRight=0
paddingDown=0
paddingLeft=0
# spacing The spacing for each character (horizontal, vertical).
spacingH=0
spacingV=0
# outline The outline thickness for the characters.
outline=0
##################################################
# common: This tag holds information common to all characters.
##################################################
# lineHeight  This is the distance in pixels between each line of text.
lineHeight=${charHeight}
# base    The number of pixels from the absolute top of the line to the base of the characters.
base=${charHeight}
# scaleW  The width of the texture, normally used to scale the x pos of the character image.
scaleW=256
# scaleH  The height of the texture, normally used to scale the y pos of the character image.
scaleH=256
# pages   The number of texture pages included in the font.
pages=1
# packed  Set to 1 if the monochrome characters have been packed into each of the texture channels. In this case alphaChnl describes what is stored in each channel.
packed=0
# alphaChnl   Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.
alphaChnl=1
# redChnl Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.
redChnl=0
# greenChnl   Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.
greenChnl=0
# blueChnl    Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.
blueChnl=0
##################################################
# page: This tag gives the name of a texture file. There is one for each page in the font.
##################################################
# id  The page id.
id=0
# file    The texture file name.
file=${localPngFile}
##################################################
# char: This tag describes on character in the font. There is one for each included character in the font.
##################################################
# id  The character id.
# x   The left position of the character image in the texture.
# y   The top position of the character image in the texture.
y=0
# width   The width of the character image in the texture.
width=${charWidth}
# height  The height of the character image in the texture.
height=${charHeight}
# xoffset How much the current position should be offset when copying the image from the texture to the screen.
xoffset=0
# yoffset How much the current position should be offset when copying the image from the texture to the screen.
yoffset=0
# xadvance    How much the current position should be advanced after drawing the character.
xadvance=${charWidth}
# page    The texture page where the character image is found.
page=0
# chnl    The texture channel where the character image is found (1 = blue, 2 = green, 4 = red, 8 = alpha, 15 = all channels).
chnl=15
##################################################
# kerning: The kerning information is used to adjust the distance between certain characters, e.g. some characters should be placed closer to each other than others.
##################################################
# first   The first character id.
# second  The second character id.
# amount  How much the x position should be adjusted when drawing the second character immediately following the first.
##################################################


writeInfo ()
{
    echo "info face=\"${face}\" size=${size} bold=${bold} italic=${italic} charset=\"${charset}\" unicode=${unicode} stretchH=${stretchH} smooth=${smooth} aa=${aa} padding=${paddingUp},${paddingRight},${paddingDown},${paddingLeft} spacing=${spacingH},${spacingV} outline=${outline}"
    echo "info face=\"${face}\" size=${size} bold=${bold} italic=${italic} charset=\"${charset}\" unicode=${unicode} stretchH=${stretchH} smooth=${smooth} aa=${aa} padding=${paddingUp},${paddingRight},${paddingDown},${paddingLeft} spacing=${spacingH},${spacingV} outline=${outline}" >> ${fntFile}
}


writeCommon ()
{
    echo "common lineHeight=${lineHeight} base=${base} scaleW=${scaleW} scaleH=${scaleH} pages=${pages} packed=${packed} alphaChnl=${alphaChnl} redChnl=${redChnl} greenChnl=${greenChnl} blueChnl=${blueChnl}"
    echo "common lineHeight=${lineHeight} base=${base} scaleW=${scaleW} scaleH=${scaleH} pages=${pages} packed=${packed} alphaChnl=${alphaChnl} redChnl=${redChnl} greenChnl=${greenChnl} blueChnl=${blueChnl}" >> ${fntFile}
}


writePage ()
{
    echo "page id=${id} file=\"${file}\""
    echo "page id=${id} file=\"${file}\"" >> ${fntFile}
}


writeChars ()
{
    echo "chars count=${imageNum}"
    echo "chars count=${imageNum}" >> ${fntFile}
    declare -i i=0
    for file in "${pngFileList[@]}"
    do
        letter=$(echo ${file} | cut -d'.' -f 1 | tail -c 2)
        id=$(printf '%d' "'${letter}")
        let "x = charWidth * i"
        echo "char id=${id} x=${x} y=${y} width=${width} height=${height} xoffset=${xoffset} yoffset=${yoffset} xadvance=${xadvance} page=${page} chnl=${chnl}"
        echo "char id=${id} x=${x} y=${y} width=${width} height=${height} xoffset=${xoffset} yoffset=${yoffset} xadvance=${xadvance} page=${page} chnl=${chnl}" >> ${fntFile}
        let "i += 1"
    done
}


clean
mergePngs
touch ${fntFile}
writeInfo
writeCommon
writePage
writeChars
```

需要说明的是，本渣也只是出于工作需求去写这个脚本，并没有时间去开发一个完整的BMFont字体生成器，所以功能还是有局限的：

- 目前只支持png，但这很容易拓展，我用的是`ImageMagic`来生成图集，`ImageMagic`可以处理很多图片格式。

- 目前图集只有一行字符，因为我们用到的BMFont里字符数不多，没有做多行的必要。

- 目前只支持每个字符图片大小一致的情况，这也是由我们美术大大出的图片资源决定的，暂时没有扩展的需求。

- 暂时没有kerning等字体设置。
