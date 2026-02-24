from dataclasses import dataclass
from collections.abc import Callable
from typing import get_args

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
    var: Entity
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
            raise Exception("ArityError: Invalid arity for predicate.")


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


def subst_term(v: Entity,
               w: Entity,
               term: Entity) -> Entity:

    if v == term:
        return w
    else:
        return term


def alpha_conversion(v: Entity,
                     w: Entity,
                     expr: Expr) -> Expr:
    """Implementation of alpha-conversion (variable renaming)"""
    match expr:

        case Bind(name, var, expr):
            var = subst_term(v, w, var)
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


def subst_terms(v: Entity,
                w: Entity,
                expr: Expr) -> Expr:
    match expr:

        case Op(name, args):
            args = [subst_terms(v, w, expr) for expr in args]
            return Op(name, args)

        case Bind(name, var, expr):

            if var == w:
                expr = alpha_conversion(var, Var('v'), expr)
                expr = subst_terms(v, w, expr)
                expr = alpha_conversion(Var('v'), v, expr)
                return Bind(name, var, expr)
            else:
                var = subst_term(v, w, var)
                expr = subst_terms(v, w, expr)
                return Bind(name, var, expr)

        case Pred(name, args):
            args = [subst_term(v,
                               w,
                               term) for term in args]
            return Pred(name, args)

        case Entity():
            return subst_term(v, w, expr)

        case _:
            return expr


def subst_expr(v: Var, w: Expr, expr: Expr) -> Expr:

    match expr:

        case Bind(name, var, expr):
            expr = subst_expr(v, w, expr)
            return Bind(name, var, expr)

        case Pred(name, args):

            if v == name:

                match args:
                    case [arg]:
                        return beta_reduction((w, arg))
                    case [arg1, arg2]:
                        w_prime = beta_reduction((w, arg1))
                        return beta_reduction((w_prime, arg2))
                    case _:
                        raise Exception("Invalid arity for predicate in expression substitution.")
            else:
                return expr

        case Op(name, args):
            args = [subst_expr(v, w, expr) for expr in args]
            return Op(name, args)

        case Wff(expr):
            expr = subst_expr(v, w, expr)
            return Wff(expr)

        case Entity():
           if v == expr:
               return w
           else:
               return expr

        case _:
            return expr


def expr_type(expr: Expr):

    if isinstance(expr, Entity):
        return Entity
    
    elif isinstance(expr, Pred):
        return Truth

    elif isinstance(expr, Op):
        return Truth
                
    elif isinstance(expr, Bind):

        if expr.binder == LAMBDA:

            if isinstance(expr.var, Wff):
                return Entity

            if isinstance(expr.var, Var):
                if expr.var.name.islower():
                    return Callable[[Entity], expr_type(expr.expr)]
                else:
                    typ = Callable[[Entity], Truth]
                    return Callable[[typ], expr_type(expr.expr)]

            elif isinstance(expr.var, Const):
                if expr.var.name.islower():
                    return Callable[[Entity], expr_type(expr.expr)]
                else:
                    typ = Callable[[Entity], Truth]
                    return Callable[[typ], expr_type(expr.expr)]

        elif expr.binder == EXISTS:
            return Truth

        elif expr.binder == FORALL:
            return Truth


def beta_reduction(exprs: tuple[Expr, Expr]) -> Expr:

    match exprs:

        case Const(term), Bind('\\', Var(name), expr):
            if name.islower():
                return subst_terms(Var(name), Const(term), expr)
            else:
                raise Exception("AppError: Invalid types for function application.")

        case Bind('\\', Var(name), expr), Const(term):
            if name.islower():
                print('---')
                return subst_terms(Var(name), Const(term), expr)
            else:
                raise Exception("AppError: Invalid types for function application.")

        case Bind(binder='\\', var=Var(name1), expr=expr1), Bind(binder='\\', var=Var(name2), expr=expr2):
            if name1.isupper() and name2.islower() \
            or name1.islower() and name2.isupper():
                v = Var(name1)
                w = Bind('\\', Var(name2), expr2)
                return subst_expr(v, w, expr1)
            else:
                raise Exception(f"AppError: Invalid types for function application: {name1} and {name2}")

        case _:
                raise Exception("AppError: Invalid types for function application.")



class Model:

    def __init__(self) -> None:
        self.entities: set[Entity] = set()                                    # x : e
        self.unaries: dict[str, dict[Entity, bool]] = dict()                  # λx.P(x)
        self.binaries: dict[str, dict[Entity, dict[Entity, bool]]] = dict()   # λy.λx.R(x,y)

    def word2lf(self, cat: list[tuple[str,str]], lemma: str = ''):
        match cat:
            case [('sel', 'd'),('sel', 'd'),('cat', 'v')]:
                expr = build_binary(lemma)
                return expr

            case [('sel', 'j'),('sel', 'd'),('cat', 'v')]:
                var = Var('P')
                args: list[Entity] = []
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
                return None


if __name__ == "__main__":
    expr1 = build_quant('a')
    expr2 = build_unary('P')
    print(expr_type(expr1))
    print(expr_type(expr2))
    typ = expr_type(expr1)
    print(get_args(typ)[0][0])
