from __future__ import annotations

from typing import Any, cast, Union
import numpy as np

from xarray import DataArray
from xtensors.typing import NDArray, number

from ._broadcast import broadcast_arrays


from .. import tensor as xtt
from scipy import special


def where(condition: NDArray, x: NDArray|number, y: NDArray|number) -> DataArray:
    '''
        The returned tensor is named only if condition is named
    '''
    dims = None

    X = cast(Union[NDArray,np.number], x)
    Y = cast(Union[NDArray,np.number], y)

    _c = condition.__array__()
    _x = X
    _y = Y

    if hasattr(x, 'shape'):
        _x = cast(NDArray, X.__array__())
        _c, _x, _, _ = broadcast_arrays(_c, _x)

    if hasattr(y, 'shape'):
        _y = cast(NDArray, Y.__array__())
        _c, _y, _, _ = broadcast_arrays(_c, _y)

    _z = np.where(_c, _x, _y)

    if isinstance(condition, DataArray): 
        dims = list(condition.dims)
        if len(_z.shape) > len(dims):
            dims = ['dim_i' for i in range(len(_z.shape)-len(dims))] + dims

    return DataArray(_z, dims=dims)


@xtt.generalize_1
def softmax(X: xtt.XTensor, /, dim: str) -> xtt.XTensor:
    axis = X.get_axis(dim)
    _y = special.softmax(X.data, axis=axis)
    return xtt.XTensor(_y, dims=X.dims, coords=X.coords)


def get_rank(x: Any) -> int:
    if hasattr(x, 'shape'):
        return len(x.shape)

    if hasattr(x, '__array__'):
        return get_rank(x.__array__())

    if isinstance(x, (list, tuple)):
        return get_rank(x[0]) + 1

    return 0


