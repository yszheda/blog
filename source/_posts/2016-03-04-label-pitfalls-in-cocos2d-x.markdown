---
layout: post
title: "cocos2d-x文本类Label的一些坑"
date: 2016-03-04 11:22
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
description: Label pitfalls in cocos2d-x
---

cocos2d-x v3.2的Label实现bug真是不少，前段时间恰好排查了几个与之相关的问题，在此记录一下。

# 文字换行 #

文字换行是一个困扰我们挺长时间的问题：之前就常常有文字超过指定长度却没有换行的情况出现，后来加入韩文、泰文等“奇葩”文字后问题就更严重了。cocos2d-x引擎在v3.2后大改了这部分的实现，但由于涉及的改动太多，无法作为一个独立的patch单独apply过来，而且更新引擎版本对我们上线的游戏代价太大，也不可行。好在本渣不久前终于从各种游戏系统开发中抽出时间，完整地把这部分代码review了一遍，结果发现全是`LabelTextFormatter::multilineText`中几行代码惹的祸，缩小了排查范围便不难fix了：

<!-- more -->

```cpp
bool LabelTextFormatter::multilineText(Label *theLabel)
{
    auto limit = theLabel->_limitShowCount;
    auto strWhole = theLabel->_currentUTF16String;

    std::vector<char16_t> multiline_string;
    multiline_string.reserve( limit );

    std::vector<char16_t> last_word;
    last_word.reserve( 25 );

    bool   isStartOfLine  = false, isStartOfWord = false;
    float  startOfLine = -1, startOfWord   = -1;

    int skip = 0;
    
    int tIndex = 0;
    float scalsX = theLabel->getScaleX();
    float lineWidth = theLabel->_maxLineWidth;

    bool breakLineWithoutSpace = theLabel->_lineBreakWithoutSpaces;
    Label::LetterInfo* info = nullptr;

    for (int j = 0; j+skip < limit; j++)
    {            
        info = & theLabel->_lettersInfo.at(j+skip);

        unsigned int justSkipped = 0;

        while (info->def.validDefinition == false)
        {
            justSkipped++;
            tIndex = j+skip+justSkipped;
            if (strWhole[tIndex-1] == '\n')
            {
                StringUtils::trimUTF16Vector(last_word);

                last_word.push_back('\n');
                multiline_string.insert(multiline_string.end(), last_word.begin(), last_word.end());
                last_word.clear();
                isStartOfWord = false;
                isStartOfLine = false;
                startOfWord = -1;
                startOfLine = -1;
            }
            if(tIndex < limit)
            {
                info = & theLabel->_lettersInfo.at( tIndex );
            }
            else
                break;
        }
        skip += justSkipped;
        tIndex = j + skip;

        if (tIndex >= limit)
            break;

        char16_t character = strWhole[tIndex];

        if (!isStartOfWord)
        {
            startOfWord = info->position.x * scalsX;
            isStartOfWord = true;
        }

        if (!isStartOfLine)
        {
            startOfLine = startOfWord;
            isStartOfLine  = true;
        }
        
        // 1) Whitespace.
        // 2) This character is non-CJK, but the last character is CJK
        bool isspace = StringUtils::isUnicodeSpace(character);
        bool isCJK = false;
        if(!isspace)
        {
            isCJK = StringUtils::isCJKUnicode(character);
        }

        if (isspace ||
            (!last_word.empty() && StringUtils::isCJKUnicode(last_word.back()) && !isCJK))
        {
            // if current character is white space, put it into the current word
            if (isspace) last_word.push_back(character);

            multiline_string.insert(multiline_string.end(), last_word.begin(), last_word.end());
            last_word.clear();
            isStartOfWord = false;
            startOfWord = -1;
            // put the CJK character in the last word
            // and put the non-CJK(ASCII) character in the current word
            if (!isspace) last_word.push_back(character);

            continue;
        }

        float posRight = (info->position.x + info->def.xAdvance) * scalsX;
        // Out of bounds.
        if (posRight - startOfLine > lineWidth)
        {
            if (!breakLineWithoutSpace && !isCJK)
            {
                last_word.push_back(character);

                int found = StringUtils::getIndexOfLastNotChar16(multiline_string, ' ');
                if (found != -1)
                    StringUtils::trimUTF16Vector(multiline_string);
                else
                    multiline_string.clear();

                if (multiline_string.size() > 0)
                    multiline_string.push_back('\n');

                isStartOfLine = false;
                startOfLine = -1;
            }
            else
            {
                StringUtils::trimUTF16Vector(last_word);

                //issue #8492:endless loop if not using system font, and constrained length is less than one character width
                if (isStartOfLine && startOfWord == startOfLine && last_word.size() == 0)
                    last_word.push_back(character);
                else
                    --j;

                last_word.push_back('\n');
                
                multiline_string.insert(multiline_string.end(), last_word.begin(), last_word.end());
                last_word.clear();

                isStartOfWord = false;
                isStartOfLine = false;
                startOfWord = -1;
                startOfLine = -1;
            }
        }
        else
        {
            // Character is normal.
            last_word.push_back(character);
        }
    }

    multiline_string.insert(multiline_string.end(), last_word.begin(), last_word.end());

    std::u16string strNew(multiline_string.begin(), multiline_string.end());

    theLabel->_currentUTF16String = strNew;
    theLabel->computeStringNumLines();
    theLabel->computeHorizontalKernings(theLabel->_currentUTF16String);

    return true;
}
```

# 描边显示不均匀 #

这是我们之前常常被美术大大们吐槽的地方：文字加描边后有的地方粗有的地方细，好蓝看啊...
后来本渣在网上看到大神的[patch](http://my.oschina.net/u/1414326/blog/279456?fromerr=xX53o9Rq)，又自我扫盲了FreeType的基础概念，总算看懂了。cocos2d-x引擎在`FontFreeType::getGlyphBitmap`函数中会把不带描边的文字字形（glyph）和描边文字字形的bitmap都存到同一个数组里，在`FontFreeType::renderCharAt`中渲染。而描边文字字形是调用FreeType API生成的，其轮廓和不带描边的文字字形轮廓的间距并不能确保一定是我们所指定的描边大小，这个patch便是记下该间距和描边大小的offset，在拷贝bitmap时根据offset作调整。
其实cocos2d-x引擎在v3.2之后也改了这部分代码，但其实现思路却不如上述patch清晰，于是本渣便用了后者，并做了一点微小改动。

```cpp
unsigned char* FontFreeType::getGlyphBitmap(unsigned short theChar, long &outWidth, long &outHeight, Rect &outRect,int &xAdvance)
{
    bool invalidChar = true;
    unsigned char * ret = nullptr;

    do 
    {
        if (!_fontRef)
            break;

        auto glyphIndex = FT_Get_Char_Index(_fontRef, theChar);
        if(!glyphIndex)
            break;

        if (_distanceFieldEnabled)
        {
            if (FT_Load_Glyph(_fontRef,glyphIndex,FT_LOAD_RENDER | FT_LOAD_NO_HINTING | FT_LOAD_NO_AUTOHINT))
                break;
        }
        else
        {
            if (FT_Load_Glyph(_fontRef,glyphIndex,FT_LOAD_RENDER | FT_LOAD_NO_AUTOHINT))
                break;
        }

        outRect.origin.x    = _fontRef->glyph->metrics.horiBearingX >> 6;
        outRect.origin.y    = - (_fontRef->glyph->metrics.horiBearingY >> 6);
        outRect.size.width  =   (_fontRef->glyph->metrics.width  >> 6);
        outRect.size.height =   (_fontRef->glyph->metrics.height >> 6);

        xAdvance = (static_cast<int>(_fontRef->glyph->metrics.horiAdvance >> 6));

        outWidth  = _fontRef->glyph->bitmap.width;
        outHeight = _fontRef->glyph->bitmap.rows;
        ret = _fontRef->glyph->bitmap.buffer;

        // apply patch from: http://my.oschina.net/u/1414326/blog/279456?fromerr=xX53o9Rq
        if (_outlineSize > 0)
        {
            auto copyBitmap = new unsigned char[outWidth * outHeight];
            memcpy(copyBitmap, ret, outWidth * outHeight * sizeof(unsigned char));

            long bitmapWidth;
            long bitmapHeight;
            FT_BBox bbox;
            auto outlineBitmap = getGlyphBitmapWithOutline(theChar, bbox);
            if(outlineBitmap == nullptr)
            {
                ret = nullptr;
                delete [] copyBitmap;
                break;
            }

            long glyphMinX = outRect.origin.x;
            long glyphMaxX = outRect.origin.x + outWidth;
            long glyphMinY = -outHeight - outRect.origin.y;
            long glyphMaxY = -outRect.origin.y;
            
            auto outlineMinX = bbox.xMin >> 6;
            auto outlineMaxX = bbox.xMax >> 6;
            auto outlineMinY = bbox.yMin >> 6;
            auto outlineMaxY = bbox.yMax >> 6;
            auto outlineWidth = outlineMaxX - outlineMinX;
            auto outlineHeight = outlineMaxY - outlineMinY;

            bitmapWidth = outlineMaxX - outlineMinX;
            bitmapHeight = outlineMaxY - outlineMinY;

            int offsetWidth = 0;
            int offsetHeight = 0;

            if(glyphMinX - outlineMinX != _outlineSize) {
                offsetWidth = glyphMinX - outlineMinX - _outlineSize;
            }
            if(outlineMaxY - glyphMaxY != _outlineSize) {
                offsetHeight = outlineMaxY - glyphMaxY - _outlineSize;
            }

            long index;
            auto blendImage = new unsigned char[bitmapWidth * bitmapHeight * 2];
            memset(blendImage, 0, bitmapWidth * bitmapHeight * 2);
            for (int x = 0; x < bitmapWidth; ++x)
            {
                for (int y = 0; y < bitmapHeight; ++y)
                {
                    index = x + y * bitmapWidth;
                    blendImage[2 * index] = outlineBitmap[index];
                }
            }

            long maxX = outWidth + _outlineSize;
            long maxY = outHeight + _outlineSize;
            for (int x = _outlineSize + offsetWidth; x < maxX + offsetWidth & x < bitmapWidth; ++x)
            {
                for (int y = _outlineSize + offsetHeight; y < maxY + offsetHeight & y < bitmapHeight; ++y)
                {
                    index = x + y * bitmapWidth;
                    long index2 = x - _outlineSize - offsetWidth + (y - _outlineSize - offsetHeight) * outWidth;
                    blendImage[2 * index + 1] = copyBitmap[index2];
                }
            }

            outRect.origin.x = bbox.xMin >> 6;
            outRect.origin.y = - (bbox.yMax >> 6);

            xAdvance += bitmapWidth - outRect.size.width;

            outRect.size.width  =  bitmapWidth;
            outRect.size.height =  bitmapHeight;
            outWidth  = bitmapWidth;
            outHeight = bitmapHeight;

            delete [] outlineBitmap;
            delete [] copyBitmap;
            ret = blendImage;
        }

        invalidChar = false;
    } while (0);

    if (invalidChar)
    {
        outRect.size.width  = 0;
        outRect.size.height = 0;
        xAdvance = 0;

        return nullptr;
    }
    else
    {
       return ret;
    }
}
```

# 其他 #

由于v3.2的Label实现质量不高，所以还是得时时关注cocos2d-x引擎这方面的改动。例如前段时间便apply了上游的这个patch：

```
@@ -154,13 +154,15 @@ bool FontFreeType::createFontObject(const std::string &fontName, int fontSize)
 
 FontFreeType::~FontFreeType()
 {
-    if (_stroker)
-    {
-        FT_Stroker_Done(_stroker);
-    }
-    if (_fontRef)
-    {
-        FT_Done_Face(_fontRef);
+    if (_FTInitialized) {
+        if (_stroker)
+        {
+            FT_Stroker_Done(_stroker);
+        }
+        if (_fontRef)
+        {
+            FT_Done_Face(_fontRef);
+        }
     }
 
     s_cacheFontData[_fontName].referenceCount -= 1;
```
