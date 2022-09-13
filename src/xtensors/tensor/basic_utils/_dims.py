from __future__ import annotations
from typing import TYPE_CHECKING, List, Literal, Sequence
from ..typing import Dims

from ... import numpy as xtnp

from ._axes import permute

from ._generalize import generalize_1, generalize_2, generalize_3


if TYPE_CHECKING: from .._base import XTensor


def mergedims(X: XTensor|Dims, Y: XTensor|Dims) -> Dims:
    '''
    '''

    from .._base import XTensor

    if isinstance(X, XTensor): dims_x = list(X.dims)
    else: dims_x = X

    if isinstance(Y, XTensor): dims_y = list(Y.dims)
    else: dims_y = Y


    rank_x, rank_y = len(dims_x), len(dims_y)

    if rank_x < rank_y: return mergedims(Y, X)

    newdims = []

    dims_y = [None for _ in range(rank_y, rank_x)] + dims_y
    
    for dim_x, dim_y in zip(dims_x, dims_y):
        if dim_x is not None and dim_y is not None and dim_x != dim_y:
            raise ValueError(f'Incompatible dimensions: {dims_x} and {dims_y}')
        newdims.append(dim_x if dim_x is not None else dim_y)

    return newdims


def dimslast(X: XTensor, dims: Sequence[str]) -> XTensor:
    '''

    '''
    axes: List[int] = [X.get_axis(dim) for dim in dims]
    other_axes: List[int|None] = [axis for axis in range(X.rank) if axis not in axes]

    return permute(X, other_axes+axes)


def dimsfirst(X: XTensor, dims: Sequence[str]) -> XTensor:
    '''

    '''
    axes: List[int] = [X.get_axis(dim) for dim in dims]
    other_axes: List[int|None] = [axis for axis in range(X.rank) if axis not in axes]

    return permute(X, axes+other_axes)


def flatten(X: XTensor, dims: Sequence[str], dim_out: str|None, position: Literal['left', 'right']='right') -> XTensor:
    from .._base import XTensor
    x = X.data
    axes = [X.get_axis(dim) for dim in dims]

    remaining_dims = [dim for axis, dim in enumerate(X.dims ) if axis not in axes]
    remaining_coords = [coord for axis, coord in enumerate(X.coords) if axis not in axes]


    # TODO: implement coordinate meshgrid
    coord_out = None

    x_flat = xtnp.flatten(x, axes, position=position)

    if position == 'left':
        Y = XTensor(x_flat, [dim_out]+remaining_dims, [coord_out] + remaining_coords)
        return Y

    else:
        Y = XTensor(x_flat, remaining_dims+[dim_out], remaining_coords+[coord_out])
        return Y


@generalize_1
def name_dim_if_absent(X: XTensor, /, axis: int, dim: str, *, force: bool=False) -> XTensor:
    '''
    Ensure that X has a named dimension called [dim]. If not already, the
    dimension at [axis] will be named so.
    '''
    X1 = X.viewcopy()
    if dim in X.dims:
        return X1

    if X1.dims[axis] is not None and not force:
        raise ValueError(f'Tensor already has its dimension named {X1.dims[axis]} at axis={axis}')

    X1.set_dim(axis, dim)
    return X1




