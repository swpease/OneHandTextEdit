from collections import defaultdict
import re
import json

# Assumes default key mappings.
letter_regex_map = {
    'q': '[qp]',
    'p': '[qp]',
    'w': '[wo]',
    'o': '[wo]',
    'e': '[ei]',
    'i': '[ei]',
    'r': '[ru]',
    'u': '[ru]',
    't': '[ty]',
    'y': '[ty]',

    'a': '[a;]',
    ';': '[a;]',
    's': '[ls]',
    'l': '[ls]',
    'd': '[dk]',
    'k': '[dk]',
    'f': '[fj]',
    'j': '[fj]',
    'g': '[gh]',
    'h': '[gh]',

    'z': '[z.]',
    '.': '[z.]',
    'x': '[x,]',
    ',': '[x,]',
    'c': '[cm]',
    'm': '[cm]',
    'v': '[vn]',
    'n': '[vn]',
    'b': '[b]',

    '-': '-'
}


def word_to_regex(word: str) -> str:
    """Lower-case regex mapping. e.g. "AARdvarK" -> "^[a;][a;][ru][dk][vn][a;][ru][dk]$" """
    lc_word = word.lower()  # I want the words to be regexed case-insensitively, but remain cased for lookup.
    regex = '^'
    for i in lc_word:
        regex += letter_regex_map.get(i, '[' + i + ']')  # Do I need to worry about "\" escaping for Qt?
    regex += '$'

    return regex


def _create_regex_map(src='/usr/share/dict/words', dest='regex_map.json'):
    """
    Takes a builtin list of dictionary words and converts it like,
    e.g.: {"^[a;]$": {"default": "A", "words": ["A", "a"]}, [...]}
    then dumps to a big json file.
    """
    with open(src) as f:
        words = [line.rstrip() for line in f]

    regex_words = defaultdict(list)
    for word in words:
        regex = word_to_regex(word)
        regex_words[regex].append(word)

    regex_map = dict()
    for regex, words in regex_words.items():
        regex_map[regex] = {'default': words[0], 'words': words}

    with open(dest, 'w') as f:
        json.dump(regex_map, f)


if __name__ == '__main__':
    _create_regex_map()
