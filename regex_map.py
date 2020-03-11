from collections import defaultdict
from typing import TypedDict, List, Optional, Dict
import json
import re
import copy


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


def map_word_to_entry(raw_word: str, regex_map: Dict[str, Entry]) -> Optional[Entry]:
    """
    Tries to map a string to an Entry.
    Handles ending `;` `.` and `,` (`a` `z` and `x`)
    Assumes default keyboard character mapping (so that, e.g., `z` and `.` are mirrored).

    :param raw_word: pattern ~ r'([A-Za-z,.;:<>\'-]+?)\'*$' , though I suppose this still kind of works with r'.*'
    :param regex_map: The dictionary of words grouped by their regexes {str: Entry}, to draw from.
    :return: A deep copy of the Entry, if it exists.
    """
    if len(raw_word) == 0:
        return

    # Accounting for a=; z=. and x=, possibly at end of word (differentiating, e.g. 'pix' vs 'pi,')
    grouped_word_match = re.match(r'(?P<root>.+?)[.,;]*$', raw_word)
    root = grouped_word_match.group('root')
    possible_word = raw_word
    while len(possible_word) >= len(root):
        regex: str = word_to_lc_regex(possible_word)
        entry: Optional[Entry] = regex_map.get(regex)
        if entry is not None:
            return copy.deepcopy(entry)
        else:
            possible_word = possible_word[:-1]
    # No matched, so return None.


def lowerize_symbols(raw_text: str) -> str:
    """Lower-caseify words, accounting for A=< Z=> and X=: """
    text = raw_text.lower()
    for upper, lower in capitalized_symbol_map.items():
        text = text.replace(upper, lower)
    return text


def word_to_lc_regex(word: str) -> str:
    """Lower-case regex mapping. e.g. "AARdvarK" -> "^[a;][a;][ru][dk][vn][a;][ru][dk]$" """
    lc_word = lowerize_symbols(word)  # I want the words to be regexed case-insensitively, but remain cased for lookup.
    regex = '^'
    for i in lc_word:
        regex += letter_regex_map.get(i, '[' + i + ']')  # Do I need to worry about "\" escaping for Qt?
    regex += '$'

    return regex


def create_regex_map(src: List, keep_capitals: List[bool], dest='regex_map.json'):
    """
    Takes a list of lists of dictionary words and converts it like,
    e.g.: {"^[a;][vn]$": {"default": "an", "words": ["an", "av"]}, [...]}
    then dumps to a big json file.

    :param src: List of source files of "{word}\n". Put in order of priority (first mapped word set as Entry default).
    :param keep_capitals: Defaults to / padded with False. Linked by index to src List.
    :param dest: Output file name.
    :return:
    """
    len_diff = len(src) - len(keep_capitals)
    if len_diff > 0:
        keep_capitals.extend([False] * len_diff)
    words = []

    for i in range(len(src)):
        with open(src[i]) as f:
            all_words = [line.rstrip() for line in f]
            if keep_capitals[i]:
                words.extend([wd for wd in all_words if wd not in words])
            else:
                words.extend([wd for wd in all_words if wd.islower() and wd not in words])

    regex_words = defaultdict(list)
    for word in words:
        regex = word_to_lc_regex(word)
        regex_words[regex].append(word)

    regex_map = dict()
    for regex, words in regex_words.items():
        regex_map[regex]: Entry = {'default': words[0], 'words': words}

    with open(dest, 'w') as f:
        json.dump(regex_map, f)


if __name__ == '__main__':
    create_regex_map(['/usr/share/dict/words'], [False])
