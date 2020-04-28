import pytest
import json
import os
import os.path
from unittest.mock import MagicMock, patch

from PySide2.QtWidgets import QToolButton, QMessageBox, QDockWidget, QLabel, QApplication, QDialog
from PySide2.QtCore import Qt, QSettings
from PySide2.QtPrintSupport import QPrintDialog

from src.main.python.regex_map import create_regex_map
from src.main.python.main_window import MainWindow
from src.main.python.validating_dialog import ValidatingDialog
from src.main.python.textedit import Mode


# Mocking modal.
QMessageBox.information = MagicMock()
QMessageBox.warning = MagicMock(return_value=QMessageBox.Cancel)
QPrintDialog.exec_ = MagicMock(return_value=QDialog.Accepted)


@pytest.fixture()
def main_win():
    MainWindow.dict_modified = False

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


@pytest.fixture(scope="class")
def mainwin_recentfiles():
    MainWindow.dict_modified = False
    MainWindow.max_recent_files = 2

    # resetting recent files
    settings = QSettings('PMA', 'OneHandTextEdit')
    settings.setValue('recent_files', [])

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
    os.remove('document1.txt')
    os.remove('document2.txt')
    os.remove('document3.txt')
    # resetting recent files
    settings = QSettings('PMA', 'OneHandTextEdit')
    settings.setValue('recent_files', [])


class TestRecentFiles(object):
    """This is a set of interdependent tests, which has its pros and cons. Also requires manual interaction."""
    def test_inactive_clear_recent(self, mainwin_recentfiles: MainWindow, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        assert not mainwin_recentfiles.clear_recent_files_act.isEnabled()

    def test_no_files(self, mainwin_recentfiles, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        for act in mainwin_recentfiles.recent_file_acts:
            assert not act.isVisible()

    def test_save_one_file(self, mainwin_recentfiles, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        mainwin_recentfiles.text_edit.setPlainText('1')
        mainwin_recentfiles.save_as() # raises a modal
        act1 = mainwin_recentfiles.recent_file_acts[0]
        assert act1.isVisible()
        assert act1.data() == os.path.realpath('document1.txt')
        assert act1.text() == 'document1.txt'
        act2 = mainwin_recentfiles.recent_file_acts[1]
        assert not act2.isVisible()
        assert mainwin_recentfiles.clear_recent_files_act.isEnabled()

    def test_save_three_files(self, mainwin_recentfiles, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        # file 2
        mainwin_recentfiles.new_file()
        win2 = MainWindow.window_list[0]
        win2.text_edit.setPlainText('2')
        win2.save_as()
        act1 = mainwin_recentfiles.recent_file_acts[0]  # check that it updates across open files
        assert act1.isVisible()
        assert act1.text() == 'document2.txt'
        act2 = mainwin_recentfiles.recent_file_acts[1]
        assert act2.isVisible()
        assert act2.text() == 'document1.txt'
        # file 3
        win2.new_file()
        win3 = MainWindow.window_list[1]
        win3.text_edit.setPlainText('3')
        win3.save_as()
        act1 = mainwin_recentfiles.recent_file_acts[0]
        assert act1.isVisible()
        assert act1.text() == 'document3.txt'
        act2 = mainwin_recentfiles.recent_file_acts[1]
        assert act2.isVisible()
        assert act2.text() == 'document2.txt'

    def test_open_nonrecent_file(self, mainwin_recentfiles, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        mainwin_recentfiles.open()  # use test_words.txt
        act1 = mainwin_recentfiles.recent_file_acts[0]
        assert act1.isVisible()
        assert act1.text() == 'test_words.txt'
        act2 = mainwin_recentfiles.recent_file_acts[1]
        assert act2.isVisible()
        assert act2.text() == 'document3.txt'

    def test_open_recent_hookup(self, mainwin_recentfiles: MainWindow, qtbot):
        MainWindow.open_file = MagicMock()
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        win3: MainWindow = MainWindow.window_list[1]
        win3.close()
        assert not win3.isVisible()
        mainwin_recentfiles.recent_file_acts[1].trigger()  # ref: prior test
        MainWindow.open_file.assert_called_once_with(win3.cur_file)

    def test_clear_recent(self, mainwin_recentfiles: MainWindow, qtbot):
        mainwin_recentfiles.show()
        qtbot.addWidget(mainwin_recentfiles)
        mainwin_recentfiles.clear_recent_files_act.trigger()
        for act in mainwin_recentfiles.recent_file_acts:
            assert not act.isVisible()
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                assert not widget.clear_recent_files_act.isEnabled()


class TestEntryDefaultSet(object):
    """Checks that everything is hooked up right from MainWindow down to the regex_map fn call."""
    def test_true(self, main_win, qtbot):
        with patch('src.main.python.textedit.set_entry_default', return_value=True) as mock:
            main_win.show()
            qtbot.addWidget(main_win)
            # main_win.text_edit.set_wordcheck_word_as_default = MagicMock()
            qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
            assert main_win.text_edit.mode == Mode.WORDCHECK
            qtbot.keyClick(main_win.text_edit, Qt.Key_O)
            assert MainWindow.dict_modified

    # checking other hotkey
    def test_true_b(self, main_win, qtbot):
        with patch('src.main.python.textedit.set_entry_default', return_value=True) as mock:
            main_win.show()
            qtbot.addWidget(main_win)
            # main_win.text_edit.set_wordcheck_word_as_default = MagicMock()
            qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
            assert main_win.text_edit.mode == Mode.WORDCHECK
            qtbot.keyClick(main_win.text_edit, Qt.Key_W)
            assert MainWindow.dict_modified

    def test_false(self, main_win, qtbot):
        with patch('src.main.python.textedit.set_entry_default', return_value=False) as mock:
            main_win.show()
            qtbot.addWidget(main_win)
            qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
            assert main_win.text_edit.mode == Mode.WORDCHECK
            qtbot.keyClick(main_win.text_edit, Qt.Key_O)
            assert not MainWindow.dict_modified


class TestMarkdownFont(object):
    def test_basic(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.md_text_edit.setFont = MagicMock()
        main_win.md_font_act.trigger()
        assert main_win.md_text_edit.setFont.call_count == 1


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

    def test_dock_updates_markdown_when_its_made_visible(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.update_markdown_viewer = MagicMock()
        dock = main_win.findChild(QDockWidget)
        qtbot.keyClick(main_win.text_edit, Qt.Key_M)
        qtbot.keyClick(main_win.text_edit, Qt.Key_M, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert dock.isVisible()
        qtbot.keyClick(main_win.text_edit, Qt.Key_M)
        qtbot.keyClick(main_win.text_edit, Qt.Key_C, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        qtbot.keyClick(main_win.text_edit, Qt.Key_M)
        assert not dock.isVisible()
        assert main_win.update_markdown_viewer.call_count == 1


class TestAddWord(object):
    def test_add_word(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.add_word_act.trigger()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'mat')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert main_win.dict_modified

    def test_add_duplicate_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.add_word_act.trigger()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'may')
        qtbot.keyClick(vd, Qt.Key_Enter)
        QMessageBox.information.assert_called()
        assert not main_win.dict_modified


class TestDelWord(object):
    def test_del_missing_word(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.delete_word_act.trigger()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'mat')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert not main_win.dict_modified

    def test_del_word(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.delete_word_act.trigger()
        vd = main_win.findChildren(ValidatingDialog)[-1]
        qtbot.keyClicks(vd.line_edit, 'may')
        qtbot.keyClick(vd, Qt.Key_Enter)
        assert main_win.dict_modified


# Obsolete, with saving now in `main.py`
# class TestSaveChanges(object):
#     def test_save(self, main_win, qtbot):
#         main_win.show()
#         qtbot.addWidget(main_win)
#         main_win.dict_tool_bar.findChildren(QToolButton)[1].click()
#         vd = main_win.findChildren(ValidatingDialog)[-1]
#         qtbot.keyClicks(vd.line_edit, 'mat')
#         qtbot.keyClick(vd, Qt.Key_Enter)
#         old_dict = main_win.regex_map
#         qtbot.keyClick(main_win, Qt.Key_N, Qt.ControlModifier)  # Test env breaks if you close only QMainWindow
#         main_win.close()
#
#         with open('test_out.json') as f:
#             regex_map = json.load(f)
#         assert old_dict == regex_map


class TestModeSwitch(object):
    def test_textedit_hookup(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        assert main_win.text_edit.mode == Mode.INSERT
        qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
        assert main_win.text_edit.mode == Mode.WORDCHECK
        qtbot.keyClick(main_win.text_edit, Qt.Key_I, modifier=Qt.ControlModifier)
        assert main_win.text_edit.mode == Mode.INSERT

    def test_statusbar(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        assert main_win.statusBar().findChild(QLabel).text() == Mode.INSERT.name.capitalize() + " Mode"
        qtbot.keyClick(main_win.text_edit, Qt.Key_E, modifier=Qt.ControlModifier)
        assert main_win.statusBar().findChild(QLabel).text() == Mode.WORDCHECK.name.capitalize() + " Mode"
        qtbot.keyClick(main_win.text_edit, Qt.Key_I, modifier=Qt.ControlModifier)
        assert main_win.statusBar().findChild(QLabel).text() == Mode.INSERT.name.capitalize() + " Mode"

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


class TestFind(object):
    def test_hookup(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.show_find_and_replace_dialog = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_F, modifier=Qt.ControlModifier)
        qtbot.keyClick(main_win.text_edit, Qt.Key_J, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert main_win.show_find_and_replace_dialog.call_count == 2


class TestPrint(object):
    def test_hookup(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_ = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=Qt.ControlModifier)
        qtbot.keyClick(main_win.text_edit, Qt.Key_R, modifier=Qt.ControlModifier)
        assert main_win.print_.call_args[0][1] == main_win.text_edit
        assert main_win.print_.call_count == 2


class TestPrintMarkdown(object):
    def test_hookup(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_ = MagicMock()
        main_win.update_markdown_viewer = MagicMock()
        qtbot.keyClick(main_win.text_edit, Qt.Key_P, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        qtbot.keyClick(main_win.text_edit, Qt.Key_R, modifier=(Qt.ControlModifier | Qt.ShiftModifier))
        assert main_win.print_.call_args[0][1] == main_win.md_text_edit
        assert main_win.print_.call_count == 2
        assert main_win.update_markdown_viewer.call_count == 2


class TestPrintPreview(object):
    def test_basic(self, main_win, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_ = MagicMock()
        main_win.print_preview_act.trigger()
        assert main_win.print_.call_args[0][1] == main_win.text_edit
        assert main_win.print_.call_count == 1


class TestPrintMarkdownPreview(object):
    def test_basic(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        main_win.print_ = MagicMock()
        main_win.update_markdown_viewer = MagicMock()
        main_win.print_preview_markdown_act.trigger()
        assert main_win.print_.call_args[0][1] == main_win.md_text_edit
        assert main_win.print_.call_count == 1
        assert main_win.update_markdown_viewer.call_count == 1


class TestMarkdownUpdate(object):
    def test_doesnt_exceed_max_md_textedit_position(self, main_win: MainWindow, qtbot):
        main_win.show()
        qtbot.addWidget(main_win)
        qtbot.keyClicks(main_win.text_edit, "# hi")
        main_win.update_markdown_viewer()
        assert main_win.md_text_edit.textCursor().position() == 2
