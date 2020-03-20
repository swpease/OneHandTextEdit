from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import (QDialog, QLabel, QLineEdit, QDialogButtonBox, QPushButton, QMessageBox,
                               QVBoxLayout, QFormLayout)


class ValidatingDialog(QDialog):
    """
    Dialog intended to get a text input from the user, constrained by a regex validator, aided by a help message box.

    Upon clicking OK, the text is emitted through the `submitted` signal.
    A `text` property is available as well.
    """

    submitted = Signal(str)

    def __init__(self, validator: QRegExpValidator, help_msg_box: QMessageBox, input_label: str = "",
                 parent=None, f=Qt.WindowFlags()):
        """
        Sets the widget up, including a validator and help message box.

        :param validator: The validator. The reason to use this class.
        :param help_msg_box: Message box intended to describe any validation constraints to the user.
        :param input_label: string label for the line input
        :param parent: QWidget parent
        :param f: WindowFlags
        """
        super().__init__(parent=parent, f=f)

        self.help_msg_box: QMessageBox = help_msg_box

        form_layout = QFormLayout()
        edit_label = QLabel(input_label)
        self.line_edit: QLineEdit = QLineEdit()
        self.line_edit.setValidator(validator)
        form_layout.addRow(edit_label, self.line_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.help_btn: QPushButton = QPushButton("Help")
        self.help_btn.setDefault(True)
        self.ok_btn: QPushButton = QPushButton("OK")
        self.ok_btn.setEnabled(False)
        btn_box.addButton(self.help_btn, QDialogButtonBox.HelpRole)
        btn_box.addButton(self.ok_btn, QDialogButtonBox.AcceptRole)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(btn_box)
        self.setLayout(layout)

        self.line_edit.textEdited.connect(self._handle_text_edited)
        btn_box.accepted.connect(self._emit_submitted)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_box.helpRequested.connect(self.show_help)

    def _handle_text_edited(self, text):
        self.ok_btn.setEnabled(self.line_edit.hasAcceptableInput())
        if self.line_edit.hasAcceptableInput():
            self.ok_btn.setDefault(True)
        else:
            self.help_btn.setDefault(True)

    def _emit_submitted(self):
        self.submitted.emit(self.text)

    def show_help(self):
        self.help_msg_box.exec_()

    @property
    def text(self):
        """Get the QLineEdit's text."""
        return self.line_edit.text()

