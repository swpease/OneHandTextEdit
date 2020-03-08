import sys
import json
import re
from enum import Enum

from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QKeyEvent
from PySide2.QtWidgets import QApplication, QPlainTextEdit

from regex_map import map_word_to_entry, capitalized_symbol_map


class Mode(Enum):
    INSERT = 1
    WORDCHECK = 2


class MyPlainTextEdit(QPlainTextEdit):
    def __init__(self, regex_map: str = 'regex_map.json'):
        super().__init__()  # Pass parent?
        self.mode = Mode.INSERT
        with open(regex_map) as f:
            self.regex_map: dict = json.load(f)

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
