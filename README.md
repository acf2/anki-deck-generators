# anki-deck-generators
Generators of anki decks for everything

## Formats of sources and decks

### Kanji
Format of source:
```BNF
<File> ::= <Entry>\n<Entry>\n . . . \n<Entry>\n
<Entry> ::= <Simple> | <Complex>
<Simple> ::= <Kanji char>[<Translation>]:<Simple onyomi list>:<Simple kunyomi list>
<Simple onyomi list> ::= <empty>|<Onyomi><Punctuation mark> . . . <Punctuation mark><Onyomi>
<Simple kunyomi list> ::= <empty>|<Kunyomi><Punctuation mark> . . . <Punctuation mark><Kunyomi>
<Complex> ::= <Kanji char>:<Translated onyomi list>:<Translated kunyomi list>
#TODO LATER
```
