#!/usr/bin/env python3


import re
import os
import sys
from functools import reduce


# Not the best one, but it will do
# eBNF:
#   <entry> = <japanese>[ ]---[ ]<translation>
#   <japanese> = <word>{<word>}
#   <word> = <simple word>|<complex word>
#   <simple word> = <char>{<char>}|<control word>
#   <char> is any word symbol (\w)
#   <control word> = **
#   <complex word> = (<char>{<char>})[<simple word>{<simple word>}]


control_words = {
    '**': 'bold'
}

markup = {
    'semibold': {
        'opening_tag': '<span style="text-shadow: 0 0 0;">',
        'closing_tag': '</span>'
    },
    'bold': {
        'opening_tag': '<span style="font-weight: bold;">',
        'closing_tag': '</span>'
    }
}

#kana = '\u3040-\u30ff'
control_words_match_regex = '|'.join([re.escape(k) for k in control_words.keys()])
simple_word_match_regex = r'\w+|' + control_words_match_regex
complex_word_match_regex = r'\(\w+\)\[(?:' + simple_word_match_regex + r')+\]'
word_match_regex = simple_word_match_regex + '|' + complex_word_match_regex
trimmed_string = '\S|\S.*\S'
entry_regex = r'^\s*(' + trimmed_string + r')\s*---\s*(' + trimmed_string + r')\s*$'


def split_complex_word(complex_word):
    return complex_word[1:-1].split(')[')


def parse_entry(entry):
    def tokenize(text, regex):
        return re.findall(regex, text)

    def process_word(word):
        if word in control_words:
            return dict([('type', 'control'), ('value', control_words[word])])
        elif re.match(complex_word_match_regex, word) is not None:
            value, hint = split_complex_word(word)
            return dict([('type', 'complex_word'),
                         ('value', value),
                         ('hint', [process_word(w)
                                   for w in tokenize(hint, simple_word_match_regex)])])
        else:
            return dict([('type', 'simple_word'), ('value', word)])


    m = re.match(entry_regex, entry)
    if m is None:
        return None
    japanese, translation = m.groups()
    processed_japanese = [process_word(w)
                          for w in tokenize(japanese, word_match_regex)]
    processed_translation = [process_word(w)
                             for w in re.split('(%s)' % control_words_match_regex,
                                               translation)]
    return dict([('japanese', processed_japanese),
                 ('translation', processed_translation)])


ruby_template = '''<ruby>
<rb>%s</rb>
<rp>(</rp><rt>%s</rt><rp>)</rp>
</ruby>'''


def process_simple_item(item, state, prev_result=''):
    return prev_result + item['value']

def process_control_item(item, state, prev_result=''):
    if not item['value'] in markup:
        return prev_result
    name = item['value']
    state[name] = not state[name]
    return (prev_result +
            (markup[name]['opening_tag']
             if state[name]
             else markup[name]['closing_tag']))

def process_complex_item(item, state, prev_result=''):
    if not reduce(bool.__or__,
                  map(lambda x: x['type'] == 'control',
                      item['hint'])):
        return prev_result + (ruby_template % (item['value'], ''.join(item['hint'])))
    else:
        result = ''
        subresult = ''
        # TODO: refactor all these check for 'bold'
        # "Opening"
        if state['bold']:
            result += markup['bold']['closing_tag']
        # "Processing"
        if state['bold']:
            subresult += markup['bold']['opening_tag']
        actions = {
            'control': process_control_item,
            'simple_word': process_simple_item
        }
        for subitem in item['hint']:
            subresult = actions[subitem['type']](subitem, state, subresult)
        if state['bold']:
            subresult += markup['bold']['closing_tag']
        result += ruby_template % (markup['semibold']['opening_tag']
                                   + item['value']
                                   + markup['semibold']['closing_tag'],
                                   subresult)
        # "Closing"
        if state['bold']:
            result += markup['bold']['opening_tag']
        return prev_result + result

def make_reading(parsed_japanese):
    result = ''
    state = {'bold': False}
    actions = {
        'simple_word': process_simple_item,
        'control': process_control_item,
        'complex_word': process_complex_item
    }
    for item in parsed_japanese:
        result = actions[item['type']](item, state, result)
    return result


def make_translation(parsed_translation):
    result = ''
    state = {'bold': False}
    actions = {
        'simple_word': process_simple_item,
        'control': process_control_item
    }
    for item in parsed_translation:
        result = actions[item['type']](item, state, result)
    return result

def make_writing(parsed_japanese):
    result = ''
    for item in parsed_japanese:
        if item['type'] in ['simple_word', 'complex_word']:
            result += item['value']
    return result

whole_template = '''<center>
<div>%s</div>
<div>%s</div>
</center>'''


def main(argv):
    if len(argv) < 3:
        print('Usage: python3 %s <input-file> <card-file>' % argv[0])
        exit()
    inputfile = argv[1]
    cardfile = argv[2]
    with open(inputfile) as f, open(cardfile, 'w') as cdfile:
        for line in f.readlines():
            ast = parse_entry(line)
            if ast is None:
                print('Строка \'%s\' имеет неправильный формат.' % line)
                continue
            writing = make_writing(ast['japanese'])
            translation = make_translation(ast['translation'])
            whole = whole_template % (make_reading(ast['japanese']), translation)
            # strip caret returns 
            whole = whole.replace('\n', '').replace('"', '""')
            cdfile.write('<div>%s</div>\t%s\t"%s"\t\r\n' % (writing, translation, whole))


if __name__ == '__main__':
    exit(main(sys.argv))
