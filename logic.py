from dataclasses import dataclass
from typing import Callable


Unary = Callable[[str],bool]
Binary = Callable[[str], Unary]
Quant = Callable[[Unary],Callable[[Unary], bool]]


@dataclass
class Expr:
    """General expression class, all others inherit from this. The value is the
       lambda statement itself to be executed, the later classes add the data to
       allow for the realization of string representations for derived expressions
       using substitution.
    """
    value: Unary | Binary | Quant


@dataclass
class Pred(Expr):
    """Class to represent predicates as a data structure."""
    name: str
    args: list[str]

    def __str__(self) -> str:
        return f"{self.name}.({', '.join(self.args)})"


@dataclass
class Bind(Expr):
    """Class to represent lambda statements and quantifiers."""
    name: str
    var: str
    body: Expr

    def __str__(self) -> str:
        return f"{self.name}{self.var}.{self.body}"


@dataclass
class Op(Expr):
    """Class to represent logical operators and, or, if, and negation."""
    name: str
    args: list[Expr]

    def __str__(self) -> str:
        arity = len(self.args)
        if arity == 1:
            return f"{self.name}{str(self.args[0])}"
        elif arity == 2:
            op = ' ' + self.name + ' '
            return f"{op.join([str(arg) for arg in self.args])}"
        else:
            raise Exception("ArityError: Invalid arity for predicate.")


class Model:

    def __init__(self) -> None:
        self.entities: set[str] = set()                         # x : e
        self.unaries: dict[str,set[str]] = dict()               # λx.P(x)
        self.binaries: dict[str, dict[str,set[str]]] = dict()   # λy.λx.R(x,y)

    def make_unary(self, name: str) -> Unary:
        # λx.P(x)
        return lambda x: x in self.unaries[name]

    def make_binary(self, name: str) -> Binary:
        # λy.λx.R(x,y)
        return lambda y: lambda x: y in self.binaries[name][x]

    def make_exists(self) -> Quant:
        # λP.λQ.∃x[P(x) & Q(x)]
        return lambda p: lambda q: any([p(x) and q(x) for x in self.entities])

    def make_forall(self) -> Quant:
        # λP.λQ.∀x[P(x) -> Q(x)]
        return lambda p: lambda q: all([not p(x) or q(x) for x in self.entities])

    def add_unary(self, name: str) -> Callable[[str], None]:
        return lambda x: self.unaries.setdefault(name, set()).add(x)

    def add_binary(self, name: str) -> Callable[[str], Callable[[str], None]]:
        return lambda y: lambda x: self.binaries.setdefault(name, dict()).setdefault(x, set()).add(y)
