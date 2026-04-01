from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Filter(Generic[T]):
    def __init__(self, func: Callable[[T], bool]):
        self.func = func

    def __call__(self, arg: T) -> bool:
        return self.func(arg)

    def __and__(self, other):
        return Filter(lambda m: self(m) and other(m))

    def __or__(self, other):
        return Filter(lambda m: self(m) or other(m))

    def __invert__(self):
        return Filter(lambda m: not self(m))
