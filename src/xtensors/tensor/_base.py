from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, Sequence, Tuple, TypeVar, overload
from numpy.typing import ArrayLike, NDArray
import numpy as np

from .broadcast import vanilla_broadcaster, Broadcaster
from .typing import BinaryOperator, DimLike, DimsLike, TensorLike, Array

from ._decors import promote_binary_operator

from .basic_utils._base import to_xtensor
from .basic_utils._misc import strip

from ._slice import TensorIndexer



def inject_broadcast(broadcaster: Broadcaster):
    promote = promote_binary_operator(broadcaster)
    def wrapper(f: Callable[[XTensor], BinaryOperator[np.ndarray]]
        ):
        def wrapped(self: XTensor, other: TensorLike, /) -> XTensor:
            binop = promote(f(self))
            if isinstance(other, XTensor):
                return binop(self, other)
            try:
                return binop(self, to_xtensor(other))
            except TypeError:
                return NotImplemented
        return wrapped
    return wrapper


class XTensor:
    def __init__(self, data: Array,
        dims: Optional[Sequence[str|None]]=None,
        coords: Optional[Sequence[Sequence[Any]|NDArray[Any]|None]]=None,
            ) -> None:


        self.data = data.__array__()


        self._dim_axis_dict: Dict[str,int] = dict()

        self._dims: List[str|None]
        self._coords: List[NDArray[Any]|None]

        self.set_dims(dims)
        self.set_coords(coords)

    def viewcopy(self) -> XTensor:
        return XTensor(self.data, self.dims, self.coords)
    
    def item(self) -> float:
        return self.data.item()

    @property
    def dims(self) -> Tuple[str|None,...]:
        return tuple(self._dims)

    @property
    def coords(self) -> Tuple[NDArray[Any]|None,...]:
        return tuple(self._coords)

    @property
    def shape(self) -> Tuple[int,...]:
        return self.data.shape

    @property
    def rank(self) -> int:
        return len(self.data.shape)

    def get_axis(self, dim: DimLike) -> int:
        try:
            dim = dim.__get_dimname__() # type: ignore
        except AttributeError: pass

        if isinstance(dim, str): return self._dim_axis_dict[dim]
        if isinstance(dim, int):
            if dim < 0: dim = dim + self.rank
            if dim < 0 or dim >= self.rank: raise ValueError(f'Invalid axis: {dim}, rank={self.rank}')
            return dim
        
        try:
            assert isinstance(dim, tuple) 
            assert isinstance(dim[0], str)
            assert isinstance(dim[1], int)
            assert len(dim) == 2
        except AssertionError as e:
            raise ValueError('Dimlike should be int, str, or (str, int)') from e


        try:
            return self.get_axis(dim[0])
        except KeyError:
            return self.get_axis(dim[1])

    def get_axes(self, dims: DimLike|DimsLike|None) -> List[int]:
        if dims is None:
            return [i for i in range(self.rank)]
        try:
            dims = dims.__get_dimname__() # type: ignore
        except AttributeError: pass

        if isinstance(dims, (int, str, tuple)): return [self.get_axis(dims)]

        assert isinstance(dims, list)

        axes = [self.get_axis(dim) for dim in dims]
        assert len(axes) == len(set(axes))
        return axes
            
    def set_dims(self, dims: Sequence[str|None]|None) -> None:
        if dims is None:
            self._dims = [None for _ in self.data.shape]
        else:
            assert len(dims) == len(self.data.shape)
            assert '' not in dims
            _dims_without_none = [dim for dim in dims if dim is not None]
            assert len(_dims_without_none) == len(set(_dims_without_none))
            self._dims = list(dims)

            for axis, dim in enumerate(dims):
                if dim is not None:
                    self._dim_axis_dict[dim] = axis

    def set_dim(self, dim: DimLike, newdim: str|None) -> None:
        axis = self.get_axis(dim)
        new_dims = self._dims.copy()
        new_dims[axis] = newdim
        self.set_dims(new_dims)

    def get_coord(self, dim: DimLike) -> NDArray|None:
        axis = self.get_axis(dim)
        return self._coords[axis]

    def set_coords(self, coords: Sequence[Sequence[Any]|NDArray[Any]|None]|None) -> None:
        if coords is None:
            self._coords = [None for _ in self.data.shape]
        else:
            coords_clean: List[NDArray[Any]|None] = []
            assert len(coords) == len(self.data.shape)
            for axis, coord in enumerate(coords):
                if coord is not None:
                    assert len(coord) == self.data.shape[axis]
                    coords_clean.append(np.array(coords[axis]))
                else:
                    coords_clean.append(None)
            self._coords = coords_clean

    def set_coord(self, dim: DimLike, coord: Sequence[Any]|NDArray[Any]|None) -> None:
        axis = self.get_axis(dim)
        new_coords = self._coords.copy()
        if coord is None:
            new_coords[axis] = None
        else:
            new_coords[axis] = np.array(coord)
        self.set_coords(new_coords)


    def slc(self, dim: DimLike, slc: slice) -> XTensor:
        axis = self.get_axis(dim)

        slices: List[slice] = [slice(None, None, None)]*self.rank
        slices[axis] = slc

        data = self.data[tuple(slices)]
        coords = list(self.coords)
        
        coord = coords[axis]
        if coord is not None:
            coords[axis] = coord[slc]

        return XTensor(data, dims=self.dims, coords=coords)


    def get(self, dim: DimLike, index: int) -> XTensor:
        axis = self.get_axis(dim)
        
        slices: List[slice|int] = [slice(None, None, None)]*self.rank
        slices[axis] = index

        data = self.data[tuple(slices)]

        dims = strip(self.dims, [axis])
        coords = strip(self.coords, [axis])
        
        return XTensor(data, dims=dims, coords=coords)

    def __getitem__(self, slices: TensorIndexer|Tuple[TensorIndexer,...]) -> XTensor:

        if isinstance(slices, tuple):
            _Y = slices[0].index(self)
            if len(slices) == 1: 
                return _Y
            return _Y.__getitem__(tuple(slices[1:]))
        return slices.index(self)

    def __repr__(self):
        _repr = 'Tensor\n'
        _repr += f'shape={self.shape}\n'
        _repr += f'dims={self.dims}\n'

        _repr += f'coords:\n'
        for axis, coord in enumerate(self.coords):
            if coord is None:
                _repr += f'{axis}: None\n'
            if coord is not None:
                _repr += f'{axis}: {coord[0]}..{coord[-1]}\n'


        _repr += self.data.__repr__()

        return _repr

    def __neg__(self) -> XTensor:
        return XTensor(data=-self.data, dims=self._dims, coords=self._coords)

    @inject_broadcast(vanilla_broadcaster)
    def __add__(self): return lambda X, Y: X+Y

    @inject_broadcast(vanilla_broadcaster)
    def __radd__(self): return lambda X, Y: X+Y

    @inject_broadcast(vanilla_broadcaster)
    def __sub__(self): return lambda X, Y: X-Y

    @inject_broadcast(vanilla_broadcaster)
    def __rsub__(self): return lambda X, Y: Y-X

    @inject_broadcast(vanilla_broadcaster)
    def __mul__(self): return lambda X, Y: X*Y

    @inject_broadcast(vanilla_broadcaster)
    def __rmul__(self): return lambda X, Y: X*Y

    @inject_broadcast(vanilla_broadcaster)
    def __truediv__(self): return lambda X, Y: X/Y

    @inject_broadcast(vanilla_broadcaster)
    def __rtruediv__(self): return lambda X, Y: Y/X

    @inject_broadcast(vanilla_broadcaster)
    def __pow__(self): return lambda X, Y: X**Y

    @inject_broadcast(vanilla_broadcaster)
    def __rpow__(self): return lambda X, Y: Y**X

    @inject_broadcast(vanilla_broadcaster)
    def __eq__(self): return lambda X, Y: X==Y

    @inject_broadcast(vanilla_broadcaster)
    def __lt__(self): return lambda X, Y: X<Y

    @inject_broadcast(vanilla_broadcaster)
    def __gt__(self): return lambda X, Y: X>Y

    @inject_broadcast(vanilla_broadcaster)
    def __le__(self): return lambda X, Y: X<=Y

    @inject_broadcast(vanilla_broadcaster)
    def __ge__(self): return lambda X, Y: X>=Y

    def __array__(self): return self.data


