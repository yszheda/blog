---
layout: post
title: "cocos2d-x V3.x内存管理分析"
date: 2014-07-30 22:13
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, cocos, cocos2d, 内存, 内存管理, memory management, 游戏开发, 手游开发, mobile game, game devolopment
description: Memory Management in cocos2d-x V3.x
---
cocos2d-x移植自Objective C的cocos2d，其内存管理其实也来自于OC。因而对于写过OC程序的朋友来讲，cocos2d-x的内存管理应该是一目了然的，但对于本渣这枚没接触过OC的C++码农来说，或许直接看cocos2d-x源代码才是最直接快捷的方式。

# Node类 #
我们首先来看_Node_类的代码，_Node_是cocos2d-x中极重要的基类，许多常用的_Scene_、_Layer_、_MenuItem_等都继承自Node。

<!-- more -->

Node的创建是通过以下的接口，该函数返回一个Node的静态对象指针：
```c++
    /**
     * Allocates and initializes a node.
     * @return A initialized node which is marked as "autorelease".
     */
    /**
     * 分配空间并初始化Node
     * 返回一个被初始化过且是autorelease的Node对象
     */
    static Node * create();
```

下面让我们来看这个函数的实现。该函数采用二段式创建的方式——首先用new operator在heap中开辟空间并进行简单的初始化，假如new返回一个合法地址（cocos2d-x没有采用c++的异常处理机制），则接着init函数用于实际初始化Node的成员。只有在这二者都成功后，才把创建的指针设为`autorelease`（关于`autorelease`后面会继续解释）并返回。
```c++
Node * Node::create()
{
	Node * ret = new Node();
    if (ret && ret->init())
    {
        ret->autorelease();
    }
    else
    {
        CC_SAFE_DELETE(ret);
    }
	return ret;
}
```
对于创建失败的情况，cocos2d-x使用了下面的宏保证该指针被delete且被设为nullptr：
```c++
#define CC_SAFE_DELETE(p)           do { delete (p); (p) = nullptr; } while(0)
```

这个二段式的create函数在cocos2d-x中非常常用，因而cocos2d-x用了以下一个叫`CREATE_FUNC`来表示这个函数以便给继承Node的子类使用：
```c++
/**
 * define a create function for a specific type, such as Layer
 * @param \__TYPE__  class type to add create(), such as Layer
 */
#define CREATE_FUNC(__TYPE__) \
static __TYPE__* create() \
{ \
    __TYPE__ *pRet = new __TYPE__(); \
    if (pRet && pRet->init()) \
    { \
        pRet->autorelease(); \
        return pRet; \
    } \
    else \
    { \
        delete pRet; \
        pRet = NULL; \
        return NULL; \
    } \
}
```
这样，继承Node的子类（例如`ExampleLayer`）只需要在类声明(class declaration)中加入`CREATE_FUNC(类名)`（例如`CREATE_FUNC(ExampleLayer)`），再override下init函数即可。

# Ref类 #
在cocos2d-x中，_Node_类的父类是_Ref_类，之前我们所看到的`autorelease`方法实际上就来自于这个父类。

下面我们先来看Ref类的声明，这里为了突出重点，我们忽略script binding的情况：
```c++
class CC_DLL Ref
{
public:
    /**
     * Retains the ownership.
     *
     * This increases the Ref's reference count.
     *
     * @see release, autorelease
     * @js NA
     */
    /**
     * 拿到所有权
     * 这会增加引用计数
     */
    void retain();

    /**
     * Releases the ownership immediately.
     *
     * This decrements the Ref's reference count.
     *
     * If the reference count reaches 0 after the descrement, this Ref is
     * destructed.
     *
     * @see retain, autorelease
     * @js NA
     */
    /**
     * 立即释放所有权
     * 这会减少引用计数
     * 如果更新后的引用计数为0，该Ref对象会被销毁
     */
    void release();

    /**
     * Releases the ownership sometime soon automatically.
     *
     * This descrements the Ref's reference count at the end of current
     * autorelease pool block.
     *
     * If the reference count reaches 0 after the descrement, this Ref is
     * destructed.
     *
     * @returns The Ref itself.
     *
     * @see AutoreleasePool, retain, release
     * @js NA
     * @lua NA
     */
    /**
     * 自动释放所有权
     * 这会减少引用计数
     *
     * This descrements the Ref's reference count at the end of current
     * autorelease pool block.
     * 如果更新后的引用计数为0，该Ref对象会被销毁
     * If the reference count reaches 0 after the descrement, this Ref is
     * destructed.
     */
    Ref* autorelease();

    /**
     * Returns the Ref's current reference count.
     *
     * @returns The Ref's reference count.
     * @js NA
     */
    /**
     * 返回该Ref对象的引用计数
     */
    unsigned int getReferenceCount() const;

protected:
    /**
     * Constructor
     *
     * The Ref's reference count is 1 after construction.
     * @js NA
     */
    /**
     * 构造函数
     * 初始引用计数为1
     */
    Ref();

public:
    /**
     * @js NA
     * @lua NA
     */
    virtual ~Ref();

protected:
    /**
	 * 采用引用计数(reference counting)
	 * _referenceCount就是计数值
     */
    // count of references
    unsigned int _referenceCount;

    friend class AutoreleasePool;

    // Memory leak diagnostic data (only included when CC_USE_MEM_LEAK_DETECTION is defined and its value isn't zero)
	// 以下函数用于开启内存泄露检测时打印出泄露信息
#if CC_USE_MEM_LEAK_DETECTION
public:
    static void printLeaks();
#endif
};
```
从上面的代码，我们可以初步了解到：Ref采用引用计数（reference counting）的方法来管理某个指针所指向的某个对象，初始创建时计数是1，当计数变为0时该对象被析构；`retain`方法会增加计数并拿到所有权，而与之对应的，`release`方法会减少计数；`autorelease`是把所有权交给友类（friend class）`AutoreleasePool`，让它来决定何时减少计数，这个类我们后面会继续谈到。

下面我们来看Ref类的实现（definition）：
```c++
#if CC_USE_MEM_LEAK_DETECTION
static void trackRef(Ref* ref);
static void untrackRef(Ref* ref);
#endif

// 在初始化列表中将计数设为1
Ref::Ref()
: _referenceCount(1) // when the Ref is created, the reference count of it is 1
{
// 假如开启内存泄露检测，则追踪该对象指针，将该对象指针放入一个列表（list）中
// 后面的代码我们很快就会看到这个list
#if CC_USE_MEM_LEAK_DETECTION
    trackRef(this);
#endif
}

Ref::~Ref()
{
// 假如开启内存泄露检测且引用计数非0，则在追踪列表中找到该对象指针并删除
#if CC_USE_MEM_LEAK_DETECTION
    if (_referenceCount != 0)
        untrackRef(this);
#endif
}

// retain只是单纯将计数递增
void Ref::retain()
{
	// CCASSERT是cocos2d-x对C++的assert所封装的宏
    CCASSERT(_referenceCount > 0, "reference count should greater than 0");
    ++_referenceCount;
}

void Ref::release()
{
	// 首先计数递减
    CCASSERT(_referenceCount > 0, "reference count should greater than 0");
    --_referenceCount;

	// 计数为0，应当析构对象
    if (_referenceCount == 0)
    {
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
		// 得到一个PoolManager单例的对象
		// PoolManager类后面会解释
        auto poolManager = PoolManager::getInstance();
		// 后面会详细解释这段代码
        if (!poolManager->getCurrentPool()->isClearing() && poolManager->isObjectInPools(this))
        {
			// 以下的注释很重要，很快会解释到
            // Trigger an assert if the reference count is 0 but the Ref is still in autorelease pool.
            // This happens when 'autorelease/release' were not used in pairs with 'new/retain'.
            //
            // Wrong usage (1):
            //
            // auto obj = Node::create();   // Ref = 1, but it's an autorelease Ref which means it was in the autorelease pool.
            // obj->autorelease();   // Wrong: If you wish to invoke autorelease several times, you should retain `obj` first.
            //
            // Wrong usage (2):
            //
            // auto obj = Node::create();
            // obj->release();   // Wrong: obj is an autorelease Ref, it will be released when clearing current pool.
            //
            // Correct usage (1):
            //
            // auto obj = Node::create();
            //                     |-   new Node();     // `new` is the pair of the `autorelease` of next line
            //                     |-   autorelease();  // The pair of `new Node`.
            //
            // obj->retain();
            // obj->autorelease();  // This `autorelease` is the pair of `retain` of previous line.
            //
            // Correct usage (2):
            //
            // auto obj = Node::create();
            // obj->retain();
            // obj->release();   // This `release` is the pair of `retain` of previous line.
            CCASSERT(false, "The reference shouldn't be 0 because it is still in autorelease pool.");
        }
#endif

// 假如开启内存泄露检测，则在追踪列表中找到该对象指针并删除
#if CC_USE_MEM_LEAK_DETECTION
        untrackRef(this);
#endif
		// 调用析构函数并释放空间
        delete this;
    }
}

// 把该对象指针交给友类AutoreleasePool（具体来说，是PoolManager单例对象所得到的当前的AutoreleasePool）来管理
Ref* Ref::autorelease()
{
    PoolManager::getInstance()->getCurrentPool()->addObject(this);
    return this;
}

unsigned int Ref::getReferenceCount() const
{
    return _referenceCount;
}

#if CC_USE_MEM_LEAK_DETECTION

// 这里便是存放所追踪的对象指针的列表
static std::list<Ref*> __refAllocationList;

void Ref::printLeaks()
{
    // Dump Ref object memory leaks
    if (__refAllocationList.empty())
    {
        log("[memory] All Ref objects successfully cleaned up (no leaks detected).\n");
    }
    else
    {
        log("[memory] WARNING: %d Ref objects still active in memory.\n", (int)__refAllocationList.size());

		// C++的range-for语法
		// 打印出每个泄露内存的对象指针的类型和引用计数
        for (const auto& ref : __refAllocationList)
        {
            CC_ASSERT(ref);
            const char* type = typeid(*ref).name();
            log("[memory] LEAK: Ref object '%s' still active with reference count %d.\n", (type ? type : ""), ref->getReferenceCount());
        }
    }
}

// 将对象指针放入列表中
static void trackRef(Ref* ref)
{
    CCASSERT(ref, "Invalid parameter, ref should not be null!");

    // Create memory allocation record.
    __refAllocationList.push_back(ref);
}

// 在列表中找到该对象指针并删除
static void untrackRef(Ref* ref)
{
    auto iter = std::find(__refAllocationList.begin(), __refAllocationList.end(), ref);
    if (iter == __refAllocationList.end())
    {
        log("[memory] CORRUPTION: Attempting to free (%s) with invalid ref tracking record.\n", typeid(*ref).name());
        return;
    }

    __refAllocationList.erase(iter);
}

#endif // #if CC_USE_MEM_LEAK_DETECTION
```
这段源代码对使用者最重要的在于release函数中的注释：

- 当Ref的计数变为0时，它一定不能在AutoreleasePool中。

- Ref的计数为0且同时在AutoreleasePool中的错误是由new/retain和autorelease/release没有对应引起的（有木有想起C++中new和delete没对应所引起的内存泄露？）：
	
	- autorelease缺乏对应的retain。
例如：
```c++
auto obj = Node::create();   // 注意create函数会调用autorelease方法，因此obj已经没有该指针的所有权了
obj->autorelease();   // obj没有所有权，因此无法再把所有权转交给AutoreleasePool，若要调用autorelease方法需要先调用retain拿到所有权
```

	- release缺乏对应的retain。
例如：
```c++
auto obj = Node::create();   // 注意create函数会调用autorelease方法，因此obj已经没有该指针的所有权了
obj->release();   // obj没有所有权，因此无法再控制计数（所有权在AutoreleasePool），若要调用release方法需要先调用retain拿到所有权
```

- 正确的用法是在create后调用autorelease或release方法前先用retain拿到所有权：
例如：
```c++
// 前面我们分析过create函数，它会先用new operator得到对象，再调用autorelease方法
// 这里new和autorelease对应
auto obj = Node::create();
                    |-   new Node();
                    |-   autorelease();

// 这里retain和autorelease对应，autorelease一个已经被autorelease过的对象（例如通过create函数构造的对象）必须先retain
obj->retain();
obj->autorelease();
```
又如：
```c++
auto obj = Node::create();
// 这里retain和release对应，release一个已经被autorelease过的对象（例如通过create函数构造的对象）必须先retain
obj->retain();
obj->release();
```

# AutoreleasePool类 #
现在我们来看Ref类的友类AutoreleasePool。
首先来看类声明：

```c++
class CC_DLL AutoreleasePool
{
public:
    /**
     * @warn Don't create an auto release pool in heap, create it in stack.
     * @js NA
     * @lua NA
     */
    /**
     * 警告：不要在heap上构造AutoreleasePool对象，要在stack上构造
     */
    AutoreleasePool();
    
    /**
     * Create an autorelease pool with specific name. This name is useful for debugging.
     */
    AutoreleasePool(const std::string &name);
    
    /**
     * @js NA
     * @lua NA
     */
    ~AutoreleasePool();

    /**
     * Add a given object to this pool.
     *
     * The same object may be added several times to the same pool; When the
     * pool is destructed, the object's Ref::release() method will be called
     * for each time it was added.
     *
     * @param object    The object to add to the pool.
     * @js NA
     * @lua NA
     */
    /**
     * 把指定的对象指针放到AutoreleasePool对象中
     * 注意：
     * 同一对象的指针可能会被多次加入到同一AutoreleasePool对象中；
     * 当该AutoreleasePool对象被析构时，该对象指针被加入多少次，就得调用多少次该对象的release()函数
     * 这是因为AutoreleasePool用vector而非set来存放所管理的对象指针，因此不会去重
     */
    void addObject(Ref *object);

    /**
     * Clear the autorelease pool.
     *
     * Ref::release() will be called for each time the managed object is
     * added to the pool.
     * @js NA
     * @lua NA
     */
    /**
     * 清空AutoreleasePool
     * 每个被管理的对象指针被加入多少次，就会调用多少次release()函数
     */
    void clear();
    
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
    /**
     * Whether the pool is doing `clear` operation.
     */
    bool isClearing() const { return _isClearing; };
#endif
    
    /**
     * Checks whether the pool contains the specified object.
     */
    /**
     * 检查AutoreleasePool对象是否管理某个对象指针
     */
    bool contains(Ref* object) const;

    /**
     * Dump the objects that are put into autorelease pool. It is used for debugging.
     *
     * The result will look like:
     * Object pointer address     object id     reference count
     *
     */
    void dump();
    
private:
    /**
     * The underlying array of object managed by the pool.
     *
     * Although Array retains the object once when an object is added, proper
     * Ref::release() is called outside the array to make sure that the pool
     * does not affect the managed object's reference count. So an object can
     * be destructed properly by calling Ref::release() even if the object
     * is in the pool.
     */
    /**
     * AutoreleasePool对象将它所管理的对象指针放到下面的vector中
	 * 尽管每次有对象指针加到该vector中时，该vector实际上retain拿到了所有权，
	 * 但是Ref::release()会被调用来保证AutoreleasePool不会改变它所管理的对象指针
	 * 的引用计数。
	 * 所以，当某个对象指针被放到AutoreleasePool类中管理时，仍然可以通过调用
	 * Ref::release()函数来析构它
     */
    std::vector<Ref*> _managedObjectArray;
    std::string _name;
    
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
    /**
     *  The flag for checking whether the pool is doing `clear` operation.
     */
    bool _isClearing;
#endif
};
```
从类声明中能解读出的最重要的信息是AutoreleasePool类用STL vector来存放它所管理的Ref所指向的对象。要搞清楚原理还需要继续看它的实现：

```c++
AutoreleasePool::AutoreleasePool()
: _name("")
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
, _isClearing(false)
#endif
{
    _managedObjectArray.reserve(150);
    // 每个新创建的AutoreleasePool对象都交由PoolManager单例对象统一管理
    PoolManager::getInstance()->push(this);
}

AutoreleasePool::AutoreleasePool(const std::string &name)
: _name(name)
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
, _isClearing(false)
#endif
{
    _managedObjectArray.reserve(150);
    // 每个新创建的AutoreleasePool对象都交由PoolManager单例对象统一管理
    PoolManager::getInstance()->push(this);
}

AutoreleasePool::~AutoreleasePool()
{
    CCLOGINFO("deallocing AutoreleasePool: %p", this);
	// 清空该AutoreleasePool
    clear();
    
    // 要析构的AutoreleasePool对象不再由PoolManager管理
    PoolManager::getInstance()->pop();
}

// 只是单纯调用vector::push_back加入所管理的对象
void AutoreleasePool::addObject(Ref* object)
{
    _managedObjectArray.push_back(object);
}

// clear函数就是AutoreleasePool调用release来管理对象的引用计数的地方
void AutoreleasePool::clear()
{
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
    _isClearing = true;
#endif
	// 调用每个在AutoreleasePool的对象指针的release方法
    for (const auto &obj : _managedObjectArray)
    {
        obj->release();
    }
	// 清空存放管理对象的vector
    _managedObjectArray.clear();
#if defined(COCOS2D_DEBUG) && (COCOS2D_DEBUG > 0)
    _isClearing = false;
#endif
}

// 线性搜索所管理的对象指针的vector，查看所指定的Ref指针是否存在
bool AutoreleasePool::contains(Ref* object) const
{
    for (const auto& obj : _managedObjectArray)
    {
        if (obj == object)
            return true;
    }
    return false;
}

void AutoreleasePool::dump()
{
    CCLOG("autorelease pool: %s, number of managed object %d\n", _name.c_str(), static_cast<int>(_managedObjectArray.size()));
    CCLOG("%20s%20s%20s", "Object pointer", "Object id", "reference count");
    for (const auto &obj : _managedObjectArray)
    {
        CC_UNUSED_PARAM(obj);
        CCLOG("%20p%20u\n", obj, obj->getReferenceCount());
    }
}
```

# PoolManager类 #
下面我们来看PoolManager类，在cocos2d-x中，这个类是典型的单例（singleton）工厂类——及有且只有一个PoolManager对象，该PoolManger有一个存放AutoreleasePool对象指针的stack，该stack是由STL::vector实现的。需要注意的是，cocos2d-x的单例类都不是线程安全的，跟内存管理紧密相关的PoolManager类也不例外，因此在多线程中使用cocos2d-x的接口需要特别注意内存管理的问题。

我们先来看类声明：
```c++
class CC_DLL PoolManager
{
public:
    /**
     * @js NA
     * @lua NA
     */
    CC_DEPRECATED_ATTRIBUTE static PoolManager* sharedPoolManager() { return getInstance(); }
    static PoolManager* getInstance();
    
    /**
     * @js NA
     * @lua NA
     */
    CC_DEPRECATED_ATTRIBUTE static void purgePoolManager() { destroyInstance(); }
    static void destroyInstance();
    
    /**
     * Get current auto release pool, there is at least one auto release pool that created by engine.
     * You can create your own auto release pool at demand, which will be put into auto releae pool stack.
     */
    AutoreleasePool *getCurrentPool() const;

    bool isObjectInPools(Ref* obj) const;

    /**
     * @js NA
     * @lua NA
     */
    friend class AutoreleasePool;
    
private:
	// singleton类把构造函数和析构函数设为private，避免被调用
    PoolManager();
    ~PoolManager();
    
    void push(AutoreleasePool *pool);
    void pop();
    
    static PoolManager* s_singleInstance;
    
	// 同样用vector来存放所管理AutoreleasePool对象指针的列表
    std::vector<AutoreleasePool*> _releasePoolStack;
};
```

再来看类实现：
```c++
PoolManager* PoolManager::s_singleInstance = nullptr;

PoolManager* PoolManager::getInstance()
{
    if (s_singleInstance == nullptr)
    {
        s_singleInstance = new PoolManager();
        // Add the first auto release pool
        new AutoreleasePool("cocos2d autorelease pool");
    }
    return s_singleInstance;
}

void PoolManager::destroyInstance()
{
    delete s_singleInstance;
    s_singleInstance = nullptr;
}

PoolManager::PoolManager()
{
    _releasePoolStack.reserve(10);
}

PoolManager::~PoolManager()
{
    CCLOGINFO("deallocing PoolManager: %p", this);
    
	// 逐个析构所管理的AutoreleasePool对象
    while (!_releasePoolStack.empty())
    {
        AutoreleasePool* pool = _releasePoolStack.back();
        
        delete pool;
    }
}

// 加入AutoreleasePool对象指针时用的是stl::vector的push_back函数，
// 于是调用back函数就可以得到最新被加入的AutoreleasePool对象指针
AutoreleasePool* PoolManager::getCurrentPool() const
{
    return _releasePoolStack.back();
}

// 线性搜索每个被管理的AutoreleasePool，
// 每个AutoreleasePool对象再用contains函数线性搜索一遍
bool PoolManager::isObjectInPools(Ref* obj) const
{
    for (const auto& pool : _releasePoolStack)
    {
        if (pool->contains(obj))
            return true;
    }
    return false;
}

void PoolManager::push(AutoreleasePool *pool)
{
    _releasePoolStack.push_back(pool);
}

void PoolManager::pop()
{
    CC_ASSERT(!_releasePoolStack.empty());
    _releasePoolStack.pop_back();
}
```

# 最后的疑问 #
想必各位用惯了c++的看官在看完了以上的代码之后，最有疑问的还是神秘的`Ref::autorelease`函数。我们从AutoreleasePool的源代码看到，事实上被autorelease的对象最后还是通过release函数来减少其引用计数的，只不过release函数不是由使用者来调用，而是AutoreleasePool来调用，调用的地方在`AutoreleasePool::clear()`函数。那么AutoreleasePool如何个「auto」自动管理内存法儿？`AutoreleasePool::clear()`会在哪个地方被调用？

谜底隐藏在`cocos/base/CCDirector.cpp`中：
```
void DisplayLinkDirector::mainLoop()
{
    if (_purgeDirectorInNextLoop)
    {
        _purgeDirectorInNextLoop = false;
        purgeDirector();
    }
    else if (! _invalid)
    {
        drawScene();
     
        // release the objects
        PoolManager::getInstance()->getCurrentPool()->clear();
    }
}
```

这里就不纠缠Director类的实现细节了，上面的代码揭示的事实是：在图像渲染的主循环中，如果当前的图形对象是在当前帧，则调用显示函数，并调用`AutoreleasePool::clear()`减少这些对象的引用计数。mainLoop是每一帧都会自动调用的，所以下一帧时这些对象都被当前的AutoreleasePool对象release了一次。这也是AutoreleasePool「自动」的来由。
