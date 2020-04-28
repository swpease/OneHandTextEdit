from collections import defaultdict
from typing import List, Optional
import json
import re
import os
import copy


# Assumes default key mappings.
letter_regex_map = {
    'q': 'q',
    'p': 'q',
    'w': 'w',
    'o': 'w',
    'e': 'e',
    'i': 'e',
    'r': 'r',
    'u': 'r',
    't': 't',
    'y': 't',

    'a': 'a',
    ';': 'a',
    's': 's',
    'l': 's',
    'd': 'd',
    'k': 'd',
    'f': 'f',
    'j': 'f',
    'g': 'g',
    'h': 'g',

    'z': 'z',
    '.': 'z',
    'x': 'x',
    ',': 'x',
    'c': 'c',
    'm': 'c',
    'v': 'v',
    'n': 'v',
    'b': 'b',

    'Q': 'q',
    'P': 'q',
    'W': 'w',
    'O': 'w',
    'E': 'e',
    'I': 'e',
    'R': 'r',
    'U': 'r',
    'T': 't',
    'Y': 't',

    'A': 'a',
    ':': 'a',
    'S': 's',
    'L': 's',
    'D': 'd',
    'K': 'd',
    'F': 'f',
    'J': 'f',
    'G': 'g',
    'H': 'g',

    'Z': 'z',
    '>': 'z',
    'X': 'x',
    '<': 'x',
    'C': 'c',
    'M': 'c',
    'V': 'v',
    'N': 'v',
    'B': 'b',
}

capitalized_symbol_map = {
    '<': ',',
    '>': '.',
    ':': ';'
}

letter_to_symbol_map = {
    'x': ',',
    'z': '.',
    'a': ';',
    'X': '<',
    'Z': '>',
    'A': ':'
}


def _handle_entry_caps(entry: Entry) -> Entry:
    """e.g. ["Fin", "fin", "fen"] --> ["Fin", "fin", "fen", "Fen"] """
    capitalized_words = [wd.capitalize() for wd in entry['words']]
    deduped_cap_words = []
    for wd in capitalized_words:
        if wd not in deduped_cap_words:
            deduped_cap_words.append(wd)
    deduped_words = [wd for wd in deduped_cap_words if wd not in entry['words']]
    entry['words'].extend(deduped_words)

    return entry


def set_entry_default(word: str, regex_map) -> bool:
    """
    Sets word as default for its Entry, if it exists. Mutates the regex_map.

    :param word: Presumed to derive from `PlainTextEdit.get_word_under_cursor()`
    :param regex_map: Dictionary to modify.
    :return: True if regex_map modified, else False.
    """
    if len(word) == 0:
        return False

    base_word = word
    regex: str = word_to_lc_regex(base_word)
    entry = regex_map.get(regex)
    if entry is None:
        # check if possessive
        if base_word.endswith('\'s'):
            base_word = base_word[:-2]
            regex: str = word_to_lc_regex(base_word)
            entry = regex_map.get(regex)
        if entry is None:
            return False

    uncapitalized_word = base_word[0].lower() if len(base_word) == 1 else base_word[0].lower() + base_word[1:]
    if base_word in entry['words']:
        entry['default'] = base_word
    # for auto-caps cases
    elif uncapitalized_word in entry['words']:
        entry['default'] = uncapitalized_word
    # user forced something in
    else:
        entry['default'] = base_word
        entry['words'].append(base_word)

    return True


def map_word_to_entry(raw_word: str, regex_map):
    """
    Tries to map a word to an Entry.

    :param raw_word: pattern ~ r'([A-Za-z\'-]+)$' , w/o leading or trailing `'`
    :param regex_map: The dictionary of words grouped by their regexes {str: Entry}, to draw from.
    :return: A deep copy of the Entry, if it exists, with upper case options appended for all lower cased words.
    """
    if len(raw_word) == 0:
        return

    regex: str = word_to_lc_regex(raw_word)
    entry = regex_map.get(regex)
    if entry is not None:
        entry_copy = copy.deepcopy(entry)
        return _handle_entry_caps(entry_copy)

    # No word found. Check for possessives.
    if raw_word.endswith('\'s'):  # You could eff this up if you manually overwrote s with l.
        regex: str = word_to_lc_regex(raw_word[:-2])
        entry = regex_map.get(regex)
        if entry is not None:
            entry_copy = copy.deepcopy(entry)
            entry_copy['default'] = entry_copy['default'] + "'s"
            possessive_words = [word + "'s" for word in entry_copy['words']]
            entry_copy['words'] = possessive_words
            return _handle_entry_caps(entry_copy)

    return  # No matched, so return None.


def map_string_to_word(raw_word: str, regex_map) -> Optional[str]:
    """
    Tries to map a string to an Entry, and takes its 'default' plus necessary punctuation.
    Assumes default keyboard character mapping (so that, e.g., `z` and `.` are mirrored).

    :param raw_word: pattern ~ r'([A-Za-z,.;:<>\'-]+)$' , w/o leading or trailing `'`
    :param regex_map: The dictionary of words grouped by their regexes {str: Entry}, to draw from.
    :return: The default value of the matched Entry, if it exists, plus trailing r'[,.;]*' punctuation.
    """
    if len(raw_word) == 0:
        return

    is_capitalized = raw_word[0].isupper() or raw_word[0] in capitalized_symbol_map

    symbolized_word = raw_word
    # For left-handers. Gets coerced back as needed later.
    for letter, symbol in letter_to_symbol_map.items():
        symbolized_word = symbolized_word.replace(letter, symbol)

    # Accounting for a=; z=. and x=, possibly at end of word (differentiating, e.g. 'pix' vs 'pi,')
    grouped_word_match = re.match(r'(?P<root>.+?)[.,;<>:]*$', symbolized_word)
    root = grouped_word_match.group('root')
    possible_word = symbolized_word
    tail = ''
    while len(possible_word) >= len(root):
        regex: str = word_to_lc_regex(possible_word)
        entry = regex_map.get(regex)
        if entry is not None:
            default = entry['default']
            word = default + tail
            if is_capitalized:
                return word.capitalize()
            else:
                return word
        else:
            tail = possible_word[-1] + tail
            possible_word = possible_word[:-1]

    # No word found. Check for possessives.
    tail = tail[1:]  # Overshot in above while loop.
    if re.search(r'\'[sl]$', root) is not None:
        regex: str = word_to_lc_regex(root[:-2])
        entry = regex_map.get(regex)
        if entry is not None:
            default = entry['default']
            word = default + "'s" + tail
            if is_capitalized:
                return word.capitalize()
            else:
                return word

    return  # No matched, so return None.


def add_word_to_dict(word: str, regex_map) -> bool:
    """
    Add a word to a regex map dictionary. Mutates the regex_map to include word.
    :param word: Word to add to dictionary.
    :param regex_map: Dictionary to add word to.
    :return: True if word added. False if already exists.
    """
    regex = word_to_lc_regex(word)
    entry = regex_map.get(regex)
    if entry is not None:
        if word not in entry['words']:
            entry['words'].append(word)
            return True
    else:
        regex_map[regex] = {'default': word, 'words': [word]}
        return True


def del_word_from_dict(word: str, regex_map) -> bool:
    """
    Deletes a word from a regex map dictionary. Mutates the regex_map to remove word.
    :param word: Word to remove from dictionary.
    :param regex_map: Dictionary to remove word from.
    :return: True if word removed. False if not in dictionary.
    """
    regex = word_to_lc_regex(word)
    entry = regex_map.get(regex)

    if entry is None or word not in entry['words']:
        return False
    else:
        entry['words'].remove(word)
        if len(entry['words']) == 0:
            del regex_map[regex]
        elif entry['default'] == word:
            entry['default'] = entry['words'][0]
        return True


def word_to_lc_regex(word: str) -> str:
    """Lower-case regex mapping. e.g. "AARdvarK" -> "^[a;][a;][ru][dk][vn][a;][ru][dk]$"

       Note that these regexes are basically used as lookup keys, not for actual regexing.
       For instance, the caret and backslash characters, as is, will yield incorrect / invalid patterns.
    """
    regex = ''
    for i in word:
        regex += letter_regex_map.get(i, i)  # Do I need to worry about "\" escaping for Qt?

    return regex


def create_regex_map(src: List[str], keep_capitals: List[bool], dest='regex_map.json'):
    """
    Takes a list of lists of dictionary words and converts it like,
    e.g.: {"^[a;][vn]$": {"default": "an", "words": ["an", "av"]}, [...]}
    then dumps to a big json file.

    :param src: List of source files of "{word}\n". Put in order of priority (first mapped word set as Entry default).
    :param keep_capitals: Defaults to / padded with True. Linked by index to src List.
    :param dest: Output file name.
    :return:
    """
    len_diff = len(src) - len(keep_capitals)
    if len_diff > 0:
        print("Padding `keep_capitals` arg with `True`")
        keep_capitals.extend([True] * len_diff)

    words = {}
    for i in range(len(src)):
        with open(src[i]) as f:
            all_words = [line.rstrip() for line in f]
            if keep_capitals[i]:
                for wd in all_words:
                    words[wd] = 1  # Values are irrelevant.
            else:
                for wd in all_words:
                    if wd.islower():
                        words[wd] = 1

    regex_words = defaultdict(list)
    for word in list(words):  # Python 3.7+ preserves dict insertion order.
        regex = word_to_lc_regex(word)
        regex_words[regex].append(word)

    regex_map = dict()
    for regex, words in regex_words.items():
        regex_map[regex] = {'default': words[0], 'words': words}

    with open(dest, 'w') as f:
        json.dump(regex_map, f)


if __name__ == '__main__':
    # maybe see: http://www.kilgarriff.co.uk/bnc-readme.html
    #  src = https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Contemporary_fiction (Mar 2020)
    #  src = https://www.english-corpora.org/coca/ (pre Mar 2020 update)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    common_words_path = os.path.join(dir_path, "common_words.txt")
    COCA_path = os.path.join(dir_path, "COCA.txt")
    contractions = os.path.join(dir_path, "contractions.txt")
    countries_demonyms = os.path.join(dir_path, "countries_demonyms.txt")
    months_and_days = os.path.join(dir_path, 'months_and_days.txt')
    plurals = os.path.join(dir_path, 'BNC_curated_plurals.txt')
    create_regex_map([common_words_path, COCA_path, contractions, countries_demonyms, months_and_days, plurals,
                      '/usr/share/dict/words', '/usr/share/dict/propernames'],
                     [True, True, True, True, True, False,
                      False, True])
