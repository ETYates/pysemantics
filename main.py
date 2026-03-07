from logic import Logic, Expr, Model
from parse import Parser

import warnings

class SymbolicAI:

    def __init__(self): 
        self.parser: Parser = Parser()
        self.model: Model = Model()
        self.logic: Logic = Logic()

    def run(self, raw_input: str):
        trees, lemmas = self.parser.parse(raw_input)
        exprs: list[Expr] = []
        for tree in trees:
            expr = self.logic.denotation(tree, lemmas)
            exprs.append(expr)

        expr = exprs[0]

        if len(exprs) > 1:
            warnings.warn("Ambiguous sentence: tree arbitrarily selected.", SyntaxWarning)

        return expr
        # value = self.model.evaluate(expr)

        # return value

    def repl(self) -> None:

        while (raw_input := input("|- ")) != 'quit':

            expression = self.run(raw_input)
            print(expression)


if __name__ == "__main__":
    
    symbolic_ai = SymbolicAI()
    # raw_input = "Aristotle is a man"
    # expr = symbolic_ai.run(raw_input)
    # print(expr)
    symbolic_ai.repl()
