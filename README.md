
# English Formal Semantics Interpreter

This is a CLI for parsing and evaluating English sentences using the principles of formal semantics.

Tokenization is performed by integration with SpaCy.

## Features

- Parses basic English syntax (e.g. *"The cat sleeps."*)
- Converts sentences into logical forms using lambda calculus
- Evaluates truth in a model-theoretic semantics framework
- Interactive REPL and file mode
- Integration with spaCy for robust tokenization

## Usage

Sentences are interpreted as predicates interpreted against a model. 

A sentence ending with a period is a **declaration** that will modify the model
so that the sentence is true when interpreted against the model. 

A sentence ending with a question mark is a **query** that will return the truth
value or denotation of a sentence without modifying the model.

The interpreter can reason with syllogisms:

```
|> Socrates is a man.
|> Every man is mortal.
|> Is Socrates mortal?
Yes
|> Who is mortal?
Socrates
```

Additionally, it is possible to reference entities with definite description.

```
|> Aristotle is a philosopher.
|> The philosopher is Greek.
|> Who is Greek?
[Aristotle]
```

Wh-questions will return whichever answers have already been declared.

```
|> Aristotle is a philosopher.
|> Who is a philosopher?
[Aristotle]
```

There are three available flags.

In order to print the logical form, use the flag `--show-formulae`

```
|> --show-formulae
|> Aristotle is a man.
man(aristotle)
|> Every man is mortal.
@x[man(x) -> mortal(x)]
```

The display of formulae can be disabled by entering `hide-formulae`

Type `quit` to exit the program.

## Installation

### 1. Install Python, spaCy, and nltk

```
pip install nltk
pip install spacy
python -m spacy download en_core_web_sm
```

### 2. Clone and Build the Project
```
git clone https://github.com/ETYates/pysemantics
cd formal-semantics
dune build
```

## Running

### Start the REPL
```
python main.py
```
