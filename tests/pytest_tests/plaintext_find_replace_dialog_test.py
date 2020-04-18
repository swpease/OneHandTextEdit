from PySide2.QtCore import Qt
from PySide2.QtGui import QTextDocument

from OHTE.plaintext_find_replace_dialog import PlainTextFindReplaceDialog


class TestInit(object):
    def test_window_flags(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QTextDocument())
        dialog.show()
        qtbot.addWidget(dialog)
        assert bool(dialog.windowFlags() & Qt.Tool)
