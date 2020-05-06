---
layout: post
title: "为cocos2d-x的TableViewCell控件添加点击及长按支持"
date: 2014-11-18 23:23
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x
description: Touchable and LongTouchEvent-supported TableViewCell in cocos2d-x
---
再次来聊一聊cocos2d-x的`TableView`。之前之所以用继承`TableView`的方式实现2D的`GridView`是因为用到`TableView`点击事件的地方涉及到全局数据的复杂处理，这块处理放到`TableViewDelegate`类的`tableCellTouched`比较合理。但这个函数在cell被点击时都会被调用，而实际游戏里一个cell往往只有部分UI才能被点击（所以当点击事件只与这个cell的数据相关时，直接把点击事件处理放到cell内部实现才是王道），故而我们需要对cell的点击区域做进一步的限制。为此，我封装了一个`TableViewCell`的子类来实现这一功能：

```
TouchableTableViewCell::TouchableTableViewCell():
    isValidTouched_(false),
    touchableNode_(nullptr)
{}

TouchableTableViewCell::~TouchableTableViewCell()
{}

bool TouchableTableViewCell::init()
{
    if (!TableViewCell::init()) {
        return false;
    }
    return true;
}

void TouchableTableViewCell::initTouchListener()
{
    auto touchListener = EventListenerTouchOneByOne::create();
    CC_SAFE_RETAIN(touchListener);
    Rect validTouchedRect;
    validTouchedRect.size = touchableNode_->getContentSize();
    touchListener->onTouchBegan = [=] (cocos2d::Touch* touch, cocos2d::Event* event) {
        if (touchableNode_ == nullptr) {
            return false;
        }
        auto touchLocation = touch->getLocation();
        auto localLocation = touchableNode_->convertToNodeSpace(touchLocation);
        if (validTouchedRect.containsPoint(localLocation)) {
            isValidTouched_ = true;
            return true;
        } else {
            isValidTouched_ = false;
            return false;
        }
    };
    touchListener->onTouchMoved = [=] (cocos2d::Touch* touch, cocos2d::Event* event) {
        auto touchLocation = touch->getLocation();
        auto localLocation = touchableNode_->convertToNodeSpace(touchLocation);
        if (validTouchedRect.containsPoint(localLocation)) {
            isValidTouched_ = true;
        } else {
            isValidTouched_ = false;
        }
    };
    touchListener->onTouchEnded = touchListener->onTouchMoved;
    touchListener->onTouchCancelled = touchListener->onTouchEnded;
    _eventDispatcher->addEventListenerWithSceneGraphPriority(touchListener, this);
}

void TouchableTableViewCell::setTouchableNode(cocos2d::Node* touchableNode)
{
    touchableNode_ = touchableNode;
    initTouchListener();
}
```

使用时只需让实际的`TableViewCell`类继承`TouchableTableViewCell`，在`tableCellTouched`函数中判断`isValidTouched_`即可。

另外，有时候我们需要让`TableViewCell`响应长按事件，我在之前的`TouchableTableViewCell`类上又做了一层封装，主要使用调度器来实现长按：

```
const std::string LongTouchableTableViewCell::SCHEDULE_KEY = "LONG_TOUCHABLE_TABLE_VIEW_CELL";
const float LongTouchableTableViewCell::LONG_TOUCH_INTERVAL = 0.2f;

LongTouchableTableViewCell::LongTouchableTableViewCell():
    TouchableTableViewCell(),
    isTouchHold_(false),
    isLongTouched_(false),
    longTouchedCallback_(nullptr)
{}

LongTouchableTableViewCell::~LongTouchableTableViewCell()
{}

bool LongTouchableTableViewCell::init()
{
    if (!TouchableTableViewCell::init()) {
        return false;
    }
    return true;
}

void LongTouchableTableViewCell::initTouchListener()
{
    auto touchListener = EventListenerTouchOneByOne::create();
    CC_SAFE_RETAIN(touchListener);
    Rect validTouchedRect;
    validTouchedRect.size = touchableNode_->getContentSize();
    touchListener->onTouchBegan = [=] (cocos2d::Touch* touch, cocos2d::Event* event) {
        if (touchableNode_ == nullptr) {
            return false;
        }
        auto touchLocation = touch->getLocation();
        auto localLocation = touchableNode_->convertToNodeSpace(touchLocation);
        if (validTouchedRect.containsPoint(localLocation)) {
            isValidTouched_ = true;
            isTouchHold_ = true;
            isLongTouched_ = false;
            
            Director::getInstance()->getScheduler()->schedule([=](float) {
                if (isTouchHold_) {
                    isLongTouched_ = true;
                    if (longTouchedCallback_ != nullptr) {
                        longTouchedCallback_();
                    }
                }
                Director::getInstance()->getScheduler()->unschedule(SCHEDULE_KEY, this);
            }, this, LONG_TOUCH_INTERVAL, 0, 0.0f, false, SCHEDULE_KEY);

            return true;
        } else {
            isValidTouched_ = false;
            isTouchHold_ = false;
            isLongTouched_ = false;

            return false;
        }
    };
    touchListener->onTouchMoved = [=] (cocos2d::Touch* touch, cocos2d::Event* event) {
        isTouchHold_ = false;
        isLongTouched_ = false;

        auto touchLocation = touch->getLocation();
        auto localLocation = touchableNode_->convertToNodeSpace(touchLocation);
        if (validTouchedRect.containsPoint(localLocation)) {
            isValidTouched_ = true;
        } else {
            isValidTouched_ = false;
        }
    };
    touchListener->onTouchEnded = [=] (cocos2d::Touch* touch, cocos2d::Event* event) {
        isTouchHold_ = false;

        auto touchLocation = touch->getLocation();
        auto localLocation = touchableNode_->convertToNodeSpace(touchLocation);
        if (validTouchedRect.containsPoint(localLocation)) {
            isValidTouched_ = true;
        } else {
            isValidTouched_ = false;
        }
    };
    touchListener->onTouchCancelled = touchListener->onTouchEnded;
    _eventDispatcher->addEventListenerWithSceneGraphPriority(touchListener, this);
}
```

完整代码详见：
[cocos2d-x-TouchableTableViewCell](https://github.com/yszheda/cocos2d-x-TouchableTableViewCell)
