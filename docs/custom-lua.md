# Custom Lua Codec

`LuaCustomCodec` is for components that need a hand-written Lua communication layer.

Use it when the generated msgpack-lua descriptor path does not fit the component. In that case the framework cannot assume the generated chunking protocol, because the custom Lua decides what bytes are sent and received.

```python
from duui_py.codecs.lua_custom import LuaCustomCodec


def decode_request(body: bytes) -> MyRequest:
    ...


def encode_response(result: MyResponse) -> bytes:
    ...


def codec(self) -> LuaCustomCodec[MyRequest, MyResponse]:
    return LuaCustomCodec(
        communication_lua=LUA_SCRIPT,
        request_media_type="application/octet-stream",
        response_media_type="application/octet-stream",
        decode_request=decode_request,
        encode_response=encode_response,
    )
```

Custom Lua currently uses the synchronous adapter unless the custom codec also implements compatible stream methods.

```python
from duui_py.adapters import SynchronousRequestAdapter


app = create_app(MyAnnotator, request_adapter=SynchronousRequestAdapter())
```

Do not use custom Lua for the standard examples. Those should use `MsgPackLuaCodec` and `AsyncChunkedRequestAdapter`.
