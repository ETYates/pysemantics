from typing import Union, Callable

class Model:

    def __init__(self) -> None:
        self.entites: set[str] = set()                          # x : e
        self.unaries: dict[str,set[str]] = dict()               # λx.P(x)
        self.binaries: dict[str, dict[str,set[str]]] = dict()   # λy.λx.R(x,y)

    def make_unary(self, name: str) -> Callable[[str], bool]:
        # λx.P(x)
        return lambda x: x in self.unaries[name]

    def make_binary(self, name: str) -> Callable[[str], Callable[[str], bool]]:
        # λy.λx.R(x,y)
        return lambda y: lambda x: y in self.binaries[name][x]

