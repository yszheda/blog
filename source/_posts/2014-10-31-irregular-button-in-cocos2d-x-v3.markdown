---
layout: post
title: "cocos2d-x V3.x不规则按钮"
date: 2014-10-31 23:23
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, cocos, cocos2d, button, widget, irregular, 不规则按钮, UI, 按钮, opengl, gl, OpenGL ES, 游戏开发, 手游开发, mobile game, game devolopment
description: Irregular Button in cocos2d-x V3.x
---
cocos2d-x的按钮默认是以长方形作为点击区域的，实际使用时这确实很蛋疼。之前有大牛研究了如何获取图片的透明度实现不规则点击区域的方法，例如：

- [cocos2d-x开发笔记：获取Sprite上某一个点的透明度，制作不规则按钮](http://www.cnblogs.com/Androider123/p/3795050.html)

- [在 cocos2d-x 中获取纹理的像素值](http://zengrong.net/post/2104.htm)

可惜在cocos2d-x v3.0以上的版本，他们的方法都失效了，因此本渣也不得不自行琢磨这一块的实现。

之前方法的核心在于：图片每个像素点的RGBA信息被保存在Image类中，这个底层类并不会随着图片Node的创建而留在内存中（否则其内存占用量可想而知）。然而，在create出一个Sprite后，可以在内存中拿到它的Frame，再用RenderTextue重画一次拿到原始的Image，这样就可以判断图片上任意点的像素了。如果某点像素的Alpha值为0，则说明它是透明的，点击在该点是无效的。

这种方法是所以会失效，是因为cocos2d-x v3.0的RenderTexture是异步渲染的，导致拿到的Image并不是最后渲染的结果。本渣用了一种简单粗暴的方法，用Image类的initWithImageFile()方法去初始化Image对象，这样就确保了对象的数据是正确的。但是这种方法会有文件IO，不宜频繁调用，因此我只在一开始时创建一次，用一个bool数组保存每个像素点是否透明度为0的信息。每次触发点击事件时，就根据这个数组的值来判断点击是否有效。我把这部分逻辑封装到`cocos2d::ui::Button`的子类`IrregularButton`中，具体代码详见：
[cocos2d-x-irregular-button](https://github.com/yszheda/cocos2d-x-irregular-button)

<!-- more -->

```c++
/*
 * =====================================================================================
 *
 *       Filename:  IrregularButton.h
 *
 *    Description:  
 *
 *        Version:  1.0
 *        Created:  2014/10/29
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Shuai Yuan (), 
 *   Organization:  
 *
 * =====================================================================================
 */
#ifndef __IRREGULAR_BUTTON_H__
#define __IRREGULAR_BUTTON_H__ 

#include "cocos2d.h"
#include "ui/CocosGUI.h"

/*
 * =====================================================================================
 *        Class:  IrregularButton
 *  Description:  
 * =====================================================================================
 */
class IrregularButton : public cocos2d::ui::Button
{
    public:
        /* ====================  LIFECYCLE     ======================================= */
        IrregularButton ();                                     /* constructor      */
        virtual ~IrregularButton ();                            /* destructor       */

        static IrregularButton* create();
        static IrregularButton* create(const std::string& normalImage,
                const std::string& selectedImage = "",
                const std::string& disableImage = "",
                cocos2d::ui::Widget::TextureResType texType = cocos2d::ui::Widget::TextureResType::LOCAL);

        /* ====================  ACCESSORS     ======================================= */

        /* ====================  MUTATORS      ======================================= */

        /* ====================  OPERATORS     ======================================= */

        virtual bool hitTest(const cocos2d::Vec2 &pt) override;
    protected:
        virtual bool init() override;
        virtual bool init(const std::string& normalImage,
                const std::string& selectedImage = "",
                const std::string& disableImage = "",
                cocos2d::ui::Widget::TextureResType texType = cocos2d::ui::Widget::TextureResType::LOCAL) override;
        void loadNormalTransparentInfo();
        bool getIsTransparentAtPoint(cocos2d::Vec2 point);

        /* ====================  DATA MEMBERS  ======================================= */

    private:
        /* ====================  DATA MEMBERS  ======================================= */
        int normalImageWidth_;
        int normalImageHeight_;
        bool* normalTransparent_;

}; /* -----  end of class IrregularButton  ----- */


#endif /* __IRREGULAR_BUTTON_H__ */
```

```c++
/*
 * =====================================================================================
 *
 *       Filename:  IrregularButton.cpp
 *
 *    Description:  
 *
 *        Version:  1.0
 *        Created:  2014/10/30
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Shuai Yuan (), 
 *   Organization:  
 *
 * =====================================================================================
 */
#include "IrregularButton.h"

USING_NS_CC;
using namespace ui;

IrregularButton::IrregularButton():
    Button(),
    normalTransparent_(nullptr)
{}

IrregularButton::~IrregularButton()
{
    delete[] normalTransparent_;
}

IrregularButton* IrregularButton::create()
{
    IrregularButton* widget = new IrregularButton();
    if (widget && widget->init()) {
        widget->autorelease();
        return widget;
    }
    CC_SAFE_DELETE(widget);
    return nullptr;
}

IrregularButton* IrregularButton::create(const std::string& normalImage,
        const std::string& selectedImage,
        const std::string& disableImage,
        TextureResType texType)
{
    IrregularButton* btn = new IrregularButton;
    if (btn && btn->init(normalImage, selectedImage, disableImage, texType)) {
        btn->autorelease();
        return btn;
    }
    CC_SAFE_DELETE(btn);
    return nullptr;
}

bool IrregularButton::init(const std::string &normalImage,
                  const std::string& selectedImage ,
                  const std::string& disableImage,
                  TextureResType texType)
{
    bool ret = true;
    do {
        if (!Button::init(normalImage, selectedImage, disableImage, texType)) {
            ret = false;
            break;
        }
    } while (0);
    loadNormalTransparentInfo();
    return ret;
}

bool IrregularButton::init()
{
    if (Button::init())
    {
        return true;
    }
    return false;
}

void IrregularButton::loadNormalTransparentInfo()
{
    Image* normalImage = new Image();
    normalImage->initWithImageFile(_normalFileName);
    normalImageWidth_ = normalImage->getWidth();
    normalImageHeight_ = normalImage->getHeight();

    auto dataLen = normalImage->getDataLen();
    if (normalTransparent_ != nullptr) {
        delete[] normalTransparent_;
    }
    auto normalPixels = normalImage->getData();
    normalTransparent_ = new bool[dataLen / (sizeof(unsigned char) * 4)];
    for (auto i = 0; i < normalImageHeight_; i++) {
        for (auto j = 0; j < normalImageWidth_; j++) {
            normalTransparent_[i * normalImageWidth_ + j] = (normalPixels[(i * normalImageWidth_ + j) * 4 + 3] == 0);
        }
    }

    delete normalImage;
}

bool IrregularButton::getIsTransparentAtPoint(cocos2d::Vec2 point)
{
    point.y = _buttonNormalRenderer->getContentSize().height - point.y;
    int x = (int) point.x - 1;
    if (x < 0) {
        x = 0;
    } else if (x >= normalImageWidth_) {
        x = normalImageWidth_ - 1;
    }
    int y = (int) point.y - 1;
    if (y < 0) {
        y = 0;
    } else if (y >= normalImageHeight_) {
        y = normalImageHeight_ - 1;
    }
    return normalTransparent_[normalImageWidth_ * y + x];
}

bool IrregularButton::hitTest(const Vec2 &pt)
{
    Vec2 localLocation = _buttonNormalRenderer->convertToNodeSpace(pt);
    Rect validTouchedRect;
    validTouchedRect.size = _buttonNormalRenderer->getContentSize();
    if (validTouchedRect.containsPoint(localLocation) && getIsTransparentAtPoint(localLocation) == false)
    {
        return true;
    }
    return false;
}
```

