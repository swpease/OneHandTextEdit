import pytest
import json
import os
from unittest.mock import MagicMock

from PySide2.QtWidgets import QToolButton, QMessageBox
from PySide2.QtCore import Qt

from OHTE.regex_map import create_regex_map
from OHTE.main_window import MainWindow
from OHTE.validating_dialog import ValidatingDialog


# Mocking modal.
QMessageBox.information = MagicMock()


@pytest.fixture()
def main_win():
    src = 'test_words.txt'
    dest = 'test_out.json'
    words = ["may", "cat"]

    with open(src, 'w') as f:
        for word in words:
            f.write("%s\n" % word)

    create_regex_map([src], [True], dest)

    with open(dest) as f:
        regex_map = json.load(f)
    yield MainWindow(regex_map, dict_src=dest)

    os.remove(src)
    os.remove(dest)


class TestAddWord(object):
    def test_add_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.dict_tool_bar.findChildren(QToolButton)[1].click()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'mat')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert main_win.dict_modified

    def test_add_duplicate_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.dict_tool_bar.findChildren(QToolButton)[1].click()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'may')
        qtbot.keyClick(vd, Qt.Key_Enter)
        QMessageBox.information.assert_called()
        assert not main_win.dict_modified


class TestDelWord(object):
    def test_del_missing_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.dict_tool_bar.findChildren(QToolButton)[2].click()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'mat')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert not main_win.dict_modified

    def test_del_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.dict_tool_bar.findChildren(QToolButton)[2].click()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'may')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert main_win.dict_modified


class TestSaveChanges(object):
    def test_save(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.dict_tool_bar.findChildren(QToolButton)[1].click()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'mat')
        qtbot.keyClick(vd, Qt.Key_Enter)
        old_dict = main_win.regex_map
        qtbot.keyClick(main_win, Qt.Key_N, Qt.ControlModifier)  # Test env breaks if you close only QMainWindow
        main_win.close()

        with open('test_out.json') as f:
            regex_map = json.load(f)
        assert old_dict == regex_map
