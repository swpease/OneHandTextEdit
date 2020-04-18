from PySide2.QtCore import Qt
from PySide2.QtGui import QTextDocument
from PySide2.QtWidgets import QPushButton, QDialogButtonBox

from OHTE.plaintext_find_replace_dialog import PlainTextFindReplaceDialog


class TestInit(object):
    def test_window_flags(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QTextDocument())
        dialog.show()
        qtbot.addWidget(dialog)
        assert bool(dialog.windowFlags() & Qt.Tool)

    def test_btns_props(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QTextDocument())
        dialog.show()
        qtbot.addWidget(dialog)
        for btn in dialog.btn_box.buttons(): #type: QPushButton
            if dialog.btn_box.buttonRole(btn) == QDialogButtonBox.RejectRole:  # Cancel btn
                assert btn.isEnabled()
                assert btn.isDefault()
            else:
                assert not btn.isEnabled()
                assert not btn.isDefault()

    def test_close_on_enter(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QTextDocument())
        dialog.show()
        qtbot.addWidget(dialog)
        qtbot.keyClick(dialog, Qt.Key_Return)
        assert not dialog.isVisible()


class TestBtnStates(object):
    def test_text_affects_state(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QTextDocument())
        dialog.show()
        qtbot.addWidget(dialog)
        qtbot.keyClick(dialog.find_line_edit, Qt.Key_R)
        # Find's line edit is non-empty
        for btn in dialog.btn_box.buttons(): #type: QPushButton
            assert btn.isEnabled()
            if btn.text() == "Next":
                assert btn.isDefault()
            else:
                assert not btn.isDefault()
        # Find's line edit is empty
        qtbot.keyClick(dialog.find_line_edit, Qt.Key_Backspace)
        for btn in dialog.btn_box.buttons(): #type: QPushButton
            if dialog.btn_box.buttonRole(btn) == QDialogButtonBox.RejectRole:  # Cancel btn
                assert btn.isEnabled()
                assert btn.isDefault()
            else:
                assert not btn.isEnabled()
                assert not btn.isDefault()
