import sys

from PySide2.QtWidgets import (QDialog, QLabel, QLineEdit, QDialogButtonBox, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QApplication)
from PySide2.QtGui import QTextDocument
from PySide2.QtCore import Qt


class PlainTextFindReplaceDialog(QDialog):
    """
    Modeless, stay-above-parent dialog that supports find and replace.

    Allows for searching case (in)sensitively, and whole-word.
    Find triggered by Enter / Shift+Enter, or corresponding button (Next / Previous).
    Find wraps.
    Highlights all matches, operating on the closest-to-user's-cursor selection first,
    in the user-selected direction (Next / Previous).
    """

    def __init__(self, document: QTextDocument, parent=None):
        """
        Sets up the dialog.

        :param document: Document to operate on.
        :param parent: QWidget parent
        """
        super().__init__(parent=parent, f=Qt.Tool)
        self.document = document

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

        self.btn_box.rejected.connect(self.reject)
        self.find_line_edit.textEdited.connect(self._handle_text_edited)

    def _handle_text_edited(self, text):
        """
        Modifies button states.

        :param text: The find_line_edit's text.
        :return: Side effect: btn enabled / default
        """
        find_enabled = text != ""
        self.find_next_btn.setEnabled(find_enabled)
        self.find_prev_btn.setEnabled(find_enabled)
        self.replace_btn.setEnabled(find_enabled)
        self.replace_all_btn.setEnabled(find_enabled)

        self.find_next_btn.setDefault(find_enabled)
        self.btn_box.button(QDialogButtonBox.Close).setDefault(not find_enabled)


if __name__ == '__main__':
    app = QApplication([])
    d = PlainTextFindReplaceDialog(QTextDocument())
    d.show()
    sys.exit(app.exec_())
