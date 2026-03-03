from mgtdbp.mgtdbp import parse
from lexer import Lexicon, Lexeme

class Parser:

    def __init__(self):
        self.start_symbol = 'c'
        self.probability  = -1 * float(1e-12)

    def parse(self, lexicon: Lexicon,
                    lexemes: list[Lexeme]):

        input_tokens = [f"{lex.text}: {lex.lemma}" for lex in lexemes]
        grammar = lexicon.lexicon

        derivation_tree = parse(
            grammar,
            self.start_symbol,
            self.probability,
            input_tokens
        )

        return derivation_tree
