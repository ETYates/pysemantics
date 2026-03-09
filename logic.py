from nltk.grammar import FeatStructNonterminal
from nltk.featstruct import Feature
from nltk.tree import Tree

from collections.abc import Callable
from collections import defaultdict

from dataclasses import dataclass

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
    r"""
    Variables and constants for predicates of the type
    \x.f(x) or \y.\x.g(x,y). Not intended to be instantiated 
    itself but only through inheritace in classes Const and 
    Var.
    """
    ...


@dataclass
class Const(Entity):
    """
    Constant entities, i.e. a named entity.
    """
    name: str

    def __str__(self):
        return self.name


@dataclass
class Var(Entity):
    """
    Variable entity, represented by x, y, or z.
    """
    name: str

    def __str__(self):
        return self.name


@dataclass
class Wff(Entity):
    """
    A "well-formed-formula" for use in iota statements, which
    are expressions that evaluate to an Entity type.
    """
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
    """
    Null expression.
    """

    def __str__(self) -> str:
        return "null"

Unary = Callable[[Entity], Truth]

class Model:
    """
    Mathematical structure for representing the values set for predicates
    through declarative sentences. This is used to evaluate expressions
    for Truth-Value, or to answer queries.
    """

    def __init__(self) -> None:
        self.entities: set[Entity] = set()                                    # x : e
        self.unaries: dict[str, dict[Entity, bool]] = dict()                  # λx.P(x)
        self.binaries: dict[str, dict[Entity, dict[Entity, bool]]] = dict()   # λy.λx.R(x,y)

class Lemmas:
    """
    A helper class meant to assist in the creation of expressions. Given that
    English words often have verbal or plural suffixes, we need to be sure to
    lemmatize all the words in the sentence in order that words with the same
    lemma will recieve the same logical predicative symbol in the model,
    despite their textual strings being distinct. 

    The challenge with this implementation is due to the fact that the nltk
    chart-parser doesn't allow for the lemmas to be carried into the parser
    tree for subsequent analysis. In order to get around this it is necessary
    to create a temporary lemmatizer for each sentence using the respective
    token, tag, and lemma that is produced by the output of the spacy analyzer. 
    """
    entries = defaultdict(set)

    def add_lemma(self,
                  word: str, 
                  cat: str, 
                  lemma: str) -> None:
        """
        Adds a tuple of a word form and its respective part-of-speech
        category to the dictionary and assigns the respective lemma as the
        value to the tuple key.

        :param word: input string of the actual word in the sentence
        :param cat: nonterminal symbol for the word in the grammar
        :param lemma: respective lemma string for word and cat
        """

        key = (word, cat)
        self.entries[key].add(lemma)

    def add_lemmas(self, 
                   words: list[str],
                   cats: list[str],
                   lemmas: list[str]) -> None:
        """
        Adds multiple lemmas to the temporary lemmatizer. Wrapper for the above method.
        """

        for word, cat, lemma in zip(words, cats, lemmas):
            self.add_lemma(word, cat, lemma)
    
    def __getitem__(self, key: tuple[str,str]) -> str:
        """
        Standard dunder method to allow hashing with brackets.
        """

        lemma = self.entries[key].pop()
        return lemma
    

class Logic:
    """
    Contains methods for building and manipulating lambda expressions of the
    types defined above. This logical system is based on those outlined in
    the book "Invitation to Formal Semantics" by Cappock and Champollion. 

    Essentially this class implements predicate logic with lambdas and higher
    order functions. The basic types are entities of type "e" and truth-value
    (basically a boolean) of type "t". Predicates are functions taking entities
    as input expressions and return truth-values retrieved from analysis of
    a model (being a mathematical structure).
    """

    def _build_unary(self, lemma: str) -> Expr:
        r"""
        Construct a predicate of the form:

        \x.f(x) : e -> t

        :param lemma: string used to create the predicate symbol.
        """

        term: Entity = Const(lemma)
        var = Var('x')
        args: list[Entity] = [var]

        expr: Expr = Pred(term, args)
        name = LAMBDA
        expr = Bind(name, var, expr)
        return expr

    def _build_binary(self, lemma: str) -> Expr:
        r"""
        Creates an expression of the form and type:

        \y.\x.f(x,y) : e -> (e -> t)

        :param lemma: string used to create the predicate symbol.
        """

        term: Entity = Const(lemma)


        x, y = Var('x'), Var('y')
        args: list[Entity] = [x, y]
        expr: Expr = Pred(term, args)

        name = LAMBDA
        expr = Bind(name, x, expr)
        expr = Bind(name, y, expr)
        return expr

    def _build_quant(self, lemma: str) -> Expr:
        r"""
        Returns possible generalized quantifier expressions depending on which
        lemma is passed as input. For example, indefinite articles produce
        expression of the following form and type:

        \P.\Q.#x.[P(x) & Q(x)]: ((e -> t) -> ((e -> t) -> t))

        Definite articles
        produce expressions in the form of iota-bindings that indicate definite
        description in the form specified by Bertrand Russell:

        ~x.f(x) : e

        This means that there is a single x that satisfies the predicate f, and
        this expression evaluates to the value of an entity. As a result, iota
        expressions can occur within the arguments of a predicate such as:

        f(~x.g(x)) : t

        The implementation of this function is currently naive because it relies
        on the individual specification of lemmas within the program logic, which
        is not extensible to the many more determiners of different values that
        will be added in the future.

        TODO: create a lexicon of logical expressions for closed grammatical
        classes such as prepositions and determiners.
        """

        var: Entity = Var('x')
        p: Entity = Var('P')

        q: Entity = Var('Q')

        if lemma == 'every':
            binder = FORALL
            rator  = IFTHEN

        elif lemma == 'a' or lemma  == 'some':
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

    def _build_copula(self) -> Expr:
        r"""
        Creates an expression for representing the semantic value of the verb
        "to be" which is of the value and type:

        \P.P : ((e -> t) -> (e -> t))

        This is simply an identity function for predicates that is used to
        apply predicates in object position to the subject.

        """

        var = Var('P')
        expr = Pred(term=var, args=[])
        expr = Bind(binder=LAMBDA, var=var, expr=expr)
        return expr

    def _subst_term(self, 
                   v: Var,
                   w: Entity,
                   term: Entity) -> Entity:
        """
        Given a variable, an entity, and another input entity, return the 
        entity if the variable matches the term entity.

        :param v: variable 
        :param w: entity, either a constant, variable, or expression of the type e
        :param term: a constant or a variable
        """

        if v == term:
            return w
        else:
            return term

    def _subst_var(self, 
                  v: Var,
                  w: Var,
                  var: Var) -> Var:
        """
        Substitutes v for w, or else if an identity function

        :param v: input variable
        :param w: input variable
        :param var: input variable
        """

        if v == var:
            return w
        else:
            return var

    def _alpha_conversion(self, 
                         v: Var,
                         w: Var,
                         expr: Expr) -> Expr:
        r"""
        Implementation of alpha-conversion (variable renaming). For example, if
        alpha-conversion were applied to the predicate \x.f(x), with the input
        variables x and y, the function would return the expression \y.f(y)
        
        :param v: input variable
        :param w: input variable
        :param expr: input expression
        """
        match expr:

            case Bind(name, var, expr):
                var = self._subst_var(v, w, var)
                expr = self._alpha_conversion(v, w, expr)
                return Bind(name, var, expr)

            case Op(name, args):
                args = [self._alpha_conversion(v, w, arg) for arg in args]
                return Op(name, args)

            case Pred(name, args):
                args = [self._subst_term(v, w, arg) for arg in args]
                return Pred(name, args)

            case _:
                return expr

    def _free_vars(self, expr: Expr) -> list[Var]:
        r"""
        Given an expression, return a list of all variables that occur in a
        lambda abtraction. For example:

        free_vars(\x.f(x)) -> [x]
        free_vars(\y.\x.g(x,y) -> [x,y]
        free_vars(\z.\y.\x.h(x,y,z) -> [x,y,z]

        :param expr: input expression
        """
        
        vs: list[Var] = []

        if isinstance(expr, Bind):

            if expr.binder == LAMBDA:
                var = expr.var
                expr = expr.expr

                vs.append(var)
                vs.extend(self._free_vars(expr))

            else:
                expr = expr.expr
                vs.extend(self._free_vars(expr))

        elif isinstance(expr, Op):

            args = expr.args

            for arg in args:
                new_vs = self._free_vars(arg)
                vs.extend(new_vs)

        vs.reverse()
        return vs

    def _reduce_bind(self, 
                    v: Var, 
                    expr: Expr) -> Expr:
        r"""
        Given an input variable and expression, remove all bindings in which
        the variable occurs in a lambda-abstraction. This is similar to naive
        eta-reduction. For example:

        reduce_bind(x, \x.f(x)) -> f(x)

        :param v: input variable
        :param expr: 
        """

        if isinstance(expr, Bind):
            binder: str = expr.binder
            w: Var = expr.var
            new_expr: Expr = expr.expr

            if binder == LAMBDA:
                if v == w:
                    return new_expr
                else:
                    new_expr = self._reduce_bind(v, new_expr)
                    new_expr = Bind(binder, w, new_expr)
                    return new_expr
            else:
                new_expr = self._reduce_bind(v, new_expr)
                new_expr = Bind(binder, w, new_expr)
                return new_expr

        elif isinstance(expr, Op):
            rator = expr.rator
            args = expr.args
            args = [self._reduce_bind(v, expr) for expr in args]
            expr = Op(rator, args)
            return expr

        else:
            return expr

    def _lift_binds(self, expr: Expr) -> Expr:
        r"""
        Given an input expression, find all bindings of lambda-abstractions
        which occur which other expressions, and move those lambda bindings to
        the topmost level of the syntax tree of the expression. For example:

        lift(@x[f(x) & \y.g(y,x)]) -> \y.@x[f(x) & g(y,x)] 

        :param expr: input expression
        """
        vs = self._free_vars(expr)

        for var in vs:
            expr = self._reduce_bind(var, expr)
            expr = Bind(LAMBDA, var, expr)

        return expr
            
    def _substitute(self, 
                   v: Var, 
                   w: Expr, 
                   expr: Expr) -> Expr:
        r"""
        Given an input expression E, return E with all instances of the
        variable v replaced with the expression w. In symbolic terms it
        would be written:

        E[v := w]

        :param v: input variable
        :param w: input expression 
        :return expr: output expression
        """

        match expr:

            case Bind(name, var, expr):

                if var == w:
                    tmp = Var('v')
                    expr = self._alpha_conversion(var, tmp, expr)
                    expr = self._substitute(v, w, expr)
                    expr = self._alpha_conversion(tmp, v, expr)
                    expr = Bind(name, v, expr)
                    return expr

                else:
                    expr = self._substitute(v, w, expr)
                    expr = Bind(name, var, expr)
                    return expr

            case Pred(term, args):

                if v == term:
                    while args:
                        arg = args.pop(0)
                        w = self.beta_reduction((w, arg))
                    return w

                else:
                    if isinstance(w, Entity):
                        args = [self._subst_term(v, w, arg) for arg in args]
                        expr = Pred(term, args)
                        return expr
                    else:
                        return expr

            case Op(name, args):
                args = [self._substitute(v, w, expr) for expr in args]
                expr = Op(name, args)
                return expr

            case Var():
                if v == expr:
                    return w
                else:
                    return expr

            case _:
                return expr

    def modify(self, expr1: Expr, expr2: Expr) -> Expr:
        r"""
        Given two predicates \x.f(x) and \x.g(x) return an expression of the
        form \x.[f(x) & g(x)]

        :param expr1: input expression
        :param expr2: input expression
        :return expr: output expr
        """

        p = Pred(Var('P'), [Var('x')])
        q = Pred(Var('Q'), [Var('x')])
        rator = AND

        expr = Op(rator, [p, q])
        expr = Bind(LAMBDA, Var('x'), expr)
        expr = Bind(LAMBDA, Var('Q'), expr)
        expr = Bind(LAMBDA, Var('P'), expr)
        expr = self.beta_reduction((expr1, expr))
        return self.beta_reduction((expr2, expr))

    def beta_reduction(self, exprs: tuple[Expr, Expr]) -> Expr:
        r"""
        Main function for application of lambda expressions. For example:\

        \x.f(x)(a) -> f(x)
        \y.\x.g(x,y)(b)(a) -> g(a,b)

        :param exprs: input expressions in the form of (Expr, Expr)
        """

        # for expr in exprs:
        #     print(expr)
        # print('------')

        match exprs:

            case Const(term), Bind(binder=LAMBDA, var=Var(name), expr=expr):

                if name.islower():
                    v = Var(name)
                    w = Const(term)
                    expr = self._substitute(v, w, expr)
                    expr = self._lift_binds(expr)
                    return expr

                raise Exception("AppError: failed beta_reduction")

            case Bind(binder=LAMBDA, var=Var(name), expr=expr), Const(term):

                if name.islower():
                    v = Var(name)
                    w = Const(term)
                    expr = self._substitute(v, w, expr)
                    expr = self._lift_binds(expr)
                    return expr

                raise Exception("AppError: failed beta_reduction")

            case Var(term), Bind(binder=LAMBDA, var=Var(name), expr=expr):

                if name.islower():
                    v = Var(name)
                    w = Var(term)
                    expr = self._substitute(v, w, expr)
                    expr = self._lift_binds(expr)
                    return expr

                raise Exception("AppError: failed beta_reduction")

            case Bind(binder=LAMBDA, var=Var(name), expr=expr), Var(term):

                if name.islower():
                    v = Var(name)
                    w = Var(term)
                    expr = self._substitute(v, w, expr)
                    expr = self._lift_binds(expr)
                    return expr

                raise Exception("AppError: failed beta_reduction")

            case Bind(binder='\\', var=Var(name1), expr=expr1), Bind(binder='\\', var=Var(name2), expr=expr2):

                if name1.isupper() and name2.islower():
                    binder = '\\'
                    var = Var(name2)
                    expr = expr2

                    v = Var(name1)
                    w = Bind(binder, var, expr)
                    expr = self._substitute(v, w, expr1)
                    expr = self._lift_binds(expr)

                    return expr

                elif name1.islower() and name2.isupper():
                    binder = '\\'
                    var = Var(name1)
                    expr = expr1

                    v = Var(name2)
                    w = Bind(binder, var, expr)
                    expr = self._substitute(v, w, expr2)
                    expr = self._lift_binds(expr)

                    return expr

                raise Exception(f"AppError: Invalid types for function application: {name1} and {name2}")
            
            case expr1, expr2:

                if isinstance(expr1, Epsilon):
                    return expr2

                elif isinstance(expr2, Epsilon):
                    return expr1

                raise Exception(f"AppError: Invalid types for function application: {expr1} and {expr2}.")

    def build_expr(self, 
                   cat: str, 
                   lemma: str, 
                   arity: int = 2):
        """
        Given a category, lemma, and arity, build the appropriate expression

        :param cat: nonterminal category 
        :param lemma: lemma for word (used for predicate symbold)
        :param arity: for indicating the transitivity of a verb
        """

        match cat:

            case 'N' | 'A':
                return self._build_unary(lemma)

            case 'D':
                return self._build_quant(lemma)

            case 'DP':
                return Const(lemma)

            case 'V':

                if lemma == 'be':
                    return self._build_copula()
                else:
                    if arity == 1:
                        return self._build_unary(lemma)
                    elif arity == 2:
                        return self._build_binary(lemma)
                    else:
                        raise ValueError(f"arity > 2 not allowed: is {arity}")

            case _:
                return Epsilon()
                
    def _proc_tree(self, 
                   symbol: str, 
                   tree: str | Tree,
                   lemmas: dict[tuple[str, str], str]) -> Expr:
        """
        Function for processing trees which could either be an nltk.Tree object
        or alternatively just a string.

        :param symbol: non-terminal symbol
        :param tree: input syntactic tree
        :param lemmas: lemma dictionary for sentence
        """

        if isinstance(tree, str):
            token = tree
            cat = symbol
            lemma = lemmas[(token,cat)]
            expr = self.build_expr(cat, lemma)
            return expr

        else:
            expr = self.denotation(tree, lemmas)
            return expr

    def _object_phrase(self, tree: Tree, lemmas) -> Expr:
        """
        A method for calculating the semantic expression of a tree in object
        position. When the main verb is the copula "to be" it is often
        necessary to discard the semantic value of the article of type D in
        order to correctly perform beta-reductions. For example:

        'Aristotle is a man' -> man(Aristotle)

        :param tree: input syntactic tree
        """

        children: list[Tree] = [child for child in tree]
        symbols: list[str] = [self._get_symbol(tree) for tree in children]

        if symbols == ['D', 'NP']:
            
            if len(children[0]) == 1:
                lemma = children[0][0]
            else:
                raise TypeError("invalid child of node-type D")

            if lemma == 'a':
                tree = children[1]
                symbol = self._get_symbol(tree)
                expr = self._proc_tree(symbol, tree, lemmas)
            else:
                symbol = self._get_symbol(tree)
                expr = self._proc_tree(symbol, tree, lemmas)

            return expr

        else:
            raise ValueError("incorrect types for object phrase of copula.")

    def _get_symbol(self, tree: Tree | str) -> str:
        """
        Given an input tree, return the symbol that represents the syntactic
        type of the tree, which is a non-terminal symbol.

        :param tree: input syntactic tree
        """

        if isinstance(tree, Tree):
            key = Feature('type')
            features: FeatStructNonterminal = tree.label()
            symbol = str(features[key])

        else:
           symbol = tree

        return symbol

    def _get_terminal(self, tree: Tree) -> str:
        """
        Given a tree, check if it a tree that has a single terminal symbol as
        its child. This applies to rules of the type nonterminal -> [terminal].
        For example:

        N -> 'man'
        V -> 'walks'

        :param tree: input tree
        """

        children = [t for t in tree]
        if len(children) == 1:
            terminal = children[0]
            return terminal
        else:
            raise ValueError(f"NonTerminal that produces a terminal should only have one child: has {len(children)}")

    def denotation(self, 
                   tree: Tree, 
                   lemmas: dict[tuple[str,str], str]) -> Expr:
        """
        Given an input tree and a dictionary containing the form-lemma
        correspondences present in the current sentence, translate the
        syntactic tree into an semantic expression tree.

        :param tree: input tree
        :param lemmas: lemma dictionary
        """

        symbol = self._get_symbol(tree)
        children: list[Tree] = [child for child in tree]

        match children:
            case [tree]:
                expr = self._proc_tree(symbol, tree, lemmas)

            case [left, right]:

                left_sym = self._get_symbol(left)
                right_sym = self._get_symbol(right)

                # Here we will check if the left element is a verb. We
                # specifically whether the verb is the copula (the verb "to
                # be") and the complement of the V node is an object DP. If so,
                # the object DP will need a different denotation function
                # that will only return the denotation of the NP without the article
                # if the article is "a" or "an" (indefinite).

                if (left_sym, right_sym) == ('V', 'DP'):
                    left_word = self._get_terminal(left)
                    left_lem = lemmas[(left_word, left_sym)]
                    if left_lem == 'be':
                        right_expr = self._object_phrase(right, lemmas)
                    else:
                        right_expr = self._proc_tree(symbol, right, lemmas)
                else:
                    right_expr = self._proc_tree(symbol, right, lemmas)

                left_expr = self._proc_tree(symbol, left, lemmas)

                if symbol == 'NP':
                    expr = self.modify(left_expr, right_expr)
                else:
                    expr = self.beta_reduction((left_expr,right_expr))

            case []:
                expr = Epsilon()

            case _:
                raise ValueError("invalid tree format")

        return expr


if __name__ == "__main__":

    logic = Logic()
    q = logic._build_quant('a')
    g = logic._build_binary('g')
    f = logic._build_unary('f')
    a = Const('a')
    expr = logic.beta_reduction((q,f))
    expr = logic.beta_reduction((g,expr))
    print(expr)
    print(logic._free_vars(expr))
    expr = logic.beta_reduction((expr,a))
    print(expr)
