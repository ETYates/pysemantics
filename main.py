from lexer import Lexer, Lexicon
from logic import Model, Translator
from parser import Parser

class SymbolicAI:

    def __init__(self): 
        self.lexicon: Lexicon = Lexicon()
        self.parser: Parser = Parser()
        self.model: Model = Model()
        self.lexer: Lexer = Lexer()
        self.translator = Translator()

    def run(self, raw_input: str):

        lexes = self.lexer.lexify(raw_input)
        self.lexicon.add_lexes(lexes)

        derivation_tree = self.parser.parse(self.lexicon, lexes)
        semantic_tree = self.translator.translate(derivation_tree)

        return semantic_tree

    def repl(self) -> None:

        while (raw_input := input("|- ")) != 'quit':

            sem_tree = self.run(raw_input)
            print(sem_tree)


if __name__ == "__main__":
    
    symbolic_ai = SymbolicAI()
    raw_input = "Aristotle is a man"
    semantic_tree = symbolic_ai.run(raw_input)
    print(semantic_tree)
