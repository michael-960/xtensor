from __future__ import annotations
from typing import Any, Protocol, Sequence, Tuple, overload, cast
import numpy as np
from xarray import DataArray

from xtensors.typing import NDArray
from xtensors.typing import AxisDimPair, DimLike, DimsLike

from xtensors.unify import get_axes, strip_dims

from .. import tensor as xtt


'''
For reduction functions that can act over multiple axes/dims.
'''

class _np_reduction_func(Protocol):
    def __call__(self, a: np.ndarray, axis: int|Tuple[int,...]) -> np.ndarray: ...


class ReductionFunc(Protocol):
    def __call__(self, x: xtt.Array,/, dim: xtt.DimLike|xtt.DimsLike|None) -> xtt.XTensor: ...


def _reduction_factory(_np_func: _np_reduction_func) -> ReductionFunc:
    @xtt.generalize_1
    def _reduce(X: xtt.XTensor, /, dim: xtt.DimLike|xtt.DimsLike|None=None) -> xtt.XTensor:
        axes = X.get_axes(dim)
        _y = _np_func(X.data, axis=tuple(axes))

        return xtt.XTensor(_y, dims=xtt.strip(X.dims, axes), coords=xtt.strip(X.coords, axes))
    return _reduce


_sum = _reduction_factory(np.sum)
_mean = _reduction_factory(np.mean)
_std = _reduction_factory(np.std)

_nanmean = _reduction_factory(np.nanmean)
_nanstd = _reduction_factory(np.nanstd)
_nansum = _reduction_factory(np.nansum)

_max = _reduction_factory(np.max)
_min = _reduction_factory(np.min)

_nanmax = _reduction_factory(np.nanmax)
_nanmin = _reduction_factory(np.nanmin)

_all = _reduction_factory(np.all)
_any = _reduction_factory(np.any)


