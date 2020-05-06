---
layout: post
title: "cocos2d-x二维TableView/GridView的实现"
date: 2014-09-20 23:23
comments: true
published: true
categories: [cocos2d-x]
keywords: cocos2d-x, cocos, cocos2d, UI, widget, GridView, TableView, 2D, 游戏开发, 手游开发, game, mobile game, game devolopment
description: GridView in cocos2d-x
---
对于刚开始接触cocos2d-x的`TableView`的人来说，这个UI类看上去并非顾名思义的是个Table，而仅仅是个一维的List。
因为项目需要，我封装了一个`TableView`的子类来实现二维的功能。效果如下：

{% img /images/GridViewDemo/gridview.gif %}

具体代码详见：
[cocos2d-x-GridView](https://github.com/yszheda/cocos2d-x-GridView)

<!-- more -->

<!--
（有时间的话我会解释为何要设计成继承`TableView`和采用`TableView`实现2D效果的workaround为何不适合项目需求）
-->

`GridView`的使用与`TableView`基本相同，只不过多了两个接口：

- 固定行数：调用`setRowNum`

- 固定列数：调用`setColNum`


这还需要修改一下cocos2d-x的`TableView`类的声明，主要是声明一些member function为virtual：

```c++
class TableView : public ScrollView, public ScrollViewDelegate
{
public:
    
    enum class VerticalFillOrder
    {
        TOP_DOWN,
        BOTTOM_UP
    };
    
    /** Empty contructor of TableView */
    static TableView* create();
    
    /**
     * An intialized table view object
     *
     * @param dataSource data source
     * @param size view size
     * @return table view
     * @code
     * when this function bound to js or lua,the input params are changed
     * in js:var create(var jsObject,var size)
     * in lua:local create(var size)
     * in lua:
     * @endcode
     */
    static TableView* create(TableViewDataSource* dataSource, Size size);
    /**
     * An initialized table view object
     *
     * @param dataSource data source;
     * @param size view size
     * @param container parent object for cells
     * @return table view
     * @code
     * when this function bound to js or lua,the input params are changed
     * in js:var create(var jsObject,var size,var container)
     * in lua:local create(var size, var container)
     * in lua:
     * @endcode
     */
    static TableView* create(TableViewDataSource* dataSource, Size size, Node *container);
    /**
     * @js ctor
     */
    TableView();
    /**
     * @js NA
     * @lua NA
     */
    virtual ~TableView();

    virtual bool initWithViewSize(Size size, Node* container = NULL);

    /**
     * data source
     * @js NA
     * @lua NA
     */
    virtual TableViewDataSource* getDataSource() { return _dataSource; }
    /**
     * when this function bound to js or lua,the input params are changed
     * in js:var setDataSource(var jsSource)
     * in lua:local setDataSource()
     * @endcode
     */
    virtual void setDataSource(TableViewDataSource* source) { _dataSource = source; }
    /**
     * delegate
     * @js NA
     * @lua NA
     */
    virtual TableViewDelegate* getDelegate() { return _tableViewDelegate; }
    /**
     * @code
     * when this function bound to js or lua,the input params are changed
     * in js:var setDelegate(var jsDelegate)
     * in lua:local setDelegate()
     * @endcode
     */
    virtual void setDelegate(TableViewDelegate* pDelegate) { _tableViewDelegate = pDelegate; }

    /**
     * determines how cell is ordered and filled in the view.
     */
    virtual void setVerticalFillOrder(VerticalFillOrder order);
    virtual VerticalFillOrder getVerticalFillOrder();

    /**
     * Updates the content of the cell at a given index.
     *
     * @param idx index to find a cell
     */
    virtual void updateCellAtIndex(ssize_t idx);
    /**
     * Inserts a new cell at a given index
     *
     * @param idx location to insert
     */
    virtual void insertCellAtIndex(ssize_t idx);
    /**
     * Removes a cell at a given index
     *
     * @param idx index to find a cell
     */
    virtual void removeCellAtIndex(ssize_t idx);
    /**
     * reloads data from data source.  the view will be refreshed.
     */
    virtual void reloadData();
    /**
     * Dequeues a free cell if available. nil if not.
     *
     * @return free cell
     */
    virtual TableViewCell *dequeueCell();

    /**
     * Returns an existing cell at a given index. Returns nil if a cell is nonexistent at the moment of query.
     *
     * @param idx index
     * @return a cell at a given index
     */
    virtual TableViewCell *cellAtIndex(ssize_t idx);

    // Overrides
    virtual void scrollViewDidScroll(ScrollView* view) override;
    virtual void scrollViewDidZoom(ScrollView* view)  override {}
    virtual bool onTouchBegan(Touch *pTouch, Event *pEvent) override;
    virtual void onTouchMoved(Touch *pTouch, Event *pEvent) override;
    virtual void onTouchEnded(Touch *pTouch, Event *pEvent) override;
    virtual void onTouchCancelled(Touch *pTouch, Event *pEvent) override;

protected:
    virtual long __indexFromOffset(Vec2 offset);
    virtual long _indexFromOffset(Vec2 offset);
    virtual Vec2 __offsetFromIndex(ssize_t index);
    virtual Vec2 _offsetFromIndex(ssize_t index);

    virtual void _moveCellOutOfSight(TableViewCell *cell);
    virtual void _setIndexForCell(ssize_t index, TableViewCell *cell);
    virtual void _addCellIfNecessary(TableViewCell * cell);

    virtual void _updateCellPositions();


    TableViewCell *_touchedCell;
    /**
     * vertical direction of cell filling
     */
    VerticalFillOrder _vordering;

    /**
     * index set to query the indexes of the cells used.
     */
    std::set<ssize_t>* _indices;

    /**
     * vector with all cell positions
     */
    std::vector<float> _vCellsPositions;
    //NSMutableIndexSet *indices_;
    /**
     * cells that are currently in the table
     */
    Vector<TableViewCell*> _cellsUsed;
    /**
     * free list of cells
     */
    Vector<TableViewCell*> _cellsFreed;
    /**
     * weak link to the data source object
     */
    TableViewDataSource* _dataSource;
    /**
     * weak link to the delegate object
     */
    TableViewDelegate* _tableViewDelegate;

    Direction _oldDirection;

    bool _isUsedCellsDirty;

public:
    virtual void _updateContentSize();

};
```
