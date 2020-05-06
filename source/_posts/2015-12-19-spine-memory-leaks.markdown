---
layout: post
title: "记一次spine内存泄露排查"
date: 2015-12-19 11:22
comments: true
published: true
categories: [cocos2d-x, CS, tech]
keywords: cocos2d-x, quick, quickx, quick-cocos2d-x, cocos, cocos2d, 游戏开发, 手游开发, mobile game, game devolopment
description: Spine Memory Leak
---

最近用`Instruments`的`Leaks`工具排查我们cocos2d-x游戏的一些内存泄露问题，大部分属于之前我们`C++`代码的bug，还有几个是`lua`代码中`sqlite`使用不当造成的内存泄露（例如数据库连接没有`close`，`prepare`的`stmt`没有`finalize`），总的来说这些都不难改。而且由于我们主要用的是`lua`，`lua`有垃圾回收，所以`Leaks`显示的内存泄露问题也不多。倒是spine的内存泄露问题相对棘手，花了我较长时间。

`Leaks`工具定位内存泄露到`spine`的`extension.c`中的`_malloc`函数：

```
static void* (*mallocFunc) (size_t size) = malloc;
static void* (*debugMallocFunc) (size_t size, const char* file, int line) = NULL;

void* _malloc (size_t size, const char* file, int line) {
	if(debugMallocFunc)
		return debugMallocFunc(size, file, line);

	return mallocFunc(size);
}
```

很显然，这是由分配的内存没有得到释放所引起的内存泄露。
接下来再找`spine`代码中分配内存和释放内存的地方，大部分都放在了不同结构体的`init`和`dispose`函数中，于是就重点关注这两个函数。可以发现在一些`dispose`函数中，部分指针并没有被`free`掉，那么是否可以把`free`加上呢？答案是不行，因为`spine`中这些指针其实只是浅拷贝，还有别的地方用到这些指针所指的内存地址，如果加上`free`会额外造成double free内存错误。

再继续考察spine分配内存和释放内存的代码，本渣发现，spine代码中用`C`结构体实现了vitrual table，从而模拟`C++`的多态，释放内存的函数类似`C++`的析构函数，也被模拟为虚函数。这块代码就成了本渣的重点怀疑对象，review下来还真发现有问题：spine调用“子类”的“析构函数”时，竟然是先调用“父类”的“析构函数”，然后在做自己的清理操作！而之所以先调用“父类”的“析构函数”不会有内存错误，是因为“父类”的“析构函数”并没有完全释放它所占用的内存，也就是说“父类”的对象在“析构”会泄露内存！

不废话，上代码。

下面是涉及到的宏定义：

```
/* All allocation uses these. */
#define MALLOC(TYPE,COUNT) ((TYPE*)_malloc(sizeof(TYPE) * (COUNT), __FILE__, __LINE__))
#define CALLOC(TYPE,COUNT) ((TYPE*)_calloc(COUNT, sizeof(TYPE), __FILE__, __LINE__))
#define NEW(TYPE) CALLOC(TYPE,1)

/* Gets the direct super class. Type safe. */
#define SUPER(VALUE) (&VALUE->super)

/* Cast to a super class. Not type safe, use with care. Prefer SUPER() where possible. */
#define SUPER_CAST(TYPE,VALUE) ((TYPE*)VALUE)

/* Cast to a sub class. Not type safe, use with care. */
#define SUB_CAST(TYPE,VALUE) ((TYPE*)VALUE)

/* Casts away const. Can be used as an lvalue. Not type safe, use with care. */
#define CONST_CAST(TYPE,VALUE) (*(TYPE*)&VALUE)

/* Gets the vtable for the specified type. Not type safe, use with care. */
#define VTABLE(TYPE,VALUE) ((_##TYPE##Vtable*)((TYPE*)VALUE)->vtable)
```

下面是`spTimeline`结构体，相当于基类：

```
typedef enum {
	SP_TIMELINE_SCALE,
	SP_TIMELINE_ROTATE,
	SP_TIMELINE_TRANSLATE,
	SP_TIMELINE_COLOR,
	SP_TIMELINE_ATTACHMENT,
	SP_TIMELINE_EVENT,
	SP_TIMELINE_DRAWORDER,
	SP_TIMELINE_FFD,
	SP_TIMELINE_IKCONSTRAINT,
	SP_TIMELINE_FLIPX,
	SP_TIMELINE_FLIPY
} spTimelineType;

struct spTimeline {
	const spTimelineType type;
	const void* const vtable;

#ifdef __cplusplus
	spTimeline() :
		type(SP_TIMELINE_SCALE),
		vtable(0) {
	}
#endif
};

void spTimeline_dispose (spTimeline* self);
void spTimeline_apply (const spTimeline* self, struct spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
		int* eventsCount, float alpha);
```

```
typedef struct _spTimelineVtable {
	void (*apply) (const spTimeline* self, spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
			int* eventsCount, float alpha);
	void (*dispose) (spTimeline* self);
} _spTimelineVtable;

void _spTimeline_init (spTimeline* self, spTimelineType type, /**/
void (*dispose) (spTimeline* self), /**/
		void (*apply) (const spTimeline* self, spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
				int* eventsCount, float alpha)) {
	CONST_CAST(spTimelineType, self->type) = type;
	CONST_CAST(_spTimelineVtable*, self->vtable) = NEW(_spTimelineVtable);
	VTABLE(spTimeline, self)->dispose = dispose;
	VTABLE(spTimeline, self)->apply = apply;
}

void _spTimeline_deinit (spTimeline* self) {
	FREE(self->vtable);
}


void spTimeline_dispose (spTimeline* self) {
	VTABLE(spTimeline, self)->dispose(self);
}


void spTimeline_apply (const spTimeline* self, spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
		int* eventsCount, float alpha) {
	VTABLE(spTimeline, self)->apply(self, skeleton, lastTime, time, firedEvents, eventsCount, alpha);
}

```

`spTimeline`结构体的子类`spCurveTimeline`：

```
typedef struct spCurveTimeline {
	spTimeline super;
	float* curves; /* type, x, y, ... */

#ifdef __cplusplus
	spCurveTimeline() :
		super(),
		curves(0) {
	}
#endif
} spCurveTimeline;

```

```
void (*dispose) (spTimeline* self), /**/
                void (*apply) (const spTimeline* self, spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
                                int* eventsCount, float alpha)) {
        _spTimeline_init(SUPER(self), type, dispose, apply);
        self->curves = CALLOC(float, (framesCount - 1) * BEZIER_SIZE);
}

void _spCurveTimeline_deinit (spCurveTimeline* self) {
        _spTimeline_deinit(SUPER(self));
        FREE(self->curves);
}
```

`spCurveTimeline`结构体的子类`spBaseTimeline`：

```
typedef struct spBaseTimeline {
        spCurveTimeline super;
        int const framesCount;
        float* const frames; /* time, angle, ... for rotate. time, x, y, ... for translate and scale. */
        int boneIndex;

#ifdef __cplusplus
        spBaseTimeline() :
                super(),
                framesCount(0),
                frames(0),
                boneIndex(0) {
        }
#endif
} spBaseTimeline;
```

```
void _spBaseTimeline_dispose (spTimeline* timeline) {
        struct spBaseTimeline* self = SUB_CAST(struct spBaseTimeline, timeline);
        _spCurveTimeline_deinit(SUPER(self));
        FREE(self->frames);
        FREE(self);
}

/* Many timelines have structure identical to struct spBaseTimeline and extend spCurveTimeline. **/
struct spBaseTimeline* _spBaseTimeline_create (int framesCount, spTimelineType type, int frameSize, /**/
                void (*apply) (const spTimeline* self, spSkeleton* skeleton, float lastTime, float time, spEvent** firedEvents,
                                int* eventsCount, float alpha)) {
        struct spBaseTimeline* self = NEW(struct spBaseTimeline);
        _spCurveTimeline_init(SUPER(self), type, framesCount, _spBaseTimeline_dispose, apply);

        CONST_CAST(int, self->framesCount) = framesCount * frameSize;
        CONST_CAST(float*, self->frames) = CALLOC(float, self->framesCount);

        return self;
}
```

`spTimeline`结构体的子类`spAttachmentTimeline`：

```
typedef struct spAttachmentTimeline {
        spTimeline super;
        int const framesCount;
        float* const frames; /* time, ... */
        int slotIndex;
        const char** const attachmentNames;

#ifdef __cplusplus
        spAttachmentTimeline() :
                super(),
                framesCount(0),
                frames(0),
                slotIndex(0),
                attachmentNames(0) {
        }
#endif
} spAttachmentTimeline;

spAttachmentTimeline* spAttachmentTimeline_create (int framesCount);
```

```
void _spAttachmentTimeline_dispose (spTimeline* timeline) {
        spAttachmentTimeline* self = SUB_CAST(spAttachmentTimeline, timeline);
        int i;

        _spTimeline_deinit(timeline);

        for (i = 0; i < self->framesCount; ++i)
                FREE(self->attachmentNames[i]);
        FREE(self->attachmentNames);
        FREE(self->frames);
        FREE(self);
}

spAttachmentTimeline* spAttachmentTimeline_create (int framesCount) {
        spAttachmentTimeline* self = NEW(spAttachmentTimeline);
        _spTimeline_init(SUPER(self), SP_TIMELINE_ATTACHMENT, _spAttachmentTimeline_dispose, _spAttachmentTimeline_apply);

        CONST_CAST(int, self->framesCount) = framesCount;
        CONST_CAST(float*, self->frames) = CALLOC(float, framesCount);
        CONST_CAST(char**, self->attachmentNames) = CALLOC(char*, framesCount);

        return self;
}
```

`spTimeline`结构体的子类`spEventTimeline`：

```
typedef struct spEventTimeline {
        spTimeline super;
        int const framesCount;
        float* const frames; /* time, ... */
        spEvent** const events;

#ifdef __cplusplus
        spEventTimeline() :
                super(),
                framesCount(0),
                frames(0),
                events(0) {
        }
#endif
} spEventTimeline;

spEventTimeline* spEventTimeline_create (int framesCount);
```

```
void _spEventTimeline_dispose (spTimeline* timeline) {
        spEventTimeline* self = SUB_CAST(spEventTimeline, timeline);
        int i;

        _spTimeline_deinit(timeline);

        for (i = 0; i < self->framesCount; ++i)
                spEvent_dispose(self->events[i]);
        FREE(self->events);
        FREE(self->frames);
        FREE(self);
}

spEventTimeline* spEventTimeline_create (int framesCount) {
        spEventTimeline* self = NEW(spEventTimeline);
        _spTimeline_init(SUPER(self), SP_TIMELINE_EVENT, _spEventTimeline_dispose, _spEventTimeline_apply);

        CONST_CAST(int, self->framesCount) = framesCount;
        CONST_CAST(float*, self->frames) = CALLOC(float, framesCount);
        CONST_CAST(spEvent**, self->events) = CALLOC(spEvent*, framesCount);

        return self;
}
```

`spTimeline`结构体的子类`spDrawOrderTimeline`：

```
typedef struct spDrawOrderTimeline {
        spTimeline super;
        int const framesCount;
        float* const frames; /* time, ... */
        const int** const drawOrders;
        int const slotsCount;

#ifdef __cplusplus
        spDrawOrderTimeline() :
                super(),
                framesCount(0),
                frames(0),
                drawOrders(0),
                slotsCount(0) {
        }
#endif
} spDrawOrderTimeline;

spDrawOrderTimeline* spDrawOrderTimeline_create (int framesCount, int slotsCount);
```

```
void _spDrawOrderTimeline_dispose (spTimeline* timeline) {
        spDrawOrderTimeline* self = SUB_CAST(spDrawOrderTimeline, timeline);
        int i;

        _spTimeline_deinit(timeline);

        for (i = 0; i < self->framesCount; ++i)
                FREE(self->drawOrders[i]);
        FREE(self->drawOrders);
        FREE(self->frames);
        FREE(self);
}

spDrawOrderTimeline* spDrawOrderTimeline_create (int framesCount, int slotsCount) {
        spDrawOrderTimeline* self = NEW(spDrawOrderTimeline);
        _spTimeline_init(SUPER(self), SP_TIMELINE_DRAWORDER, _spDrawOrderTimeline_dispose, _spDrawOrderTimeline_apply);

        CONST_CAST(int, self->framesCount) = framesCount;
        CONST_CAST(float*, self->frames) = CALLOC(float, framesCount);
        CONST_CAST(int**, self->drawOrders) = CALLOC(int*, framesCount);
        CONST_CAST(int, self->slotsCount) = slotsCount;

        return self;
}
```

`spCurveTimeline`结构体的子类`spFFDTimeline`：

```
typedef struct spFFDTimeline {
        spCurveTimeline super;
        int const framesCount;
        float* const frames; /* time, ... */
        int const frameVerticesCount;
        const float** const frameVertices;
        int slotIndex;
        spAttachment* attachment;

#ifdef __cplusplus
        spFFDTimeline() :
                super(),
                framesCount(0),
                frames(0),
                frameVerticesCount(0),
                frameVertices(0),
                slotIndex(0) {
        }
#endif
} spFFDTimeline;

spFFDTimeline* spFFDTimeline_create (int framesCount, int frameVerticesCount);
```

```
void _spFFDTimeline_dispose (spTimeline* timeline) {
        spFFDTimeline* self = SUB_CAST(spFFDTimeline, timeline);
        int i;

        _spCurveTimeline_deinit(SUPER(self));

        for (i = 0; i < self->framesCount; ++i)
                FREE(self->frameVertices[i]);
        FREE(self->frameVertices);
        FREE(self->frames);
        FREE(self);
}

spFFDTimeline* spFFDTimeline_create (int framesCount, int frameVerticesCount) {
        spFFDTimeline* self = NEW(spFFDTimeline);
        _spCurveTimeline_init(SUPER(self), SP_TIMELINE_FFD, framesCount, _spFFDTimeline_dispose, _spFFDTimeline_apply);
        CONST_CAST(int, self->framesCount) = framesCount;
        CONST_CAST(float*, self->frames) = CALLOC(float, self->framesCount);
        CONST_CAST(float**, self->frameVertices) = CALLOC(float*, framesCount);
        CONST_CAST(int, self->frameVerticesCount) = frameVerticesCount;
        return self;
}
```

如果按照正确的`C++`析构函数写法，应该这么改：

```
void _spTimeline_deinit (spTimeline* self) {
	FREE(self->vtable);
    FREE(self);
}



void _spCurveTimeline_deinit (spCurveTimeline* self) {
	FREE(self->curves);
	_spTimeline_deinit(SUPER(self));
}



void _spBaseTimeline_dispose (spTimeline* timeline) {
	struct spBaseTimeline* self = SUB_CAST(struct spBaseTimeline, timeline);
	FREE(self->frames);
	_spCurveTimeline_deinit(SUPER(self));
}


void _spFFDTimeline_dispose (spTimeline* timeline) {
	spFFDTimeline* self = SUB_CAST(spFFDTimeline, timeline);
	int i;

    for (i = 0; i < self->framesCount; ++i)
        FREE(self->frameVertices[i]);
    FREE(self->frameVertices);
    FREE(self->frames);

	_spCurveTimeline_deinit(SUPER(self));
}
```

正当本渣以为解决了问题的一部分时，`Leaks`查出来的内存泄露并没有减少。本渣再次trace了下代码，这才发现spine这套析构函数多态机制之所以没问题，是因为根本不会有基类对象！坑爹啊！！

本渣的下一个思路是把spine用到的结构体或类大小整理出来，和`Leaks`查出来的内存大小相比对，从而找到可疑的结构体，再相应去看它的实现代码。
不过查出的泄露内存大小并不固定，这给本渣排查带来了很多不便。
本渣在整理spine的结构体和类的同时也一点点地review代码，不知看了多久，最后总算在`SkeletonRenderer`的代码里捉到一处内存泄露bug：

```
void SkeletonRenderer::initialize () {
        _atlas = 0;
        _debugSlots = false;
        _debugBones = false;
        _timeScale = 1;

        _worldVertices = MALLOC(float, 1000); // Max number of vertices per mesh.

        _batch = PolygonBatch::createWithCapacity(2000); // Max number of vertices and triangles per batch.
        _batch->retain();

        _blendFunc = BlendFunc::ALPHA_PREMULTIPLIED;
        setOpacityModifyRGB(true);

        setGLProgram(ShaderCache::getInstance()->getGLProgram(GLProgram::SHADER_NAME_POSITION_TEXTURE_COLOR));
}

SkeletonRenderer::SkeletonRenderer () {
}

SkeletonRenderer::SkeletonRenderer (spSkeletonData *skeletonData, bool ownsSkeletonData) {
        initWithData(skeletonData, ownsSkeletonData);
}

SkeletonRenderer::SkeletonRenderer (const std::string& skeletonDataFile, spAtlas* atlas, float scale) {
        initWithFile(skeletonDataFile, atlas, scale);
}

SkeletonRenderer::SkeletonRenderer (const std::string& skeletonDataFile, const std::string& atlasFile, float scale) {
        initWithFile(skeletonDataFile, atlasFile, scale);
}

void SkeletonRenderer::initWithData (spSkeletonData* skeletonData, bool ownsSkeletonData) {
        setSkeletonData(skeletonData, ownsSkeletonData);

        initialize();
}

void SkeletonRenderer::initWithFile (const std::string& skeletonDataFile, spAtlas* atlas, float scale) {
        spSkeletonJson* json = spSkeletonJson_create(atlas);
        json->scale = scale;
        spSkeletonData* skeletonData = spSkeletonJson_readSkeletonDataFile(json, skeletonDataFile.c_str());
        CCASSERT(skeletonData, json->error ? json->error : "Error reading skeleton data.");
        spSkeletonJson_dispose(json);

        setSkeletonData(skeletonData, true);

        initialize();
}

void SkeletonRenderer::initWithFile (const std::string& skeletonDataFile, const std::string& atlasFile, float scale) {
        _atlas = spAtlas_createFromFile(atlasFile.c_str(), 0);
        CCASSERT(_atlas, "Error reading atlas file.");

        spSkeletonJson* json = spSkeletonJson_create(_atlas);
        json->scale = scale;
        spSkeletonData* skeletonData = spSkeletonJson_readSkeletonDataFile(json, skeletonDataFile.c_str());
        CCASSERT(skeletonData, json->error ? json->error : "Error reading skeleton data file.");
        spSkeletonJson_dispose(json);

        setSkeletonData(skeletonData, true);

        initialize();
}
```

注意，`SkeletonRenderer::initWithFile`里为成员变量`_atlas`申请了内存空间，随后调用`SkeletonRenderer::initialize`，竟重置了这一指针，却没有释放内存！话说spine这段代码的C++类构造函数写得也真是醉：既然调用完`initWithFile`后不需要访问`_atlas`，那干脆用一个临时变量就可以了，何必用成员变量；而且`initialize`函数的不少赋值操作放在构造函数的初始化列表里比较合适。不过简单一点改，就直接调整下函数调用次序就好：

```
SkeletonRenderer::SkeletonRenderer () {
    initialize();
}

SkeletonRenderer::SkeletonRenderer (spSkeletonData *skeletonData, bool ownsSkeletonData) {
    initialize();
    initWithData(skeletonData, ownsSkeletonData);
}

SkeletonRenderer::SkeletonRenderer (const std::string& skeletonDataFile, spAtlas* atlas, float scale) {
    initialize();
    initWithFile(skeletonDataFile, atlas, scale);
}

SkeletonRenderer::SkeletonRenderer (const std::string& skeletonDataFile, const std::string& atlasFile, float scale) {
    initialize();
    initWithFile(skeletonDataFile, atlasFile, scale);
}
void SkeletonRenderer::initWithData (spSkeletonData* skeletonData, bool ownsSkeletonData) {
        setSkeletonData(skeletonData, ownsSkeletonData);
}

void SkeletonRenderer::initWithFile (const std::string& skeletonDataFile, spAtlas* atlas, float scale) {
        spSkeletonJson* json = spSkeletonJson_create(atlas);
        json->scale = scale;
        spSkeletonData* skeletonData = spSkeletonJson_readSkeletonDataFile(json, skeletonDataFile.c_str());
        CCASSERT(skeletonData, json->error ? json->error : "Error reading skeleton data.");
        spSkeletonJson_dispose(json);

        setSkeletonData(skeletonData, true);
}

void SkeletonRenderer::initWithFile (const std::string& skeletonDataFile, const std::string& atlasFile, float scale) {
        _atlas = spAtlas_createFromFile(atlasFile.c_str(), 0);
        CCASSERT(_atlas, "Error reading atlas file.");

        spSkeletonJson* json = spSkeletonJson_create(_atlas);
        json->scale = scale;
        spSkeletonData* skeletonData = spSkeletonJson_readSkeletonDataFile(json, skeletonDataFile.c_str());
        CCASSERT(skeletonData, json->error ? json->error : "Error reading skeleton data file.");
        spSkeletonJson_dispose(json);

        setSkeletonData(skeletonData, true);
}
```

改完这个bug，再重新跑`Instruments`的`Leaks`工具，结果之前的内存泄露都没有了，看来`SkeletonRenderer`的这处bug就是被检测出来的所有spine内存泄露的罪魁祸首！

等到本渣兴高采烈想去提交一个PR时才发现，原来`spine`的repo上早有了fix该bug的[patch](https://github.com/EsotericSoftware/spine-runtimes/pull/461)，cocos2d-x也有相同的[patch](https://github.com/cocos2d/cocos2d-x/issues/13150)，看来还是要多跟进官方repo的进展啊......这次查bug真是白耗精力，而且看了些spine的烂坑对自己也木有帮助，不开森:(
