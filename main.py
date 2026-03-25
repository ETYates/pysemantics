from logic import Logic, Expr, Model
from parse import Parser, Node

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

    def run(self, raw_input: str):
        """
        Runs the whole program a single time on a single input and returns a
        single output. 

        params:
            raw_input: the input string from the user to be processed by the
                system, raw string

        returns expr
        """
        nodes, lemmas = self.parser.parse(raw_input)
        # if len(nodes) > 1:
        #     warnings.warn("Ambiguous sentence: tree arbitrarily selected.", SyntaxWarning)
        node: Node = nodes[0]
        expr = self.logic.denotation(node, lemmas)

        punct_node = node.data[1]
        if isinstance(punct_node, Node):
            punct = punct_node.data
            if punct == '.':
                self.model.decl(expr)
                return expr, None
            elif punct == '?':
                value = self.model.eval(expr)
                return expr, value
        else:
            raise ValueError("Invalid punctuation.")


    def repl(self) -> None:
        """
        read-execute-print-loop method for testing the whole system. This
        method allows for repeated calls from the command line to allow for
        easy usage, testing, and demonstration.

        type "quit" to exit from the REPL.
        """
        show_expr = False

        while (raw_input := input("|- ")) != 'quit':

        
            match raw_input:
                case "--show-formulae":
                    show_expr = True
                case "--hide-formulae":
                    show_expr = False
                case raw_input:

                    try:
                        expr, value = self.run(raw_input)
                        if value:
                            print(value)

                        if show_expr:
                            print(expr)

                    except:
                        print("Error: invalid input.")


if __name__ == "__main__":
    
    symbolic_ai = SymbolicAI()
    # raw_input = "Aristotle is a man"
    # expr = symbolic_ai.run(raw_input)
    # print(expr)
    symbolic_ai.repl()
