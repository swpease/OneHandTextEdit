import sys
import json
import re
from enum import Enum
from typing import Optional, Dict

from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QKeyEvent, QColor
from PySide2.QtWidgets import QApplication, QPlainTextEdit, QTextEdit

from OHTE.regex_map import map_word_to_entry, map_string_to_word, letter_to_symbol_map, Entry


class Mode(Enum):
    INSERT = 1
    WORDCHECK = 2


class MyPlainTextEdit(QPlainTextEdit):
    def __init__(self, regex_map: Dict[str, Entry]):
        super().__init__()  # Pass parent?

        self.regex_map = regex_map
        self.mode = Mode.INSERT
        self.wordcheck_cursor: QTextCursor = self.textCursor()
        self.wordcheck_entry: Optional[Entry] = None
        self.entry_idx = 0
        self.autocaps = True

        self.cursorPositionChanged.connect(self.handle_cursor_position_changed)

    def next_word_replace(self):
        next_word = self.wordcheck_entry['words'][self.entry_idx % len(self.wordcheck_entry['words'])]
        self.wordcheck_cursor.insertText(next_word)
        self.wordcheck_cursor.setPosition(self.wordcheck_cursor.position() - len(next_word))
        self.wordcheck_cursor.setPosition((self.wordcheck_cursor.position() + len(next_word)), mode=QTextCursor.KeepAnchor)
        self.highlight_word(self.wordcheck_cursor, self.wordcheck_entry)

    def correct_index(self):
        """Pickup where you left off so the list cycling is sane."""
        if self.wordcheck_entry is not None:
            try:
                # TODO: adjust for caps?
                self.entry_idx = self.wordcheck_entry['words'].index(self.wordcheck_cursor.selection().toPlainText())
            except ValueError as e:
                self.entry_idx = 0
        else:
            self.entry_idx = 0

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
        raw_front_match = re.search(r'(?P<junk>\'*)(?P<raw_front>[A-Za-z\'-]*?)$', front_text)
        raw_front_word = raw_front_match.group('raw_front')
        # strip trailing quotes
        raw_back_match = re.search(r'^(?P<raw_back>[A-Za-z\'-]*)', back_text)
        raw_back_word = raw_back_match.group('raw_back')
        pre_back_match = re.search(r'^(?P<pre_back>[A-Za-z\'-]*?)(?P<junk>\'*)$', raw_back_word)
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

    def setup_wordcheck_for_word_under_cursor(self):
        if self.mode == Mode.WORDCHECK:
            self.wordcheck_cursor = self.textCursor()
            front_word, back_word = self.get_word_under_cursor(self.wordcheck_cursor)
            word = front_word + back_word
            self.wordcheck_entry = map_word_to_entry(word, self.regex_map)

            self.wordcheck_cursor.setPosition(self.wordcheck_cursor.position() - len(front_word))
            self.wordcheck_cursor.setPosition((self.wordcheck_cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
            self.highlight_word(self.wordcheck_cursor, self.wordcheck_entry)
            self.correct_index()

    def handle_cursor_position_changed(self):
        if self.mode == Mode.WORDCHECK:
            self.setup_wordcheck_for_word_under_cursor()

    def highlight_word(self, cursor: QTextCursor, entry: Optional[Entry]):
        selection = QTextEdit.ExtraSelection()
        normal_color = QColor(Qt.yellow).lighter()
        missing_color = QColor(Qt.magenta).lighter()
        default_color = QColor(Qt.green).lighter()

        if entry is None:
            selection.format.setBackground(missing_color)
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
        # Last line of Pattern matches closing parens of moderate complexity. Need to coerce post-parens punctuation.
        word_pattern = re.compile(r'''(?P<lead_symbols>[^\sA-Za-z,.;:<>]*)
                                      (?P<raw_word>[A-Za-z,.;:<>\'-]+?)
                                      (?P<end>[^A-Za-z,.;:<>]*|
                                      [!?\'"]*[]})]+[\'"]*(?P<end_punct_and_space>[.,;:azxA]+\s*))$''', re.X)
        end_seq_match = word_pattern.search(text)
        if end_seq_match is None:  # No word to handle
            return

        # Handling closing parens
        end_punct_and_space = end_seq_match.group('end_punct_and_space')
        if end_punct_and_space is not None:
            paren_cursor = self.textCursor()
            converted_string = ''
            for c in end_punct_and_space:
                converted_string += letter_to_symbol_map.get(c, c)
            paren_cursor.setPosition(paren_cursor.position() - len(converted_string), mode=QTextCursor.KeepAnchor)
            paren_cursor.insertText(converted_string)

        # Handling word
        match_len = len(end_seq_match[0]) - len(end_seq_match.group('lead_symbols'))  # how far back to send cursor
        raw_word = end_seq_match.group('raw_word')
        word = map_string_to_word(raw_word, self.regex_map)
        if word is None:  # Word not found in regex_map dictionary
            return

        # autocaps
        if self.autocaps:
            autocaps_match = re.search(r'(?P<prev_word>\S*?)(?P<junk>[\'\"]*)(?P<whitespace>\s*?)(?P<cur_word>\S+)$', text)
            if autocaps_match is not None:
                prev_word = autocaps_match.group('prev_word')
                if len(prev_word) == 0 or prev_word.endswith(('.', '?', '!')):
                    word = word.capitalize()

        # Replace the old word
        cursor.setPosition(cursor.position() - match_len)
        cursor.setPosition((cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
        cursor.insertText(word)

    def handle_wordcheck_key_events(self, e: QKeyEvent):
        """
        Remaps key events to their Wordcheck mode equivalents. Only handles NoModifier and ShiftModifier events.

        :param e: The key event to remap.
        :return:
        """
        if e.key() in [Qt.Key_Delete, Qt.Key_Backspace,
                       Qt.Key_Comma, Qt.Key_Period, Qt.Key_Semicolon,
                       Qt.Key_Colon, Qt.Key_Less, Qt.Key_Greater]:
            if e.type() == QKeyEvent.KeyPress:
                super().keyPressEvent(e)
            elif e.type() == QKeyEvent.KeyRelease:
                super().keyReleaseEvent(e)

        elif e.modifiers() == Qt.NoModifier:
            if e.key() in [Qt.Key_S, Qt.Key_H]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Left, Qt.AltModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() in [Qt.Key_G, Qt.Key_L]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Right, Qt.AltModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() in [Qt.Key_F, Qt.Key_J]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Down, Qt.KeypadModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() in [Qt.Key_D, Qt.Key_K]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Up, Qt.KeypadModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() in [Qt.Key_C, Qt.Key_N]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Left, Qt.KeypadModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() in [Qt.Key_V, Qt.Key_M]:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Right, Qt.KeypadModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)

            elif e.key() in [Qt.Key_R, Qt.Key_U] and e.type() == QKeyEvent.KeyPress:
                if self.wordcheck_entry is not None:
                    self.entry_idx += 1
                    self.next_word_replace()
            elif e.key() in [Qt.Key_E, Qt.Key_I] and e.type() == QKeyEvent.KeyPress:
                if self.wordcheck_entry is not None:
                    self.entry_idx -= 1
                    self.next_word_replace()

            elif e.key() in [Qt.Key_A, Qt.Key_Z, Qt.Key_X]:
                if e.key() == Qt.Key_A:
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Semicolon, Qt.NoModifier, text=';',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)
                elif e.key() == Qt.Key_Z:
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Period, Qt.NoModifier, text='.',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)
                else:  # Key_X
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Comma, Qt.NoModifier, text=',',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)

        elif e.modifiers() == Qt.ShiftModifier:
            if e.key() in [Qt.Key_A, Qt.Key_Z, Qt.Key_X]:
                if e.key() == Qt.Key_A:
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Colon, Qt.ShiftModifier, text=':',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)
                elif e.key() == Qt.Key_Z:
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Greater, Qt.ShiftModifier, text='>',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)
                else:  # Key_X
                    mapped_e = QKeyEvent(e.type(), Qt.Key_Less, Qt.ShiftModifier, text='<',
                                         autorep=e.isAutoRepeat(), count=e.count())
                    QApplication.sendEvent(self, mapped_e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.modifiers() == Qt.ControlModifier:
            # Toggle modes
            if e.key() in [Qt.Key_E, Qt.Key_I]:
                self.mode = Mode.WORDCHECK if self.mode == Mode.INSERT else Mode.INSERT
                if self.mode == Mode.INSERT:
                    self.setExtraSelections([])
                else:
                    self.setup_wordcheck_for_word_under_cursor()
            # Mirror shortcuts.
            elif e.key() == Qt.Key_Semicolon:
                mapped_e = QKeyEvent(e.type(), Qt.Key_A, Qt.ControlModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            elif e.key() == Qt.Key_Slash:
                mapped_e = QKeyEvent(e.type(), Qt.Key_Z, Qt.ControlModifier,
                                     autorep=e.isAutoRepeat(), count=e.count())
                QApplication.sendEvent(self, mapped_e)
            else:
                super().keyPressEvent(e)

        elif self.mode == Mode.INSERT:
            if e.key() in [Qt.Key_Space, Qt.Key_Return, Qt.Key_Slash] and e.modifiers() == Qt.NoModifier:
                self.process_previous_word()
            super().keyPressEvent(e)

        elif self.mode == Mode.WORDCHECK:
            if e.modifiers() in [Qt.NoModifier, Qt.ShiftModifier]:
                self.handle_wordcheck_key_events(e)
            else:
                super().keyPressEvent(e)

        else:
            super().keyPressEvent(e)

    def keyReleaseEvent(self, e: QKeyEvent):
        # TODO: intercepted keyPressEvent counterparts?
        if self.mode == Mode.WORDCHECK:
            if e.modifiers() in [Qt.NoModifier, Qt.ShiftModifier]:
                self.handle_wordcheck_key_events(e)
            else:
                super().keyReleaseEvent(e)
        else:
            super().keyReleaseEvent(e)


if __name__ == "__main__":
    app = QApplication([])
    with open('regex_map.json') as f:
        regex_map: dict = json.load(f)
    editor = MyPlainTextEdit(regex_map)
    editor.show()
    sys.exit(app.exec_())
