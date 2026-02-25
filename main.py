from lexer import Lexer, Lexicon
from logic import Model
from mgtdbp import parse

class SymbolicAI:

    def __init__(self): 
        self.lexicon = Lexicon()
        self.model = Model()
        self.lexer = Lexer()

    def run(self, raw_input: str):

        lexes = self.lexer.lexify(raw_input)
        entries = [f"{lex.text}: {lex.lemma}" for lex in lexes]
        self.lexicon.add_lexes(lexes)

        deriv_tree = parse(self.lexicon.lexicon, 'c', -1 * float(1e-10), entries)
        sem_tree = self.model.convert(deriv_tree)
        return sem_tree

    def repl(self) -> None:

        while (raw_input := input("|- ")) != 'quit':
            sem_tree = self.run(raw_input)
            print(sem_tree)


if __name__ == "__main__":
    
    symbolic_ai = SymbolicAI()
    raw_input = "Aristotle is a man"
    sem_tree = symbolic_ai.run(raw_input)
    print(sem_tree)
