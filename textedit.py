import sys
import json
import re
from enum import Enum
from typing import Optional

from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QKeyEvent
from PySide2.QtWidgets import QApplication, QPlainTextEdit

from regex_map import word_to_regex, capitalized_symbol_map, Entry


class Mode(Enum):
    INSERT = 1
    WORDCHECK = 2


class MyPlainTextEdit(QPlainTextEdit):
    def __init__(self, regex_map: str = 'regex_map.json'):
        super().__init__()  # Pass parent?
        self.mode = Mode.INSERT
        with open(regex_map) as f:
            self.regex_map: dict = json.load(f)
            
    def lowerize_symbols(self, text: str) -> str:
        """Account for A=< Z=> and X=: """
        for upper, lower in capitalized_symbol_map.items():
            text = text.replace(upper, lower)
        return text

    def map_word(self, raw_word: str) -> Optional[str]:
        """
        Tries to map a string of non-whitespace chars to an actual word.
        Handles trailing `'` `"` `?` and `!`. Leading `'` and `"` assumed already stripped.
        Handles ending `;` `.` and `,` (`a` `z` and `x`)
        Preserves first-letter capitalization.
        Assumes default keyboard character mapping (so that, e.g., `z` and `.` are mirrored).

        :param raw_word: a string of non-whitespace chars, beginning with not(' or ")
        :return: the default mapped word, if found. Else, None.
        """
        is_capitalized = raw_word[0].isupper() or raw_word[0] in capitalized_symbol_map  # Want to keep capitalization in end word.
        word = self.lowerize_symbols(raw_word)

        end_stripped_match = re.match(r'(?P<end_stripped_word>.+?)[\'\"?!]*$', word)  # e.g. `'lkl'n.?!""` -> `'lkl'n.`
        unquoted_word = end_stripped_match.group('end_stripped_word')

        # Accounting for a=; z=. and x=, possibly at end of word (differentiating, e.g. 'pix' vs 'pi,')
        grouped_word_match = re.match(r'(?P<root>.+?)[.,;]*$', unquoted_word)
        root = grouped_word_match.group('root')
        possible_word = unquoted_word
        while len(possible_word) >= len(root):
            regex: str = word_to_regex(possible_word)
            entry: Optional[Entry] = self.regex_map.get(regex)
            if entry is not None:
                mapped_word: str = entry['default']
                if is_capitalized:
                    return mapped_word.capitalize()
                else:
                    return mapped_word
            else:
                possible_word = possible_word[:-1]
        # No matched, so return None.

    def process_previous_word(self):
        """
        Overwrites the word before the cursor with the default mapping, if said mapping exists.
        def: word = string of non-whitespace chars, not beginning with `'` or `"`, nor ending with `'`, `"`, `?`, or `!`
        """
        cursor = self.textCursor()
        text = cursor.block().text()[:cursor.positionInBlock()]  # Look b/w start of para and current pos.
        end_seq_match = re.search(r'(?P<lead_quotes>[\"\']*)(?P<raw_word>\S+)\s*$', text)  # e.g. `'"lk . jkln,.k  ` -> `jkln,.k  `
        if end_seq_match is None:  # No word to handle
            return

        match_len = len(end_seq_match[0]) - len(end_seq_match.group('lead_quotes'))  # how far back to send cursor
        word = self.map_word(end_seq_match.group('raw_word'))
        if word is None:  # Word not found in regex_map dictionary
            return

        # Replace the old word
        cursor.setPosition(cursor.position() - match_len)
        cursor.setPosition((cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
        cursor.insertText(word)

    def keyPressEvent(self, e: QKeyEvent):
        if self.mode == Mode.INSERT:
            if e.key() == Qt.Key_Space or e.key() == Qt.Key_Return:  # For some reason Return is handled before kRE capturing.
                self.process_previous_word()

            super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):
        if e.modifiers() == Qt.ControlModifier and (e.key() == Qt.Key_E or e.key() == Qt.Key_I):
            self.mode = Mode.WORDCHECK if self.mode == Mode.INSERT else Mode.INSERT
            return

        super().keyReleaseEvent(e)


if __name__ == "__main__":
    app = QApplication([])
    editor = MyPlainTextEdit()
    editor.show()
    sys.exit(app.exec_())