import unittest
from unittest.mock import MagicMock
import os
import json

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from PySide2.QtTest import QTest

from src.main.python.textedit import MyPlainTextEdit, Mode
from src.main.python.regex_map import create_regex_map


src = 'test_words.txt'
dest = 'test_out.json'
regex_map: dict = {}


def setUpModule():
    if QApplication.instance() is None:
        app = QApplication([])
    words = ["e", "i", "the", "and", "ax", "it's", "den", "din", "ken", "en", "in", "hex", "he", "hi", "z"]
    with open(src, 'w') as f:
        for word in words:
            f.write("%s\n" % word)
    create_regex_map([src], [False], dest)

    with open(dest) as f:
        global regex_map
        regex_map = json.load(f)


def tearDownModule():
    os.remove(src)
    os.remove(dest)


class TestInsertMode(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_basic(self):
        # e: QKeyEvent = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
        # editor.appendPlainText("Z")
        # editor.event(e)
        QTest.keyClicks(self.editor, 'z')
        self.assertEqual(self.editor.textCursor().block().text(), "z")

    def test_word_replace_trigger(self):
        QTest.keyClicks(self.editor, 'i')
        self.assertEqual(self.editor.textCursor().block().text(), "i", msg="plain i stays i")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'e')
        self.assertEqual(self.editor.textCursor().block().text(), "e", msg="plain e stays e")
        self.editor.document().clear()
        # for whatever reason, python puts e before i, so e is default.
        QTest.keyClicks(self.editor, 'i ')
        self.assertEqual(self.editor.textCursor().block().text(), "e ", msg="space bar coersion")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'i')
        QTest.keyClick(self.editor, Qt.Key_Return)
        self.assertEqual(self.editor.textCursor().block().previous().text(), "e", msg="return btn coersion")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'i/')
        self.assertEqual(self.editor.textCursor().block().text(), "e/", msg="slash coersion")

    def test_capitalization_preservation(self):
        QTest.keyClicks(self.editor, 'And ')
        self.assertEqual(self.editor.textCursor().block().text(), "And ")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, ':nd ')
        self.assertEqual(self.editor.textCursor().block().text(), "And ")

    def test_end_of_word_letter_maps(self):
        QTest.keyClicks(self.editor, ';, ')
        self.assertEqual(self.editor.textCursor().block().text(), "ax ")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, ';,, ')
        self.assertEqual(self.editor.textCursor().block().text(), "ax, ")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'axAx ')
        self.assertEqual(self.editor.textCursor().block().text(), "ax:, ", msg="for lefties")

    def test_handles_contractions(self):
        QTest.keyClicks(self.editor, 'iy\'lAzx ')
        self.assertEqual(self.editor.textCursor().block().text(), "it\'s:., ")

    def test_handles_starting_symbols(self):
        QTest.keyClicks(self.editor, '?!3""\'"thi ')
        self.assertEqual(self.editor.textCursor().block().text(), '?!3""\'"the ')

    def test_end_of_word_stripping(self):
        QTest.keyClicks(self.editor, 'thi?!"\' ')
        self.assertEqual(self.editor.textCursor().block().text(), 'the?!"\' ')

    def test_autocaps(self):
        self.editor.autocaps = True
        QTest.keyClicks(self.editor, 'thi!\' ')
        self.assertEqual(self.editor.textCursor().block().text(), 'The!\' ')
        QTest.keyClicks(self.editor, 'thi. the ')
        self.assertEqual(self.editor.textCursor().block().text(), 'The!\' The. The ')

    def test_end_parens(self):
        QTest.keyClicks(self.editor, '"(\'thi?!\')".z  ')
        self.assertEqual(self.editor.textCursor().block().text(), '"(\'the?!\')"..  ')


class TestWordcheckModeAllowedKeys(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_typing(self):
        self.editor.handle_mode_toggle()
        QTest.keyClicks(self.editor, 'xza,.;')
        self.assertEqual(self.editor.textCursor().block().text(), ',.;,.;')
        self.editor.clear()
        QTest.keyClicks(self.editor, 'XZA<>:', modifier=Qt.ShiftModifier)
        self.assertEqual(self.editor.textCursor().block().text(), '<>:<>:')
        QTest.keyClick(self.editor, Qt.Key_Backspace, modifier=Qt.NoModifier)
        self.assertEqual(self.editor.textCursor().block().text(), '<>:<>')

    def test_hot_word_replacement(self):
        # this test handles getting to "hi," from its default coersion to "hex"
        QTest.keyClicks(self.editor, 'hi, ')  # coerced to "hex"
        self.editor.handle_mode_toggle()

        cur = self.editor.textCursor()
        cur.setPosition(3)
        self.editor.setTextCursor(cur)
        QTest.keyClick(self.editor, Qt.Key_Backspace, modifier=Qt.NoModifier)  # "he| " (| = cursor)

        QTest.keyClick(self.editor, Qt.Key_U)
        self.assertEqual(self.editor.textCursor().block().text(), 'hi ')


class TestWordcheckModeMovement(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_move_up(self):
        QTest.keyClick(self.editor, Qt.Key_Return)
        QTest.keyClick(self.editor, Qt.Key_Return)
        self.editor.handle_mode_toggle()
        QTest.keyClick(self.editor, Qt.Key_K)
        QTest.keyClick(self.editor, Qt.Key_D)
        self.assertEqual(self.editor.textCursor().blockNumber(), 0)
        self.assertEqual(self.editor.toPlainText(), "\n\n", msg="text modified")

    def test_move_down(self):
        QTest.keyClick(self.editor, Qt.Key_Return)
        QTest.keyClick(self.editor, Qt.Key_Return)
        start_cur = self.editor.textCursor()
        start_cur.setPosition(0)
        self.editor.setTextCursor(start_cur)
        self.editor.handle_mode_toggle()
        QTest.keyClick(self.editor, Qt.Key_F)
        QTest.keyClick(self.editor, Qt.Key_J)
        self.assertEqual(self.editor.textCursor().blockNumber(), 2)
        self.assertEqual(self.editor.toPlainText(), "\n\n", msg="text modified")

    def test_move_left_then_right(self):
        QTest.keyClicks(self.editor, 'the box')
        self.editor.handle_mode_toggle()
        QTest.keyClick(self.editor, Qt.Key_S)
        QTest.keyClick(self.editor, Qt.Key_H)
        self.assertEqual(self.editor.textCursor().position(), 0, msg="move by word")
        QTest.keyClick(self.editor, Qt.Key_V)
        QTest.keyClick(self.editor, Qt.Key_M)
        self.assertEqual(self.editor.textCursor().position(), 2, msg="move by char")
        self.assertEqual(self.editor.toPlainText(), "the box", msg="text modified")

    def test_move_right_then_left(self):
        QTest.keyClicks(self.editor, 'the box is')
        self.editor.handle_mode_toggle()
        start_cur = self.editor.textCursor()
        start_cur.setPosition(0)
        self.editor.setTextCursor(start_cur)
        QTest.keyClick(self.editor, Qt.Key_G)
        QTest.keyClick(self.editor, Qt.Key_L)
        self.assertEqual(self.editor.textCursor().position(), 8, msg="move by word")
        QTest.keyClick(self.editor, Qt.Key_C)
        QTest.keyClick(self.editor, Qt.Key_N)
        self.assertEqual(self.editor.textCursor().position(), 6, msg="move by char")
        self.assertEqual(self.editor.toPlainText(), "the box is", msg="text modified")


class TestWordcheckModeHighlighting(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_highlighting_colors_different(self):
        QTest.keyClicks(self.editor, 'i x i')  # Don't coerce ending `i`
        self.editor.handle_mode_toggle()  # wordcheck mode

        cur = self.editor.textCursor()
        default_col = cur.charFormat().background().color().getRgb()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)

        selection = self.editor.extraSelections()[0]
        col0 = selection.format.background().color().getRgb()
        self.assertNotEqual(default_col, col0)

        cur = self.editor.textCursor()
        cur.setPosition(1)
        self.editor.setTextCursor(cur)
        selection = self.editor.extraSelections()[0]
        col1 = selection.format.background().color().getRgb()
        self.assertEqual(col0, col1)

        cur = self.editor.textCursor()
        cur.setPosition(2)
        self.editor.setTextCursor(cur)
        selection = self.editor.extraSelections()[0]
        col2 = selection.format.background().color().getRgb()
        self.assertNotEqual(col0, col2)
        self.assertNotEqual(default_col, col2)

        cur = self.editor.textCursor()
        cur.setPosition(4)
        self.editor.setTextCursor(cur)
        selection = self.editor.extraSelections()[0]
        col4 = selection.format.background().color().getRgb()
        self.assertNotEqual(col0, col4)
        self.assertNotEqual(col2, col4)
        self.assertNotEqual(default_col, col4)

        cur = self.editor.textCursor()
        cur.setPosition(5)
        self.editor.setTextCursor(cur)
        selection = self.editor.extraSelections()[0]
        col5 = selection.format.background().color().getRgb()
        self.assertEqual(col4, col5)


class TestWordcheckModeCycling(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_missing_word(self):
        text = 'jkljkl e den '
        QTest.keyClicks(self.editor, text)
        self.editor.handle_mode_toggle()  # wordcheck mode

        cur = self.editor.textCursor()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)

        QTest.keyClick(self.editor, Qt.Key_U)
        new_text = self.editor.toPlainText()
        self.assertEqual(text, new_text)

    def test_cycling(self):
        text = 'e den '
        alt_text = 'i den '
        QTest.keyClicks(self.editor, text)
        self.editor.handle_mode_toggle()  # wordcheck mode

        cur = self.editor.textCursor()
        default_col = cur.charFormat().background().color().getRgb()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)
        selection = self.editor.extraSelections()[0]
        col0 = selection.format.background().color().getRgb()

        QTest.keyClick(self.editor, Qt.Key_R)
        new_text = self.editor.toPlainText()
        selection = self.editor.extraSelections()[0]
        col1 = selection.format.background().color().getRgb()
        self.assertEqual(alt_text, new_text, msg="e to i")
        self.assertNotEqual(col1, default_col, msg="non-default color")
        self.assertNotEqual(col1, col0, msg="changed color")

        QTest.keyClick(self.editor, Qt.Key_E)
        new_text = self.editor.toPlainText()
        selection = self.editor.extraSelections()[0]
        col2 = selection.format.background().color().getRgb()
        self.assertEqual(text, new_text, msg="i to e")
        self.assertEqual(col2, col0, msg="back to same color")

    def test_index_preservation(self):
        text = 'e den '
        alt_text = 'i den '
        QTest.keyClicks(self.editor, text)
        self.editor.handle_mode_toggle()  # wordcheck mode

        cur = self.editor.textCursor()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)

        QTest.keyClick(self.editor, Qt.Key_R)
        new_text = self.editor.toPlainText()
        self.assertEqual(alt_text, new_text, msg="e to i")

        # Move to other word and back.
        cur = self.editor.textCursor()
        cur.setPosition(4)
        self.editor.setTextCursor(cur)

        cur = self.editor.textCursor()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)

        QTest.keyClick(self.editor, Qt.Key_R)
        QTest.keyClick(self.editor, Qt.Key_R)
        QTest.keyClick(self.editor, Qt.Key_R)
        new_text = self.editor.toPlainText()
        self.assertEqual(text, new_text, msg="i to e")


class TestWordcheckModeCapsPreserving(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(regex_map)
        self.editor.autocaps = False

    def test_basic(self):
        text = 'En '
        QTest.keyClicks(self.editor, text)
        self.editor.handle_mode_toggle()  # wordcheck mode

        cur = self.editor.textCursor()
        cur.setPosition(0)
        self.editor.setTextCursor(cur)

        QTest.keyClick(self.editor, Qt.Key_R)
        self.assertEqual(self.editor.toPlainText(), "In ", msg="upper case options maintained")
        QTest.keyClick(self.editor, Qt.Key_R)
        self.assertEqual(self.editor.toPlainText(), "en ", msg="lower case options maintained")


if __name__ == '__main__':
    unittest.main()
