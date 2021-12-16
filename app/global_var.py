import contextvars
import types

__global = contextvars.ContextVar("__global", default=types.SimpleNamespace())


# This is the only public API
def g():
    return __global.get()


G = g()
