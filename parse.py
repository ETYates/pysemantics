# repository: pysemantics
# Author: Ethan Yates <ethan.t.yates@gmail.com>

from nltk.grammar import FeatureGrammar, FeatStructNonterminal
from nltk.parse.featurechart import FeatureChartParser
from collections import defaultdict
import spacy

"""
Custom classes made to wrap around nltk functions. The Grammar class takes an
initially specified grammar in the form of a string and stores the information
in a dictionary. The parser contains the grammar inside its own object
instantiation, which is updated upon every call. This process allows for
maximum coverage with minimum specification.
"""

class Grammar:
    """
    Represents the grammar to be used by the system. A minimal grammar is
    first specified in Grammar.basis as the fundamental behavior of the
    parser. 

    Only nonterminals are specified in this grammar--all terminal
    nodes (except traces) are only added after being parsed from input
    sentences. 

    The basis is specified in an initial string that is read
    into a dictionary data structure. Then, after every input, the grammar
    will be updated with the appropriate rules of the form NonTerm -> Term
    in order to capture the input as specified by the input lexemes. 

    The grammmar is updated by added new entries to the dictionary. This
    dictionary, every time it is updated, is then exported to a string
    which is then passed to the ready-made nltk functions to build a
    grammar object and a parser.
    """

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

        self._read_basis() # loads the base grammar

    def update(self, tokens: list[str], tags: list[str]) -> None:
        """
        Given a list of tokens and tags, process each respective token and tag
        into a production rule, and add it to the grammar.

        :param tokens: list of tokens representing the sentence. 
        :param tags: list of tags representing the nonterminal
            symbols for adding words to production rules
        """
        for tag, token in zip(tags, tokens):
            terminal = f"'{token}'"
            if token in self.copula:
                self._add_rule('V', terminal)
            self._add_rule(tag, terminal)

    def export_parser(self) -> FeatureChartParser:
        """
        Exports the grammar into a string and then passes the string
        to nltk.grammar.fromstring(). This returns a chart parser that
        is used to parser the next input.

        :returns parser: the nltk ChartParser that is used to parse
            input sentences
        """
        grammar_str = self.export_str()
        feature_grammar = FeatureGrammar.fromstring(grammar_str)
        parser = FeatureChartParser(feature_grammar)

        return parser

    def export_str(self) -> str:
        """
        Export the entries in the grammar dictionary to string form. This
        string is readable by nltk modules such as Grammar.fromstring()
        """
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
        """
        Read the initial string containing the base grammar specification and
        save the data into a dictionary.
        """
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
        """
        Add a single rule to the grammar.

        :param cat: grammatical category and non-term symbol
        :param token: the string of the word to be added as a
            terminal symbol
        """
        self._rules[cat].add((token,))
        
    def _check_symbol(self, symbol: str) -> str | FeatStructNonterminal:
        """Checks a given symbol string against a list containing all the
        non-terminal symbols in the grammar. 

        :param symbol: the input symbol
        """
        if symbol in self._nonterminals:
            return FeatStructNonterminal(symbol)

        return symbol


class Parser:
    """
    A wrapper class for an nltk FeatureChartParser. Contains a grammar,
    a parser, and a spacy object for performing the initial tokenization
    and tagging. Persistently updates the grammar from the new input,
    based on the tags and tokens in the spacy output.
    """

    def __init__(self):
        self._grammar = Grammar()
        self._nlp = spacy.load('en_core_web_sm')
        self._parser = self._grammar.export_parser()

    def parse(self, raw_input: str):
        """
        Takes an unprocessed string and processes it with spacy, adds the 
        produced lexical entries into the grammar, and uses the grammar
        to parse the input tokens.

        :param raw_input: a string provided by the user
        """

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
