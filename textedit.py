import sys
import json
import re
from enum import Enum
from typing import Optional

from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QKeyEvent, QColor
from PySide2.QtWidgets import QApplication, QPlainTextEdit, QTextEdit

from regex_map import map_word_to_entry, capitalized_symbol_map, Entry


class Mode(Enum):
    INSERT = 1
    WORDCHECK = 2


class MyPlainTextEdit(QPlainTextEdit):
    def __init__(self, regex_map: str = 'regex_map.json'):
        super().__init__()  # Pass parent?

        self.mode = Mode.INSERT
        self.wordcheck_cursor: QTextCursor = self.textCursor()
        self.wordcheck_entry: Optional[Entry] = None

        self.cursorPositionChanged.connect(self.handle_cursor_position_changed)

        with open(regex_map) as f:
            self.regex_map: dict = json.load(f)

    def next_word_replace(self):
        pass

    def get_word_under_cursor(self, cursor: QTextCursor):
        """
        A word is ~ r'[A-Za-z\'-]+', where leading / trailing `'` are stripped or blocking
        e.g. "'h'i'" w/ cursor at 0 returns ("", ""), cursor at 1 returns ("", "h'i")
        :param cursor:
        :return: Tuple(front part, back part)
        """
        front_text = cursor.block().text()[:cursor.positionInBlock()]
        back_text = cursor.block().text()[cursor.positionInBlock():]

        # strip leading quotes
        raw_front_match = re.search(r'(?P<junk>\'*)(?P<raw_front>[A-Za-z,.;:<>\'-]*?)$', front_text)
        raw_front_word = raw_front_match.group('raw_front')
        # strip trailing quotes
        raw_back_match = re.search(r'^(?P<raw_back>[A-Za-z,.;:<>\'-]*)', back_text)
        raw_back_word = raw_back_match.group('raw_back')
        pre_back_match = re.search(r'^(?P<pre_back>[A-Za-z,.;:<>\'-]*?)(?P<junk>\'*)$', raw_back_word)
        pre_back_word = pre_back_match.group('pre_back')

        if len(pre_back_word) == 0:
            end_quotes_match = re.search(r'(?P<end_quotes>\'*)$', raw_front_word)
            if len(end_quotes_match.group('end_quotes')) > 0:  # Not inside a word.
                front_word = ''
            else:
                front_word = raw_front_word
        else:
            front_word = raw_front_word
        if len(front_word) == 0:
            lead_quotes_match = re.search(r'^(?P<lead_quotes>\'*)', pre_back_word)
            if len(lead_quotes_match.group('lead_quotes')) > 0:  # Not inside a word.
                back_word = ''
            else:
                back_word = pre_back_word
        else:
            back_word = pre_back_word

        return (front_word, back_word)

    def handle_cursor_position_changed(self):
        if self.mode == Mode.WORDCHECK:
            self.wordcheck_cursor = self.textCursor()
            front_word, back_word = self.get_word_under_cursor(self.wordcheck_cursor)
            word = front_word + back_word
            self.wordcheck_entry = map_word_to_entry(word, self.regex_map)

            self.wordcheck_cursor.setPosition(self.wordcheck_cursor.position() - len(front_word))
            self.wordcheck_cursor.setPosition((self.wordcheck_cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
            self.highlight_word(self.wordcheck_cursor, self.wordcheck_entry)

    def highlight_word(self, cursor: QTextCursor, entry: Optional[Entry]):
        selection = QTextEdit.ExtraSelection()
        normal_color = QColor(Qt.yellow).lighter()
        missing_color = QColor(Qt.magenta).lighter()
        default_color = QColor(Qt.green).lighter()

        if entry is None:
            selection.format.setBackground(missing_color)
        # TODO edge cases of capitals.
        elif entry['default'] == cursor.selection().toPlainText():
            selection.format.setBackground(default_color)
        else:
            selection.format.setBackground(normal_color)

        selection.cursor = cursor

        self.setExtraSelections([selection])

    def process_previous_word(self):
        """Overwrites the word before the cursor with the default mapping, if said mapping exists. """
        cursor = self.textCursor()
        text = cursor.block().text()[:cursor.positionInBlock()]  # Look b/w start of para and current pos.
        end_seq_match = re.search(r'(?P<lead_symbols>[^\sA-Za-z,.;:<>-]*)(?P<raw_word>[A-Za-z,.;:<>\'-]+?)(?P<end>[^A-Za-z,.;:<>-]*)$', text)
        if end_seq_match is None:  # No word to handle
            return

        match_len = len(end_seq_match[0]) - len(end_seq_match.group('lead_symbols'))  # how far back to send cursor
        raw_word = end_seq_match.group('raw_word')
        is_capitalized = raw_word[0].isupper() or raw_word[0] in capitalized_symbol_map
        entry = map_word_to_entry(raw_word, self.regex_map)
        if entry is None:  # Word not found in regex_map dictionary
            return
        else:
            word: str = entry['default']
            if is_capitalized:
                word = word.capitalize()

        # Replace the old word
        cursor.setPosition(cursor.position() - match_len)
        cursor.setPosition((cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
        cursor.insertText(word)

    def handle_wordcheck_key_events(self, e: QKeyEvent):
        """
        Remaps key events to their Wordcheck mode equivalents. Eats all events except arrow keys.

        :param e: The key event to remap. Assumes e.modifiers() == Qt.NoModifier.
        :return:
        """
        if e.key() in [Qt.Key_S, Qt.Key_H]:
            mapped_e = QKeyEvent(e.type(), Qt.Key_Left, Qt.AltModifier,
                                 autorep=e.isAutoRepeat(), count=e.count())
            QApplication.sendEvent(self, mapped_e)
        elif e.key() in [Qt.Key_G, Qt.Key_L]:
            mapped_e = QKeyEvent(e.type(), Qt.Key_Right, Qt.AltModifier,
                                 autorep=e.isAutoRepeat(), count=e.count())
            QApplication.sendEvent(self, mapped_e)
        elif e.key() in [Qt.Key_F, Qt.Key_J]:
            mapped_e = QKeyEvent(e.type(), Qt.Key_Down, Qt.NoModifier,
                                 autorep=e.isAutoRepeat(), count=e.count())
            QApplication.sendEvent(self, mapped_e)
        elif e.key() in [Qt.Key_D, Qt.Key_K]:
            mapped_e = QKeyEvent(e.type(), Qt.Key_Up, Qt.NoModifier,
                                 autorep=e.isAutoRepeat(), count=e.count())
            QApplication.sendEvent(self, mapped_e)

        elif e.key() in [Qt.Key_R, Qt.Key_U] and e.type() == QKeyEvent.KeyPress:
            self.next_word_replace()

        elif e.key() in [Qt.Key_Right, Qt.Key_Left, Qt.Key_Up, Qt.Key_Down]:
            if e.type() == QKeyEvent.KeyPress:
                super().keyPressEvent(e)
            elif e.type() == QKeyEvent.KeyRelease:
                super().keyReleaseEvent(e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.modifiers() == Qt.ControlModifier and e.key() in [Qt.Key_E, Qt.Key_I]:
            self.mode = Mode.WORDCHECK if self.mode == Mode.INSERT else Mode.INSERT

        elif self.mode == Mode.INSERT:
            if e.key() in [Qt.Key_Space, Qt.Key_Return, Qt.Key_Slash] and e.modifiers() == Qt.NoModifier:
                self.process_previous_word()
            super().keyPressEvent(e)

        elif self.mode == Mode.WORDCHECK:
            if e.modifiers() == Qt.NoModifier:  # Could be an issue if slash is remapped to be hidden under a modifier.
                self.handle_wordcheck_key_events(e)
            elif e.modifiers() != Qt.ShiftModifier:  # Eat shift-modified keys.
                super().keyPressEvent(e)

        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):
        if self.mode == Mode.WORDCHECK:
            if e.modifiers() == Qt.NoModifier:
                self.handle_wordcheck_key_events(e)
            elif e.modifiers() != Qt.ShiftModifier:  # Eat shift-modified keys.
                super().keyReleaseEvent(e)
        else:
            super().keyReleaseEvent(e)


if __name__ == "__main__":
    app = QApplication([])
    editor = MyPlainTextEdit()
    editor.show()
    sys.exit(app.exec_())
