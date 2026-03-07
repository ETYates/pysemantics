from nltk.grammar import FeatureGrammar, Production, FeatStructNonterminal
from nltk.parse.featurechart import FeatureChartParser
from nltk.data import load
from nltk.parse import load_parser
from collections import defaultdict
import spacy


class Grammar:

    start = 'CP'

    basis = """
        CP -> DP[-wh] TP/?x[-wh]
        CP -> DP[+wh] TP/?x[+wh]
        CP -> C TP
        TP/?x[+wh] -> T[-empty] vP/?x[+wh]
        TP/?x[-wh] -> T vP/?x[-wh]
        TP -> T[-empty] vP[+inv]
        vP/?x[+wh] -> DP/DP[+wh] VP
        vP/?x[-wh] -> DP/DP[-wh] VP
        vP/?x[+wh] -> DP[-wh] VP/?x[+wh]
        vP[+inv] -> DP[-wh] VP
        VP/?x[+wh] -> V DP/DP[+wh]
        VP -> V DP
            | V CP
            | V A
            | VP PP
            | V
        DP[-wh] -> D NP
                | NP
        NP -> N
            | A N
            | NP PP
        DP/DP[+wh] ->
        DP/DP[-wh] ->
        T[+empty] ->
        PP -> P DP
        C ->
    """

    pos2cat = { 
        'ADJ': 'A', 
        'ADP': 'P',
        'ADV': 'R', 
        'NOUN': 'N', 
        'AUX': 'T[-empty]', 
        'DET': 'D',
        'VERB': 'V', 
        'PROPN': 'DP[-wh]',
        'WP': 'DP[+wh]'
    } 

    copula = ['am', 'is', 'are', 'was', 'were', 'been']

    def __init__(self):
        self._rules = defaultdict(set)
        self._nonterminals: set[str] = set()

        self._read_basis()

    def update(self, tokens: list[str], tags: list[str]) -> None:
        for tag, token in zip(tags, tokens):
            terminal = f"'{token}'"
            if token in self.copula:
                self._add_rule('V', terminal)
            self._add_rule(tag, terminal)

    def export_parser(self) -> FeatureChartParser:
        grammar_str = self.export_str()
        feature_grammar = FeatureGrammar.fromstring(grammar_str)
        parser = FeatureChartParser(feature_grammar)

        return parser

    def export_str(self) -> str:
        output: list[str] = []
        output.append(f"% start {self.start}")
        for key in self._rules:
            products = list(self._rules[key])

            for n in range(len(products)):
                product = products[n]
                line = f"{key} -> {' '.join(product)}"

                output.append(line)

        out_str = '\n'.join(output)
        return out_str

    def _read_basis(self) -> None:
        lines = self.basis.strip().split('\n')
        basis = [line.strip() for line in lines]
        symbol = None
        product = None

        for line in basis:
            if line.strip() != '':
                if '->' in line:
                    left, right = line.split('->')
                    symbol = left.strip()
                    if right:
                        product = tuple(right.split())
                    else:
                        product = tuple()
                    product = tuple(symbol.strip() for symbol in product)
                else:
                    _, right = line.split('|')
                    product = tuple(right.split())
                    product = tuple(symbol.strip() for symbol in product)
                
                if symbol:
                    self._nonterminals.add(symbol)
                    self._nonterminals.update(product)
                    self._rules[symbol].add(product)
                else:
                    raise ValueError("Invalid basis.")

    def _add_rule(self, cat: str, token: str) -> None:
        self._rules[cat].add((token,))
        
    def _check_symbol(self, symbol: str) -> str | FeatStructNonterminal:
        if symbol in self._nonterminals:
            return FeatStructNonterminal(symbol)

        return symbol

    def _make_production(self, cat: str, product: tuple[str] | tuple[str, str]) -> Production:
        left = FeatStructNonterminal(cat)
        right = tuple(self._check_symbol(symbol) for symbol in product)

        production = Production(left, right)
        return production



class Parser:

    def __init__(self):
        self._grammar = Grammar()
        self._nlp = spacy.load('en_core_web_sm')
        self._parser = self._grammar.export_parser()

    def parse(self, raw_input: str):

        words = self._nlp(raw_input)
        tokens: list[str] = []
        tags: list[str] = []
        lemmas: dict[tuple[str,str],str] = dict()
        
        for word in words:
            token = word.text
            lemma = word.lemma_
            pos = word.pos_
            if pos == 'PRON':
                if word.tag_ == 'WP':
                    pos = word.tag_

            tag = self._grammar.pos2cat[pos]
            tokens.append(token)
            tags.append(tag)

            sym = tag.split('[')[0]

            if lemma == 'be':
                lemmas[(token,'V')] = lemma
                lemmas[(token,'T')] = lemma
            else:
                lemmas[(token,sym)] = lemma

        self._grammar.update(tokens, tags)
        self._parser = self._grammar.export_parser()
        trees = self._parser.parse(tokens)

        return trees, lemmas

    def repl(self):

        while ((raw_input := input('|- ')) != 'quit'):
            trees = self.parse(raw_input)
            for tree in trees:
                print(tree)

if __name__ == "__main__":
    parser = Parser()
    parser.repl()
