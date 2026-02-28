Title: cocos2d-x V3.x不规则按钮-续篇
Date: 2015-01-25 01:33:00
description: Irregular Button in cocos2d-x V3.x
Tags: tech, CS, cocos2d-x, cocos2d-x, cocos, cocos2d, button, widget, irregular, 不规则按钮, UI, 按钮, opengl, gl, OpenGL ES, 游戏开发, 手游开发, mobile game, game devolopment
Category: tech
Slug: 20150125-irregular-button-in-cocos2d-x-v3-2
之前曾经在[cocos2d-x V3.x不规则按钮](http://galoisplusplus.coding.me/blog/2014/10/31/irregular-button-in-cocos2d-x-v3/)探讨过在cocos2d-x 3.x版本实现不规则按钮的方法，后来本渣又琢磨了下仿照RenderTexture类调用OpenGL ES API来获取图片像素信息的方式。这种方式由于按钮图片的Texture已在内存中，且不需要解析图片文件格式，因此相比之前用Image::initWithImageFile还是要快一些的。

重写的`loadNormalTransparentInfo`函数如下：

<!-- more -->

```c++
void IrregularButton::loadNormalTransparentInfo()
{
#ifdef DEBUG
    auto start = std::chrono::steady_clock::now();
#endif
    
    Sprite* normalRenderer = static_cast<Sprite*>(_buttonNormalRenderer);
    auto normalTexture = normalRenderer->getTexture();
    const Size& s = normalTexture->getContentSizeInPixels();
    
    int savedBufferWidth = (int)s.width;
    int savedBufferHeight = (int)s.height;
    
    GLubyte *buffer = nullptr;
    
    // the FBO which cocos2dx used is not window-system-provided (non-zero id)
    GLint oldFBO;
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &oldFBO);
    
    GLuint framebuffer;
    glGenFramebuffers(1, &framebuffer);
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
    
    glBindTexture(GL_TEXTURE_2D, normalTexture->getName());
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA4, savedBufferWidth, savedBufferHeight, 0, GL_RGBA, GL_UNSIGNED_BYTE, 0);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, normalTexture->getName(), 0);
    
    CCASSERT(glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE, "Could not attach texture to framebuffer");
    
    buffer = new (std::nothrow) GLubyte[savedBufferWidth * savedBufferHeight * 4];
    
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, savedBufferWidth, savedBufferHeight, GL_RGBA, GL_UNSIGNED_BYTE, buffer);
    glBindFramebuffer(GL_FRAMEBUFFER, oldFBO);
    
    auto dataLen = savedBufferWidth * savedBufferHeight * 4;
    if (normalTransparent_ != nullptr) {
        delete[] normalTransparent_;
    }
    normalImageWidth_ = savedBufferWidth;
    normalImageHeight_ = savedBufferHeight;
    normalTransparent_ = new bool[dataLen / (sizeof(unsigned char) * 4)];
    for (auto i = 0; i < normalImageHeight_; i++) {
        for (auto j = 0; j < normalImageWidth_; j++) {
            normalTransparent_[i * normalImageWidth_ + j] = (buffer[(i * normalImageWidth_ + j) * 4 + 3] == 0);
        }
    }
    
    CC_SAFE_DELETE_ARRAY(buffer);
    
#ifdef DEBUG
    auto end = std::chrono::steady_clock::now();
    auto totalTime = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    printf("load from memory: %lld ms\n", totalTime.count());
#endif
}
```

完整代码请参考：
[cocos2d-x-irregular-button](https://github.com/yszheda/cocos2d-x-irregular-button)
