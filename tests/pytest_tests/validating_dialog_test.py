from unittest.mock import MagicMock

from PySide2.QtCore import Qt
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QMessageBox, QPushButton

from src.main.python.validating_dialog import ValidatingDialog


class TestVDBtns(object):
    def test_help(self, qtbot):
        validator = QRegExpValidator(r'(x|xxx)')
        help_popup = QMessageBox(QMessageBox.Information, "hi", "hi")
        help_popup.exec_ = MagicMock()
        vd = ValidatingDialog(validator, help_popup)
        vd.show()
        qtbot.addWidget(vd)

        qtbot.mouseClick(vd.help_btn, Qt.LeftButton)
        help_popup.exec_.assert_called()

    def test_cancel(self, qtbot):
        validator = QRegExpValidator(r'(x|xxx)')
        help_popup = QMessageBox(QMessageBox.Information, "hi", "hi")
        vd = ValidatingDialog(validator, help_popup)
        vd.reject = MagicMock()
        vd.show()
        qtbot.addWidget(vd)

        # print('\n\n', vd.children()[-2].findChildren(QPushButton), '\n\n')
        qtbot.mouseClick(vd.children()[-2].findChildren(QPushButton)[0], Qt.LeftButton)
        vd.reject.assert_called()
