import pytest
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextDocument
from PySide2.QtWidgets import QPushButton, QDialogButtonBox, QPlainTextEdit

from src.main.python.plaintext_find_replace_dialog import PlainTextFindReplaceDialog

@pytest.fixture()
def stuff():
    g = QPlainTextEdit()
    d = PlainTextFindReplaceDialog(g)
    return g, d


class TestInit(object):
    def test_window_flags(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QPlainTextEdit())
        dialog.show()
        qtbot.addWidget(dialog)
        assert bool(dialog.windowFlags() & Qt.Tool)

    def test_btns_props(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QPlainTextEdit())
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
        dialog = PlainTextFindReplaceDialog(QPlainTextEdit())
        dialog.show()
        qtbot.addWidget(dialog)
        qtbot.keyClick(dialog, Qt.Key_Return)
        assert not dialog.isVisible()


class TestBtnStates(object):
    def test_text_affects_state(self, qtbot):
        dialog = PlainTextFindReplaceDialog(QPlainTextEdit())
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


class TestNext(object):
    def test_highlight_basic(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)

        es = te.extraSelections()
        assert len(es) == 3
        # wraps around to first (b/c te cursor is at end of doc)
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[1].format.background().color().getRgb()

    def test_cycles_fwd(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 3
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[0].format.background().color().getRgb()

    def test_refinds_on_te_edit(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        qtbot.keyClick(te, Qt.Key_Backspace)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 2

    def test_moves_te_cursor(self, stuff, qtbot):
        # doing this updates the viewport to have current cursor selection in frame.
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert te.textCursor().position() == d.current_cursor.position()


class TestPrev(object):
    def test_highlight_basic(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)

        es = te.extraSelections()
        assert len(es) == 3
        # back to second (b/c te cursor is at end of doc)
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[0].format.background().color().getRgb()

    def test_shiftenter_basic(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.keyClick(d, Qt.Key_Return, Qt.ShiftModifier)

        es = te.extraSelections()
        assert len(es) == 3
        # back to second (b/c te cursor is at end of doc)
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[0].format.background().color().getRgb()

    def test_cycles_back(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 3
        assert es[0].format.background().color().getRgb() != es[2].format.background().color().getRgb()
        assert es[1].format.background().color().getRgb() == es[0].format.background().color().getRgb()

    def test_refinds_on_te_edit(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        qtbot.keyClick(te, Qt.Key_Backspace)
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 2

    def test_moves_te_cursor(self, stuff, qtbot):
        # doing this updates the viewport to have current cursor selection in frame.
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        assert te.textCursor().position() == d.current_cursor.position()


class TestReplace(object):
    def test_same_as_next_when_cursors_needed(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.mouseClick(d.replace_btn, Qt.LeftButton)

        es = te.extraSelections()
        assert len(es) == 4
        # wraps around to first (b/c te cursor is at end of doc)
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[1].format.background().color().getRgb()

    def test_replace(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.mouseClick(d.replace_btn, Qt.LeftButton)  # find next called
        qtbot.mouseClick(d.replace_btn, Qt.LeftButton)  # replace

        es = te.extraSelections()
        assert len(es) == 3
        assert es[0].format.background().color().getRgb() != es[1].format.background().color().getRgb()
        assert es[2].format.background().color().getRgb() == es[1].format.background().color().getRgb()


class TestReplaceAll(object):
    def test_replace_all(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.keyClicks(d.replace_line_edit, "l")
        qtbot.mouseClick(d.replace_all_btn, Qt.LeftButton)
        assert te.toPlainText() == "l l"


class TestInfoLabel(object):
    def test_replace_all_notifies_num_of_replacements(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        qtbot.keyClicks(d.replace_line_edit, "l")
        qtbot.mouseClick(d.replace_all_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "Made 2 replacements"

    def test_next_and_prev_displays_x_of_y_if_matches(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "2 of 3 matches"
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "1 of 3 matches"

    def test_no_matches_says_so(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "kjhlkj")
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"
        qtbot.mouseClick(d.find_prev_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"
        qtbot.keyClicks(d.replace_line_edit, "l")
        qtbot.mouseClick(d.replace_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"

    def test_changing_thing_to_find_clears(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "kjhlkj")
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"
        qtbot.keyClicks(d.find_line_edit, "k")
        assert not d.found_info_label.text()

    def test_toggling_flags_clears(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        qtbot.keyClicks(te, "hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "kjhlkj")
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"
        d.match_case_check_box.setChecked(True)
        assert not d.found_info_label.text()
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        assert d.found_info_label.text() == "No matches found"
        d.whole_word_check_box.setChecked(True)
        assert not d.found_info_label.text()


class TestClose(object):
    def test_clears_highlights_on_close(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.keyClick(dc, Qt.Key_Return)  # not working...
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        d.reject()
        assert not te.extraSelections()


class TestFlags(object):
    def test_match_case_flag(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi hi Hi")
        qtbot.keyClicks(d.find_line_edit, "hi")
        # qtbot.mouseClick(d.match_case_check_box, Qt.LeftButton)  # not working...
        d.match_case_check_box.setChecked(True)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 2

        d.match_case_check_box.setChecked(False)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 3

    def test_whole_word_flag(self, stuff, qtbot):
        te: QPlainTextEdit = stuff[0]
        d: PlainTextFindReplaceDialog = stuff[1]
        qtbot.addWidget(te)
        qtbot.addWidget(d)

        te.setPlainText("hi Hi hii")
        qtbot.keyClicks(d.find_line_edit, "hi")
        d.whole_word_check_box.setChecked(True)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 2

        d.whole_word_check_box.setChecked(False)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 3

        # both together
        d.whole_word_check_box.setChecked(True)
        d.match_case_check_box.setChecked(True)
        qtbot.mouseClick(d.find_next_btn, Qt.LeftButton)
        es = te.extraSelections()
        assert len(es) == 1
