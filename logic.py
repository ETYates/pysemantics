from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

Truth = bool | None

LAMBDA = '\\'
EXISTS = '#'
FORALL = '@'
IOTA = '~'
IFTHEN = '->'
AND = '&'
OR = '|'
NOT = '!'

@dataclass
class Expr:
    """General expression class, all others inherit from this. The value is the
       lambda statement itself to be executed, the later classes add the data to
       allow for the realization of string representations for derived expressions
       using substitution.
    """
    ...

@dataclass
class Entity(Expr):
    ...


@dataclass
class Const(Entity):
    name: str

    def __str__(self):
        return self.name


@dataclass
class Var(Entity):
    name: str

    def __str__(self):
        return self.name


@dataclass
class Wff(Entity):
    expr: Expr

    def __str__(self):
        return str(self.expr)



@dataclass
class Pred(Expr):
    """Class to represent predicates as a data structure."""
    term: Entity
    args: list[Entity]

    def __str__(self) -> str:
        if self.args:
          return f"{self.term}({', '.join([str(arg) for arg in self.args])})"
        else:
          return f"{self.term}"


@dataclass
class Bind(Expr):
    """Class to represent lambda statements and quantifiers."""
    binder: str
    var: Var
    expr: Expr

    def __str__(self) -> str:
        if isinstance(self.expr, Op):
            return f"{self.binder}{self.var}[{self.expr}]"
        else:
            return f"{self.binder}{self.var}.{self.expr}"


@dataclass
class Op(Expr):
    """Class to represent logical operators and, or, if, and negation."""
    rator: str
    args: list[Expr]

    def __str__(self) -> str:
        arity = len(self.args)

        if arity == 1:
            return f"{self.rator}{self.args[0]}"

        elif arity == 2:
            rator = f" {self.rator} "
            return f"{rator.join([str(arg) for arg in self.args])}"

        else:
            raise Exception(f"ArityError: Invalid arity for predicate: {len(self.args)}.")

@dataclass
class Epsilon(Expr):

    def __str__(self) -> str:
        return "null"


class Node:
    data: Expr | tuple[Any, Any]

    def __init__(self, data):
        self.data = data

    def __str__(self):
        match self.data:
            case (t, u):
                return f"[{t}, {u}]"
            case _:
                return str(self.data)

Unary = Callable[[Entity], Truth]


class Model:

    def __init__(self) -> None:
        self.entities: set[Entity] = set()                                    # x : e
        self.unaries: dict[str, dict[Entity, bool]] = dict()                  # λx.P(x)
        self.binaries: dict[str, dict[Entity, dict[Entity, bool]]] = dict()   # λy.λx.R(x,y)


def build_unary(lemma: str) -> Expr:

    term: Entity = Const(lemma)
    var = Var('x')
    args: list[Entity] = [var]

    expr: Expr = Pred(term, args)
    name = LAMBDA
    expr = Bind(name, var, expr)
    return expr


def build_binary(lemma: str) -> Expr:

    term: Entity = Const(lemma)


    x, y = Var('x'), Var('y')
    args: list[Entity] = [x, y]
    expr: Expr = Pred(term, args)

    name = LAMBDA
    expr = Bind(name, x, expr)
    expr = Bind(name, y, expr)
    return expr


def build_quant(lemma: str) -> Expr:

    var: Entity = Var('x')
    p: Entity = Var('P')

    q: Entity = Var('Q')

    if lemma == 'every':
        binder = FORALL
        rator  = IFTHEN

    elif lemma == 'a':
        binder = EXISTS
        rator  = AND

    elif lemma == 'an':
        binder = EXISTS
        rator = EXISTS

    else:
        raise Exception(f"Current determiner {lemma} is unimplemented.")

    expr1: Expr = Pred(term=p, args=[var])
    expr2: Expr = Pred(term=q, args=[var])
    args: list[Expr] = [expr1, expr2]
    expr: Expr = Op(rator, args)

    expr = Bind(binder=binder, var=var, expr=expr)
    expr = Bind(binder=LAMBDA, var=q, expr=expr)
    expr = Bind(binder=LAMBDA, var=p, expr=expr)

    return expr


def subst_term(v: Var,
               w: Entity,
               term: Entity) -> Entity:

    if v == term:
        return w
    else:
        return term

def subst_var(v: Var,
              w: Var,
              var: Var) -> Var:

    if v == var:
        return w
    else:
        return var

def alpha_conversion(v: Var,
                     w: Var,
                     expr: Expr) -> Expr:
    """Implementation of alpha-conversion (variable renaming)"""
    match expr:

        case Bind(name, var, expr):
            var = subst_var(v, w, var)
            expr = alpha_conversion(v, w, expr)
            return Bind(name, var, expr)

        case Op(name, args):
            args = [alpha_conversion(v, w, arg) for arg in args]
            return Op(name, args)

        case Pred(name, args):
            args = [subst_term(v, w, arg) for arg in args]
            return Pred(name, args)

        case _:
            return expr


def reduce_bind(v: Var, expr: Expr) -> Expr:

    if isinstance(expr, Bind):
        binder: str = expr.binder
        w: Var = expr.var
        new_expr: Expr = expr.expr

        if binder == LAMBDA:
            if v == w:
                return new_expr
            else:
                new_expr = reduce_bind(v, new_expr)
                return new_expr
        else:
            new_expr = reduce_bind(v, new_expr)
            new_expr = Bind(binder, w, new_expr)
            return new_expr

    elif isinstance(expr, Op):
        rator = expr.rator
        args = expr.args
        args = [reduce_bind(v, expr) for expr in args]
        expr = Op(rator, args)
        return expr

    else:
        return expr

def free_vars(expr: Expr) -> list[Var]:
    
    vs: list[Var] = []

    if isinstance(expr, Bind):

        if expr.binder == LAMBDA:
            var = expr.var
            expr = expr.expr

            vs.append(var)
            vs.extend(free_vars(expr))
            return vs

        else:
            expr = expr.expr
            vs.extend(free_vars(expr))
            return vs

    elif isinstance(expr, Op):

        args = expr.args

        for arg in args:
            new_vs = free_vars(arg)
            vs.extend(new_vs)

        return vs

    return vs


def lift_binds(expr: Expr) -> Expr:
    vs = free_vars(expr)

    for var in vs:
        expr = reduce_bind(var, expr)
        expr = Bind(LAMBDA, var, expr)

    return expr
        

def substitute(v: Var, w: Expr, expr: Expr) -> Expr:

    match expr:

        case Bind(name, var, expr):

            if var == w:
                tmp = Var('v')
                expr = alpha_conversion(var, tmp, expr)
                expr = substitute(v, w, expr)
                expr = alpha_conversion(tmp, v, expr)
                expr = Bind(name, v, expr)
                return expr

            else:
                expr = substitute(v, w, expr)
                expr = Bind(name, var, expr)
                return expr

        case Pred(term, args):

            if v == term:
                while args:
                    arg = args.pop(0)
                    w = beta_reduction((w, arg))
                return w

            else:
                if isinstance(w, Entity):
                    args = [subst_term(v, w, arg) for arg in args]
                    expr = Pred(term, args)
                    return expr
                else:
                    return expr

        case Op(name, args):
            args = [substitute(v, w, expr) for expr in args]
            expr = Op(name, args)
            return expr

        case Var():
            if v == expr:
                return w
            else:
                return expr

        case _:
            return expr


def beta_reduction(exprs: tuple[Expr, Expr]) -> Expr:

    match exprs:

        case Const(term), Bind(binder=LAMBDA, var=Var(name), expr=expr):

            if name.islower():
                v = Var(name)
                w = Const(term)
                expr = substitute(v, w, expr)
                expr = lift_binds(expr)
                return expr

            raise Exception("AppError: failed beta_reduction")

        case Bind(binder=LAMBDA, var=Var(name), expr=expr), Const(term):

            if name.islower():
                v = Var(name)
                w = Const(term)
                expr = substitute(v, w, expr)
                expr = lift_binds(expr)
                return expr

            raise Exception("AppError: failed beta_reduction")

        case Var(term), Bind(binder=LAMBDA, var=Var(name), expr=expr):

            if name.islower():
                v = Var(name)
                w = Var(term)
                expr = substitute(v, w, expr)
                expr = lift_binds(expr)
                return expr

            raise Exception("AppError: failed beta_reduction")

        case Bind(binder=LAMBDA, var=Var(name), expr=expr), Var(term):

            if name.islower():
                v = Var(name)
                w = Var(term)
                expr = substitute(v, w, expr)
                expr = lift_binds(expr)
                return expr

            raise Exception("AppError: failed beta_reduction")

        case Bind(binder='\\', var=Var(name1), expr=expr1), Bind(binder='\\', var=Var(name2), expr=expr2):

            if name1.isupper() and name2.islower():
                binder = '\\'
                var = Var(name2)
                expr = expr2

                v = Var(name1)
                w = Bind(binder, var, expr)
                expr = substitute(v, w, expr1)
                expr = lift_binds(expr)

                return expr

            elif name1.islower() and name2.isupper():
                binder = '\\'
                var = Var(name1)
                expr = expr1

                v = Var(name2)
                w = Bind(binder, var, expr)
                expr = substitute(v, w, expr2)
                expr = lift_binds(expr)

                return expr

            raise Exception(f"AppError: Invalid types for function application: {name1} and {name2}")
        
        case expr1, expr2:

            if isinstance(expr1, Epsilon):
                return expr2

            elif isinstance(expr2, Epsilon):
                return expr1

            raise Exception(f"AppError: Invalid types for function application: {expr1} and {expr2}.")


class Translator:

    def word2lf(self, cat: list[tuple[str,str]], lemma: str = '') -> Expr:
        """
        Convert a lemma and category entry to a logical form.
        
        args:
            cat   -- the selectors and base cats for a lexical entry
            lemma -- the dictionary form of a lexical entry

        return:
            expr -- logical form in a higher order logical lambda calculus
                    expression
        """
        match cat:
            case [('sel', 'd'),('sel', 'd'),('cat', 'v')]:
                expr = build_binary(lemma)
                return expr

            case [('sel', 'j'),('sel', 'd'),('cat', 'v')]:
                var = Var('P')
                args = []
                name = LAMBDA
                expr = Pred(term=var, args=args)
                expr = Bind(name, var, expr)
                return expr

            case [('sel', 'd'),('cat', 'v')]:
                expr = build_unary(lemma)
                return expr

            case [('cat', 'd'), *_]:
                expr = Const(lemma)
                return expr

            case [('cat', 'n'), *_]:
                expr = build_unary(lemma)
                return expr

            case [('cat', 'j')]:
                expr = build_unary(lemma)
                return expr

            case [('sel', 'n'), ('cat', 'j')]:
                p = Var('P')
                x = Var('x')

                expr1 = Pred(term=Const(lemma), args=[x])
                expr2 = Pred(term=p, args=[x])

                rator = AND
                expr = Op(rator, args=[expr1, expr2])
                expr = Bind(binder=LAMBDA, var=x, expr=expr)
                expr = Bind(binder=LAMBDA, var=p, expr=expr)
                return expr

            case [('sel', 'n'),('cat', 'd'), *_]:
                expr = build_quant(lemma)
                return expr

            case [('sel', 'j'),('cat', 'd'), *_]:
                expr = build_quant(lemma)
                return expr

            case _:
                raise Exception("LF for lexical item is unimplemented.")

    def translate(self, derivation_tree: list | tuple) -> Node:
        """
        Converts a derivation-tree into a tree of lambda applications.

        args: 
            derivation_tree -- tree (in list data structure) of lexical items.
                               This is the output of the parser

        returns:
            node -- converted tree data structure
            """

        match derivation_tree:
            case ([entry], cat):
                _, lemma = entry.split(':')
                data = self.word2lf(cat, lemma.strip())
                node = Node(data)
                return node

            case ([], cat):
                data = Epsilon()
                node = Node(data)
                return node

            case ['*', dt1, dt2]:
                node1 = self.translate(dt1)
                node2 = self.translate(dt2)
                data = (node1,node2)
                node = Node(data)
                return node

            case ['o', dt]:
                node = self.translate(dt)
                return node

            case _:
                raise Exception(f"Invalid format for output list-derivation tree: {derivation_tree}")

    def simplify(self, node: Node) -> Expr:
        
        data = node.data
        
        if isinstance(data, Expr):
            expr = data
            return expr

        else:
            n1, n2 = data

            expr1 = self.simplify(n1)
            expr2 = self.simplify(n2)
            
            expr = beta_reduction((expr1,expr2))
            return expr


if __name__ == "__main__":
    q = build_quant('a')
    g = build_binary('g')
    f = build_unary('f')
    a = Const('a')
    expr = beta_reduction((q,f))
    expr = beta_reduction((g,expr))
    print(expr)
    print(free_vars(expr))
    expr = beta_reduction((expr,a))
    print(expr)
