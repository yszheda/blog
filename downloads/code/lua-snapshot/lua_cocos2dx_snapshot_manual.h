#ifndef __COCOS_SCRIPTING_LUA_BINDINGS_MANUAL_SNAPSHOT_LUA_COCOS2DX_SNAPSHOT_MANUAL_H__
#define __COCOS_SCRIPTING_LUA_BINDINGS_MANUAL_SNAPSHOT_LUA_COCOS2DX_SNAPSHOT_MANUAL_H__

#ifdef __cplusplus
extern "C" {
#endif
#include "tolua++.h"
#ifdef __cplusplus
}
#endif

TOLUA_API int register_snapshot_module(lua_State* L);

#endif //#ifndef __COCOS_SCRIPTING_LUA_BINDINGS_MANUAL_SNAPSHOT_LUA_COCOS2DX_SNAPSHOT_MANUAL_H__
