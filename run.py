import spacy
import pprint
from mgtdbp import parse, dt2t, pptree

nlp = spacy.load("en_core_web_sm")
doc = nlp("some text")


class Lexeme:


    def __init__(self, text: str, tag: str, lemma: str):
        self.text = text
        self.tag = tag
        self.lemma = lemma
        self.set_cat()

    def __str__(self) -> str:
        return f"{self.lemma}: {self.cat}"

    def set_cat(self) -> None:
        match self.tag:
            case "JJ" | "JJR" | "JJS":
                self.cat = [('sel', 'n'),('cat', "n")]
            case "NN" | "NNS":
                self.cat = [('cat', "n")]
            case "NNP" | "PRP" | "NNPS":
                self.cat = [('cat', 'd')]
            case "DT":
                self.cat = [('sel', 'n'),('cat', "d")]
            case "VBZ" | "VBD" | "VBP" | "VBN" | "VBG" | "VB":
                match self.lemma:
                    case "do":
                        self.cat = [('sel', 'v'), ('cat', 't')]
                    case "have":
                        self.cat = [('sel', 'v'), ('cat', 'h')]
                    case "be":
                        self.cat = [('sel', 'v'),('cat', 'b')]
                    case _:
                        self.cat = [('cat','v')]
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
                self.cat = [('cat', 'w')]
            case "WDT":
                self.cat = [('sel', 'n'), ('cat', 'd'), ('neg', 'wh')]
            case _:
                raise Exception(f"POS tag {self.tag} is unimplemented.")

class Lexicon:

    def __init__(self):
        self.lexicon = [([], [('sel', 'v'),('cat','c')]),
                   ([],[('sel','v'),('pos','wh'), ('cat', 'c')])
                   ]
        self.members: set[str] = {}

    def add(self, text, cat):
        entry = ([text], cat)
        self.lexicon.append(entry)

    def __str__(self):
        return str(self.lexicon)


def tokenize(raw_input: str):
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
        for lex in lexes:
            text = lex.text
            cat = lex.cat
            if text not in lexicon.members:
                if cat == [('cat', 'v')]:
                    lexicon.add(text, [('sel', 'd'), ('sel', 'd'), ('cat', 'v')])
                    lexicon.add(text, [('sel', 'c'), ('sel', 'd'), ('cat', 'v')])
                    lexicon.members[text] = True
                else:
                    lexicon.add(text, cat)
        inpt = raw_input.split()
        dt = parse(lexicon.lexicon, 'c', -1 * float(0.001), inpt)
        pptree(dt2t(dt))
        pprint.pprint(lexicon.lexicon)


if __name__ == "__main__":
    __main__()
