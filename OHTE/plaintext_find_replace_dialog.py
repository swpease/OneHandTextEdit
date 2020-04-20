import sys
from typing import List

from PySide2.QtWidgets import (QDialog, QLabel, QLineEdit, QDialogButtonBox, QPushButton, QPlainTextEdit, QTextEdit,
                               QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QApplication)
from PySide2.QtGui import QTextDocument, QTextCursor, QColor, QKeyEvent
from PySide2.QtCore import Qt


class PlainTextFindReplaceDialog(QDialog):
    """
    Modeless, stay-above-parent dialog that supports find and replace.

    Allows for searching case (in)sensitively, and whole-word.
    Find triggered by Enter / Shift+Enter, or corresponding button (Next / Previous).
    Find wraps.
    Highlights all matches, operating on the closest-to-user's-cursor selection first,
    in the user-selected direction (Next / Previous).
    Highlighting / found cursors retained on navigation back to text editor, and cleared on re-find/replace if
    user modified the document.
    """

    def __init__(self, plain_text_edit: QPlainTextEdit, parent=None):
        """
        Sets up the dialog.

        :param plain_text_edit: Text Editor to operate on.
        :param parent: QWidget parent
        """
        super().__init__(parent=parent, f=Qt.Tool)
        self.plain_text_edit = plain_text_edit
        self.cursors_needed = True
        self.find_flags = QTextDocument.FindFlags()
        self.found_cursors: List[QTextCursor] = []
        self.current_cursor = QTextCursor()

        # UI
        layout = QVBoxLayout()
        find_and_replace_layout = QGridLayout()
        layout.addLayout(find_and_replace_layout)  # if QGL is sub-layout, add to parent layout before doing stuff.

        self.find_line_edit = QLineEdit()
        find_label = QLabel("&Find")
        find_label.setBuddy(self.find_line_edit)

        options_layout = QHBoxLayout()
        self.match_case_check_box = QCheckBox("Match Case")
        self.whole_word_check_box = QCheckBox("Whole Word")
        options_layout.addWidget(self.match_case_check_box)
        options_layout.addWidget(self.whole_word_check_box)
        options_layout.addStretch()

        self.replace_line_edit = QLineEdit()
        replace_label = QLabel("&Replace")
        replace_label.setBuddy(self.replace_line_edit)

        find_and_replace_layout.addWidget(find_label, 0, 0)
        find_and_replace_layout.addWidget(self.find_line_edit, 0, 1)
        find_and_replace_layout.addLayout(options_layout, 1, 1)
        find_and_replace_layout.setRowMinimumHeight(2, 20)
        find_and_replace_layout.addLayout(QHBoxLayout(), 2, 0)  # Spacing to assoc. options with Find, not Replace
        find_and_replace_layout.addWidget(replace_label, 3, 0)
        find_and_replace_layout.addWidget(self.replace_line_edit, 3, 1)

        self.btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.find_next_btn = QPushButton("Next")
        self.find_next_btn.setEnabled(False)
        self.find_prev_btn = QPushButton("Previous")
        self.find_prev_btn.setEnabled(False)
        self.replace_btn = QPushButton("Replace")
        self.replace_btn.setEnabled(False)
        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.setEnabled(False)
        self.btn_box.addButton(self.replace_btn, QDialogButtonBox.ActionRole)
        self.btn_box.addButton(self.replace_all_btn, QDialogButtonBox.ActionRole)
        self.btn_box.addButton(self.find_prev_btn, QDialogButtonBox.ActionRole)
        self.btn_box.addButton(self.find_next_btn, QDialogButtonBox.ActionRole)

        layout.addWidget(self.btn_box)
        self.setLayout(layout)
        # End UI

        self.btn_box.rejected.connect(self.reject)
        self.find_line_edit.textEdited.connect(self._handle_text_edited)
        self.find_next_btn.clicked.connect(self.next)
        self.find_prev_btn.clicked.connect(self.prev)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.plain_text_edit.document().contentsChanged.connect(self.set_cursors_needed_true)
        self.whole_word_check_box.stateChanged.connect(self.toggle_whole_word_flag)
        self.match_case_check_box.stateChanged.connect(self.toggle_match_case_flag)

    def closeEvent(self, arg__1):
        self.plain_text_edit.setExtraSelections([])
        super().closeEvent(arg__1)

    def keyPressEvent(self, arg__1: QKeyEvent):
        # Shift+Enter triggers find previous, if the corresponding btn is enabled.
        if (arg__1.key() in [Qt.Key_Return, Qt.Key_Enter] and arg__1.modifiers() == Qt.ShiftModifier
                and self.find_prev_btn.isEnabled()):
            self.prev()
        else:
            super().keyPressEvent(arg__1)

    def set_cursors_needed_true(self):
        self.cursors_needed = True

    def toggle_match_case_flag(self, state: int):
        self.cursors_needed = True

        if state == Qt.Unchecked:
            self.find_flags &= ~QTextDocument.FindCaseSensitively
        elif state == Qt.Checked:
            self.find_flags |= QTextDocument.FindCaseSensitively

    def toggle_whole_word_flag(self, state: int):
        self.cursors_needed = True

        if state == Qt.Unchecked:
            self.find_flags &= ~QTextDocument.FindWholeWords
        elif state == Qt.Checked:
            self.find_flags |= QTextDocument.FindWholeWords

    def find_all(self, text: str, document: QTextDocument, flags=QTextDocument.FindFlags()) -> List[QTextCursor]:
        """
        Finds all occurrences of `text` in `document`, in order.

        :param text: Text to find.
        :param document: Document to search.
        :param flags: Conditions to set on the search: none or (whole word and/or match case)
        :return: Ordered list of all found instances.
        """
        cursor = QTextCursor(document)  # default pos == 0
        found: List[QTextCursor] = []

        while True:
            cursor = document.find(text, cursor, flags)
            if cursor.isNull():
                return found
            else:
                found.append(cursor)

    def update_textedit_visuals(self):
        """
        Moves text editor's cursor to match currently highlighted `find` word, and performs the `find` highlighting.
        """
        # move along text editor's viewport
        next_pte_cursor = QTextCursor(self.current_cursor)
        next_pte_cursor.clearSelection()
        self.plain_text_edit.setTextCursor(next_pte_cursor)

        #highlighting
        normal_color = QColor(Qt.yellow).lighter()
        current_color = QColor(Qt.magenta).lighter()
        extra_selections: List[QTextEdit.ExtraSelection] = []
        for cur in self.found_cursors:
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cur
            if cur == self.current_cursor:
                selection.format.setBackground(current_color)
            else:
                selection.format.setBackground(normal_color)
            extra_selections.append(selection)
        self.plain_text_edit.setExtraSelections(extra_selections)

    def init_find(self):
        """Sets up internal state for the case when cursors are needed (e.g. first find, user modifies doc...)"""
        self.found_cursors = self.find_all(self.find_line_edit.text(), self.plain_text_edit.document(), self.find_flags)
        self.cursors_needed = False
        self.current_cursor = self.plain_text_edit.textCursor()  # returns copy of
        self.plain_text_edit.setExtraSelections([])

    def replace_all(self):
        """
        Replaces all instances of Find's text with Replace's text.

        :return: Side effect: replaces words in text edit
        """
        if self.cursors_needed:
            self.init_find()

        for cur in self.found_cursors:
            cur.insertText(self.replace_line_edit.text())

    def replace(self):
        """
        Replaces the word under focus by `next`.

        Replaces with the Replace line edit's text, and advances to next word. If no word under focus via this dialog,
        calls `next`.
        :return: Side effect: replaces word in text edit
        """
        if self.cursors_needed:
            self.next()
            return

        if not self.found_cursors:
            return

        self.plain_text_edit.document().contentsChanged.disconnect(self.set_cursors_needed_true)  # don't dup work.
        self.current_cursor.insertText(self.replace_line_edit.text())
        self.plain_text_edit.document().contentsChanged.connect(self.set_cursors_needed_true)
        self.found_cursors.remove(self.current_cursor)
        self.next()

    def prev(self):
        if self.cursors_needed:
            self.init_find()

        if not self.found_cursors:
            return

        if self.current_cursor <= self.found_cursors[0]:  # loop back to end.
            self.current_cursor = self.found_cursors[-1]
        else:
            for cur in reversed(self.found_cursors):
                if cur < self.current_cursor:  # prev in order
                    self.current_cursor = cur
                    break

        self.update_textedit_visuals()

    def next(self):
        if self.cursors_needed:
            self.init_find()

        if not self.found_cursors:
            return

        if self.current_cursor >= self.found_cursors[-1]:  # loop back to start. cursor equality based on position.
            self.current_cursor = self.found_cursors[0]
        else:
            for cur in self.found_cursors:
                if cur > self.current_cursor:  # next in order
                    self.current_cursor = cur
                    break

        self.update_textedit_visuals()

    def _handle_text_edited(self, text):
        """
        Modifies button states and sets self.cursors_needed to True.

        :param text: The find_line_edit's text.
        :return: Side effect: btn enabled / default
        """
        self.cursors_needed = True

        find_enabled = text != ""
        self.find_next_btn.setEnabled(find_enabled)
        self.find_prev_btn.setEnabled(find_enabled)
        self.replace_btn.setEnabled(find_enabled)
        self.replace_all_btn.setEnabled(find_enabled)

        self.find_next_btn.setDefault(find_enabled)
        self.btn_box.button(QDialogButtonBox.Close).setDefault(not find_enabled)


if __name__ == '__main__':
    app = QApplication([])
    g = QPlainTextEdit()
    d = PlainTextFindReplaceDialog(g)
    g.show()
    d.show()
    sys.exit(app.exec_())
