#include "lua_snapshot_extensions.h"

#if __cplusplus
extern "C" {
#endif
// snapshot
#include "lua-snapshot/snapshot.h"

static luaL_Reg luax_exts[] = {
    {"snapshot", luaopen_snapshot},
    {NULL, NULL}
};

void luaopen_lua_snapshot_extensions(lua_State *L)
{
    // load extensions
    luaL_Reg* lib = luax_exts;
    lua_getglobal(L, "package");
    lua_getfield(L, -1, "preload");
    for (; lib->func; lib++)
    {
        lua_pushcfunction(L, lib->func);
        lua_setfield(L, -2, lib->name);
    }
    lua_pop(L, 2);
}

#if __cplusplus
} // extern "C"
#endif
