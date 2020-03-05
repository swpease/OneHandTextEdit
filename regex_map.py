from collections import defaultdict
from typing import TypedDict, List
import json


class Entry(TypedDict):
    default: str
    words: List[str]


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

capitalized_symbol_map = {
    '<': ',',
    '>': '.',
    ':': ';'
}


def word_to_regex(word: str) -> str:
    """Lower-case regex mapping. e.g. "AARdvarK" -> "^[a;][a;][ru][dk][vn][a;][ru][dk]$" """
    lc_word = word.lower()  # I want the words to be regexed case-insensitively, but remain cased for lookup.
    regex = '^'
    for i in lc_word:
        regex += letter_regex_map.get(i, '[' + i + ']')  # Do I need to worry about "\" escaping for Qt?
    regex += '$'

    return regex


def create_regex_map(src='/usr/share/dict/words', dest='regex_map.json'):
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
        regex_map[regex]: Entry = {'default': words[0], 'words': words}

    with open(dest, 'w') as f:
        json.dump(regex_map, f)


if __name__ == '__main__':
    create_regex_map()
