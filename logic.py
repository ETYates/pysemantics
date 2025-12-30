from dataclasses import dataclass
from typing import Callable, Any


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
    ...

@dataclass
class Entity:
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
        return str(expr)


@dataclass
class Term(Expr):
    term: Entity

    def __str__(self):
        match term:
            case Const(name):
                return name
            case Var(name):
                return name
            case Wff(expr):
                return str(expr)


@dataclass
class Pred(Expr):
    """Class to represent predicates as a data structure."""
    name: Entity
    args: list[Entity]

    def __str__(self) -> str:
        if self.args:
          return f"{self.name}({', '.join([str(arg) for arg in self.args])})"
        else:
          return f"{self.name}"


@dataclass
class Bind(Expr):
    """Class to represent lambda statements and quantifiers."""
    name: str
    var: Var
    expr: Expr

    def __str__(self) -> str:
        if isinstance(self.expr, Op):
            return f"{self.name}{self.var}[{self.expr}]"
        else:
            return f"{self.name}{self.var}.{self.expr}"


@dataclass
class Op(Expr):
    """Class to represent logical operators and, or, if, and negation."""
    name: str
    args: list[Expr]

    def __str__(self) -> str:
        arity = len(self.args)

        if arity == 1:
            return f"{self.name}{self.args[0]}"

        elif arity == 2:
            op = f" {self.name} "
            return f"{op.join([str(arg) for arg in self.args])}"

        else:
            raise Exception("ArityError: Invalid arity for predicate.")

def build_predicate(name: str, arity: int = 1) -> Expr:
    if arity == 1:
        pred = Pred(Const(name), [Var('x')])
        return Bind('\\', Var('x'), pred)
    elif arity == 2:
        pred = Pred(Const(name), [Var('x'), Var('y')])
        bind = Bind('\\', Var('x'), pred)
        return Bind('\\', Var('y'), bind)
    else:
        raise Exception("ArrError: Arity of predicate is greater than 2.")

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

        case Term(term):
            term = subst_term(v, w, term)
            return Term(term)

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
                        return apply((w, Term(arg)))
                    case [arg1, arg2]:
                        w_prime = apply((w, Term(arg1)))
                        return apply((w_prime, Term(arg2)))
                    case _:
                        raise Exception("Invalid arity for predicate in expression substitution.")
            else:
                return expr

        case Op(name, args):
            args = [subst_expr(v, w, expr) for expr in args]
            return Op(name, args)

        case Term(Wff(expr)):
            expr = subst_expr(v, w, expr)
            term = Wff(expr)
            return Term(term)

        case Term(term):
           if v == term:
               return w
           else:
               return expr

        case _:
            return expr

def apply(exprs: tuple[Expr, Expr]) -> Expr:

    match exprs:

        case Term(term), Bind('\\', Var(name), expr):
            if name.islower():
                return subst_terms(Var(name), term, expr)
            else:
                raise Exception("AppError: Invalid types for function application.")

        case Bind('\\', Var(name), expr), Term(term):
            if name.islower():
                print('---')
                return subst_terms(Var(name), term, expr)
            else:
                raise Exception("AppError: Invalid types for function application.")

        case Bind(name='\\', var=Var(name1), expr=expr1), Bind(name='\\', var=Var(name2), expr=expr2):
            if name1.isupper() and name2.islower() \
            or name1.islower() and name2.isupper():
                v = Var(name1)
                w = Bind('\\', Var(name2), expr2)
                return subst_expr(v, w, expr1)
            else:
                raise Exception("AppError: Invalid types for function application.")

        case _:
                raise Exception("AppError: Invalid types for function application.")



class Model:

    def __init__(self) -> None:
        self.entities: set[Entity] = set()                                    # x : e
        self.unaries: dict[str, dict[Entity, bool]] = dict()                  # λx.P(x)
        self.binaries: dict[str, dict[Entity, dict[Entity, bool]]] = dict()   # λy.λx.R(x,y)

    def eval(self, expr: Expr) -> bool | None:
        match expr:

            case Op(name='&', args=[arg1, arg2]):
                return self.eval(arg1) and self.eval(arg2)

            case Op(name='->', args=[arg1, arg2]):
                return (not self.eval(arg1)) or self.eval(arg2)

            case Pred(name, args=[arg]):
                i = self.unaries.get(name, None)
                if i:
                    return i.get(arg, None)
                else:
                    return None

            case Pred(name, args=[arg1, arg2]):
                i = self.binaries.get(name, None)
                if i:
                    i2 = i.get(arg1, None)
                    if i2:
                        return i2.get(arg2, None)
                    else:
                        return None
                else:
                    return None

            case Bind(name, var, expr):
                match name:
                    case '\\':
                        raise Exception("No lambdas allowed.")
                    case '#':
                        return any([self.eval(subst_terms(var, e, expr)) for e in self.entities])
                    case '@':
                        return all([self.eval(subst_terms(var, e, expr)) for e in self.entities])
                    case _:
                        raise Exception("EvalError: Binder not found.")
            case _:
                raise Exception("EvalError: Cannot evaluate.")



    def word2lf(self, cat: list[tuple[str,str]], lemma: str = ''):
        match cat:
            case [('sel', 'd'),('sel', 'd'),('cat', 'v')]:
                return Bind(name='\\',
                            var=Var('y'),
                            expr=Bind(name='\\',
                                      var=Var('x'),
                                      expr=Pred(name=Const(lemma),
                                                args=[Var('x'), Var('y')])))
            case [('sel', 'j'),('sel', 'd'),('cat', 'v')]:
                return Bind(name='\\',
                            var=Var('P'),
                            expr=Pred(name=Var('P'), args=[]))
            case [('sel', 'd'),('cat', 'v')]:
                return Bind(name='\\',
                            var=Var('x'),
                            expr=Pred(name=Const(lemma),
                                      args=[Var('x'), Var('y')]))
            case [('cat', 'd'), *_]:
                return Term(Const(lemma))
            case [('cat', 'n'), *_]:
                return Bind('\\', Var('x'), Pred(Const(lemma), [Var('x')]))
            case [('cat', 'j')]:
                return Bind('\\', Var('x'), Pred(Const(lemma), [Var('x')]))
            case [('sel', 'n'), ('cat', 'j')]:
                return Bind('\\', Var('P'), Bind('\\', Var('x'), Op('&', [Pred(Var('P'), [Var('x')]), Pred(Const(lemma), [Var('x')])])))
            case [('sel', 'n'),('cat', 'd'), *_]:
                p = Pred(name=Const('P'), args=[Var('x')])
                q = Pred(name=Const('Q'), args=[Var('x')])
                match lemma:
                    case 'every':
                        op = Op('->', [p, q])
                        bind = Bind('@', Var('x'), op)
                        return Bind('\\',Var('P'),Bind('\\',Var('Q'), bind))
                    case 'a' | 'an':
                        op = Op('&', [p, q])
                        bind = Bind('#', Var('x'), op)
                        return Bind('\\',Var('P'),Bind('\\',Var('Q'), bind))
                    case _:
                        raise Exception(f"Current determiner {lemma} is unimplemented.")
            case _:
                return None


if __name__ == "__main__":
    p = build_predicate('know', 2)
    e = Term(Const('e'))
    p = apply((p, e))
    print(p)
