"""Allow-list unpickler for the ESSL pandas pickles (pandas 1.x format)."""
import pickle, functools, numpy as np, pandas as pd, importlib
ALLOWED = {
    ("pandas.core.frame", "DataFrame"), ("pandas.core.internals.managers", "BlockManager"),
    ("functools", "partial"), ("pandas.core.internals.blocks", "new_block"),
    ("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
    ("numpy", "ndarray"), ("numpy", "dtype"), ("builtins", "slice"),
    ("pandas.core.indexes.base", "_new_Index"), ("pandas.core.indexes.base", "Index"),
    ("pandas.core.indexes.range", "RangeIndex"), ("pandas.core.indexes.numeric", "Int64Index"),
}
class SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"blocked {module}.{name}")
        if (module, name) == ("pandas.core.indexes.numeric", "Int64Index"):
            return getattr(importlib.import_module(module), name)
        if module == "numpy.core.multiarray":
            module = "numpy._core.multiarray" if hasattr(np, "_core") else module
        return getattr(importlib.import_module(module), name)
def load(path):
    with open(path, "rb") as f:
        return SafeUnpickler(f).load()
