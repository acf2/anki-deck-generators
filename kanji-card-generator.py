#!/usr/bin/env python3


import re
import os
import sys
from functools import reduce


kanji = "[\u4e00-\u9faf]"
hiragana = "[\u3040-\u309f\\(\\)]" # + parentheses for ending
katakana = "[\u30a0-\u30ff・]" # + onyomi usual separator
punctuation = "[,、](?![^\[\]]*\])"


trimmed_string = r"(?:[^\]\s]|[^\]\s][^\]]*[^\]\s])"
translation = r"(?:\s*\[" + trimmed_string + r"\])"


def make_csl(character, with_tips=None):
    """Function for generating CSV and CSV-with-optional-translations matching regexes"""
    if with_tips is None or with_tips == False:
        return (r"\s*((?:%s+%s\s*)*%s+)\s*") % (character, punctuation, character)
    else:
        return (r"\s*((?:%s+%s?%s\s*)*%s+%s?)\s*") % (character, translation, punctuation, character, translation)


# Groups: 0 - kanji, 1 - translation, 2 - CSV of onyomi, 3 - CSV of kunyomi
atomic_entry = r'^\s*(%s)\s*\[(%s)\]\s*:%s(?::%s)?$' % (kanji, trimmed_string, make_csl(katakana), make_csl(hiragana))
# Groups: 0 - kanji, 1 - CSV of onyomi with translations, 2 - CSV of kunyomi with translations
complex_entry = r'^\s*(%s)\s*:%s(?::%s)?$' % (kanji, make_csl(katakana, True), make_csl(hiragana, True))


def parse_entry(entry):
    def parse_atomic_entry(match):
        result = {
            'type': 'atomic',
            'kanji': {},
            'onyomi': [],
            'kunyomi': []
        }
        result['kanji']['char'] = match.groups()[0]
        result['kanji']['translation'] = match.groups()[1]
        result['onyomi'] = [w for w in re.split(punctuation + '+', match.groups()[2])]
        if len(match.groups()) > 3 and match.groups()[3] is not None:
            result['kunyomi'] = [w for w in re.split(punctuation + '+', match.groups()[3])]
        return result

    def parse_complex_entry(match):
        result = {
            'type': 'complex',
            'kanji': {},
            'onyomi': [],
            'kunyomi': []
        }
        result['kanji']['char'] = match.groups()[0]
        for word in [w for w in re.split(punctuation, match.groups()[1])]:
            m = re.match('(%s+)\s*(%s)?' % (katakana, translation), word)
            if len(m.groups()) < 2 or m.groups()[1] is None:
                result['onyomi'].append({'reading': m.groups()[0]})
            else:
                result['onyomi'].append({'reading': m.groups()[0], 'translation': m.groups()[1][1:-1]})
        if len(match.groups()) > 2 and match.groups()[2] is not None:
            for word in [w for w in re.split(punctuation, match.groups()[2])]:
                m = re.match('(%s+)\s*(%s)?' % (hiragana, translation), word)
                if len(m.groups()) < 2 or m.groups()[1] is None:
                    result['kunyomi'].append({'reading': m.groups()[0]})
                else:
                    result['kunyomi'].append({'reading': m.groups()[0], 'translation': m.groups()[1][1:-1]})
        return result

    m = re.match(atomic_entry, entry)
    if m is not None:
        result = parse_atomic_entry(m)
    else:
        m = re.match(complex_entry, entry)
        if m is not None:
            result = parse_complex_entry(m)
        else:
            result = None
    return result


# Two parameters: kanji and table contents
kanji_table_template = '''<table>
  <tr>
    <td style="font-size: 2em; padding-right: 0.5em;">%s</td>
    <td><table>
      %s</table></td>
  </tr>
</table>
'''

# Two parameters: kunyomi/onyomi and translation
reading_row_template = '''<tr>
        <td>%s</td>
        <td></td>
        <td><center>%s</center></td>
      </tr>
      '''

# One parameter: whole kanji translation
center_row_template = '''<tr>
        <td style="width: 5em;"><hr></td>
        <td style="padding-left: 2.5em;"></td>
        <td><center>%s</center></td>
      </tr>
      '''


def construct_table(ast):
    if not 'type' in ast:
        return None
    result = None
    if ast['type'] == 'atomic':
        rows = []
        rows += [reading_row_template % (r, '') for r in ast['onyomi']]
        rows.append(center_row_template % ast['kanji']['translation'])
        rows += [reading_row_template % (r, '') for r in ast['kunyomi']]
        result = kanji_table_template % (ast['kanji']['char'], ''.join(rows))
    elif ast['type'] == 'complex':
        rows = []
        rows += [reading_row_template % (r['reading'], r['translation'] if 'translation' in r else '') for r in ast['onyomi']]
        rows.append(center_row_template % '')
        rows += [reading_row_template % (r['reading'], r['translation'] if 'translation' in r else '') for r in ast['kunyomi']]
        result = kanji_table_template % (ast['kanji']['char'], ''.join(rows))
    return result


def main(argv):
    if len(argv) < 3:
        if len(argv) == 2 and argv[1] == 'regexes':
            print("Atomic: %s\n\nComplex: %s" % (atomic_entry, complex_entry))
            exit()
        print("Usage: python3 %s <input-file> <output-dir>" % argv[0])
        exit()
    filename = argv[1]
    directory = argv[2]
    if not os.path.exists(directory):
        os.mkdir(directory)
    with open(filename) as f:
        i = 0
        for line in f.readlines():
            ast = parse_entry(line)
            if ast is None:
                print("Строка '%s' имеет неправильный формат." % line)
                continue
            name = ast['kanji']['char']
            if ast['type'] == 'atomic':
                translations = ast['kanji']['translation']
            elif ast['type'] == 'complex':
                translations = ', '.join(list(map(lambda x: x['translation'],
                                                  filter(lambda x: 'translation' in x,
                                                         ast['onyomi'] +
                                                         ast['kunyomi'] if 'kunyomi' in ast else []))))
            table = construct_table(ast)
            with open(os.path.join(directory, ('%03d ' % i) + name + '.txt'), 'w') as kjfile:
                kjfile.write(name+'\r\n')
                kjfile.write(translations+'\r\n')
                kjfile.write(table+'\r\n')
            i += 1


if __name__ == "__main__":
    exit(main(sys.argv))