"""
run - file to run the whole program

This module is for running the whole semantics program. SpaCy is used for
tokenization and a top-down MG[+SpIC_mrg] parser is used for constituency
parsing.
"""
import spacy
import pprint
from mgtdbp import parse, dt2t, pptree

nlp = spacy.load("en_core_web_sm")

class Lexeme:
    """A simple class to carry data from spacy into the MG parser. There is
    also a function to convert tags from the standard PENN treebank tags to the
    simple tags used by Edward Stabler et al. in their scholarship for this
    formalism"""

    def __init__(self, text: str, tag: str, lemma: str):
        self.text = text
        self.tag = tag
        self.lemma = lemma
        self.set_cat()

    def __str__(self) -> str:
        return f"{self.lemma}: {self.cat}"

    def set_cat(self) -> None:
        """Convert PENN treebank tags to simple tags."""
        match self.tag:
            case "JJ" | "JJR" | "JJS":
                self.cat = [[('cat', 'j')],
                            [('sel', 'n'),('cat', "j")]]
            case "NN" | "NNS":
                self.cat = [('cat', "n")]
            case "NNP" | "PRP" | "NNPS":
                self.cat = [[('cat', 'd')],
                            [('cat', 'd'),('neg', 'case')]
                            ]
            case "DT":
                self.cat =[[('sel', 'n'),('cat', "d")],
                           [('sel', 'n'),('cat', "d"),('neg', 'case')],
                           [('sel', 'j'),('cat', "d")],
                           [('sel', 'j'),('cat', "d"),('neg', 'case')]
                           ]
            case "VBZ" | "VBD" | "VBP" | "VBN" | "VBG" | "VB":
                match self.lemma:
                    case "do":
                        self.cat = [('sel', 'v'), ('cat', 't')]
                    case "have":
                        self.cat = [('sel', 'v'), ('cat', 'h')]
                    case "be":
                        self.cat = [[('sel', 'v'),('cat', 't')],
                                    [('sel', 'j'),('sel', 'd'),('cat', 'v')],
                                    [('sel', 'd'),('sel', 'd'),('cat', 'v')]
                                    ]
                    case _:
                        self.cat = [
                                    [('sel', 'd'),('sel', 'd'),('cat','v')],
                                    [('sel', 'c'),('sel', 'd'),('cat','v')],
                                    [('sel', 'd'),('cat','v')]
                                    ]
            case ".":
                self.cat = [('cat', 's')]
            case "RB" | "RBR" | "RBS":
                self.cat = [('cat', 'r')]
            case "IN":
                self.cat = [('sel', 'd'),('cat','p')]
            case "MD":
                self.cat = [('sel', 'v'), ('sel', 't')]
            case "EX":
                self.cat = [('cat', 'x')]
            case "WP":
                self.cat = [('cat', 'd'), ('neg', 'wh')]
            case "WDT":
                self.cat = [('sel', 'n'), ('cat', 'd'), ('neg', 'wh')]
            case _:
                raise Exception(f"POS tag {self.tag} is unimplemented.")

class Lexicon:
    """
    This class contains a lexicon that starts with a small number of lexical
    entries (epsilons) and incrementally adds new entries as input text is
    processed.
    """

    def __init__(self):
        # base lexical entries for grammar
        self.lexicon = [([],[('sel','v'),('cat','c')]),
                        ([],[('sel','v'),('pos','wh'),('cat','c')]),
                        ([],[('sel', 't'),('cat', 'c')]),
                        ([],[('sel', 't'),('pos', 'case'),('cat', 'c')]),
                        ([],[('sel', 't'),('pos', 'wh'),('cat', 'c')])]
        self.members = set() # Keeps track of which words are in lexicon.

    def add(self, text, cat):
        if isinstance(cat,list) and all(isinstance(f, list) for f in cat):
            for f in cat:
                entry = ([text], f)
                self.lexicon.append(entry)
        else:
            entry = ([text], cat)
            self.lexicon.append(entry)


    def __str__(self):
        return str(self.lexicon)


def tokenize(raw_input: str):
    # process input with spacy
    lexes: list = []
    doc = nlp(raw_input)
    for item in doc:
        text = item.text
        lemma = item.lemma_
        tag = item.tag_
        lex = Lexeme(text, tag, lemma)
        lexes.append(lex)
    return lexes

def __main__():
    lexicon = Lexicon()
    while (raw_input := input("|- ")) != 'quit':
        lexes = tokenize(raw_input)
        inpt = []
        for lex in lexes:
            cat = lex.cat
            text = f"{lex.text}: {lex.lemma}"
            inpt.append(text)
            if text not in lexicon.members:
                lexicon.add(text, cat)
                lexicon.members.add(text)
        dt = parse(lexicon.lexicon, 'c', -1 * float(1e-10), inpt)
        pptree(dt2t(dt))
        pprint.pprint(lexicon.lexicon)


if __name__ == "__main__":
    __main__()
