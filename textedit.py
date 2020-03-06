import sys
import json
import re
from enum import Enum

from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor, QKeyEvent
from PySide2.QtWidgets import QApplication, QPlainTextEdit

from regex_map import map_word


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
        word = map_word(end_seq_match.group('raw_word'), self.regex_map)
        if word is None:  # Word not found in regex_map dictionary
            return

        # Replace the old word
        cursor.setPosition(cursor.position() - match_len)
        cursor.setPosition((cursor.position() + len(word)), mode=QTextCursor.KeepAnchor)
        cursor.insertText(word)

    def keyPressEvent(self, e: QKeyEvent):
        if self.mode == Mode.INSERT:
            if e.key() in [Qt.Key_Space, Qt.Key_Return, Qt.Key_Slash]:  # For some reason Return is handled before kRE capturing.
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
