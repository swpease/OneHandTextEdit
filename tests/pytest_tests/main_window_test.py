import pytest
import json
import os
from unittest.mock import MagicMock

from PySide2.QtWidgets import QToolButton, QMessageBox, QTextEdit, QDockWidget
from PySide2.QtCore import Qt

from OHTE.regex_map import create_regex_map
from OHTE.main_window import MainWindow
from OHTE.validating_dialog import ValidatingDialog
from OHTE.textedit import Mode


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


class TestDockingSetup(object):
    def test_hidden(self, main_win, qtbot):
        """Implicitly tests that it's hooked up to MainWindow"""
        main_win.show()
        qtbot.addWidget(main_win)
        dock = main_win.findChild(QDockWidget)
        assert not dock.isVisible()

    def test_shortcuts(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        dock = main_win.findChild(QDockWidget)
        qtbot.keyClick(main_win.text_edit, Qt.Key_M, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert dock.isVisible()
        qtbot.keyClick(main_win.text_edit, Qt.Key_C, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert not dock.isVisible()


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


class TestModeSwitch(object):
    def test_basic(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        assert main_win.text_edit.mode == Mode.INSERT
        qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
        assert main_win.text_edit.mode == Mode.WORDCHECK
        qtbot.keyClick(main_win.text_edit, Qt.Key_I, modifier=Qt.ControlModifier)
        assert main_win.text_edit.mode == Mode.INSERT

    def test_wc_enabled(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.text_edit.setup_wordcheck_for_word_under_cursor = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
        main_win.text_edit.setup_wordcheck_for_word_under_cursor.assert_called()

    def test_highlighting(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        QMessageBox.warning = MagicMock()  # suppress popup

        qtbot.keyClicks(main_win.text_edit, 'ilknkl')

        qtbot.keyClick(main_win.text_edit, Qt.Key_E, Qt.ControlModifier)  # wordcheck mode

        cur = main_win.text_edit.textCursor()
        default_col = cur.charFormat().background().color().getRgb()  # NB: does not get ExtraSelections color

        selection = main_win.text_edit.extraSelections()[0]
        col0 = selection.format.background().color().getRgb()
        assert default_col != col0

        qtbot.keyClick(main_win.text_edit, Qt.Key_E, Qt.ControlModifier)  # insert mode
        assert [] == main_win.text_edit.extraSelections()


class TestPrint(object):
    def test_hookup(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_ = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=Qt.ControlModifier)
        qtbot.keyClick(main_win.text_edit, Qt.Key_R, modifier=Qt.ControlModifier)
        assert main_win.print_.call_count == 2

    def test_print_called(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.text_edit.print_ = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=Qt.ControlModifier)
        # hit Return manually
        assert main_win.text_edit.print_.call_count == 1


class TestPrintMarkdown(object):
    def test_hookup(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_markdown = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        qtbot.keyClick(main_win.text_edit, Qt.Key_R, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert main_win.print_markdown.call_count == 2

    def test_print_called(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        QTextEdit.print_ = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        # hit Return manually
        assert QTextEdit.print_.call_count == 1


class TestPrintPreview(object):
    def test_basic(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.text_edit.print_ = MagicMock()
        main_win.print_preview_act.trigger()
        assert main_win.text_edit.print_.call_count == 1


class TestPrintMarkdownPreview(object):
    def test_basic(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.md_text_edit.print_ = MagicMock()
        main_win.print_preview_markdown_act.trigger()
        assert main_win.md_text_edit.print_.call_count == 1
