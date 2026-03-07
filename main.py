from logic import Logic, Expr, Model
from parse import Parser

import warnings

class SymbolicAI:
    """
    Symbolic AI system that utilizes formal semantics and generative syntax to
    perform symbolic reasoning from user-inputted text. The purpose of this
    program is to allow for the processing of text files and keyboard input of
    natural language using principles similar to compiler theory and programming
    language design. 
    """

    def __init__(self): 
        self.parser: Parser = Parser()
        self.model: Model = Model()
        self.logic: Logic = Logic()

    def run(self, raw_input: str) -> Expr:
        """
        Runs the whole program a single time on a single input and returns a
        single output. 

        params:
            raw_input: the input string from the user to be processed by the
                system, raw string

        returns expr
        """
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
        """
        read-execute-print-loop method for testing the whole system. This
        method allows for repeated calls from the command line to allow for
        easy usage, testing, and demonstration.

        type "quit" to exit from the REPL.
        """

        while (raw_input := input("|- ")) != 'quit':

            expression = self.run(raw_input)
            print(expression)


if __name__ == "__main__":
    
    symbolic_ai = SymbolicAI()
    # raw_input = "Aristotle is a man"
    # expr = symbolic_ai.run(raw_input)
    # print(expr)
    symbolic_ai.repl()
