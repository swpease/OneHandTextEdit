import unittest
import os

from PySide2.QtCore import Qt, QEvent
from PySide2.QtGui import QTextCursor, QKeyEvent
from PySide2.QtWidgets import QApplication, QPlainTextEdit
from PySide2.QtTest import QTest

from textedit import MyPlainTextEdit, Mode
from regex_map import create_regex_map


src = 'test_words.txt'
dest = 'test_out.json'


def setUpModule():
    app = QApplication([])
    words = ["A", "a", "the", "and", "ax", "it's"]
    with open(src, 'w') as f:
        for word in words:
            f.write("%s\n" % word)
    create_regex_map(src, dest)


def tearDownModule():
    os.remove(src)
    os.remove(dest)


class TestInsertMode(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(dest)

    def test_basic(self):
        # e: QKeyEvent = QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier)
        # editor.appendPlainText("Z")
        # editor.event(e)
        QTest.keyClicks(self.editor, 'z')
        self.assertEqual(self.editor.textCursor().block().text(), "z")

    def test_word_replace_trigger(self):
        QTest.keyClicks(self.editor, 'a')
        self.assertEqual(self.editor.textCursor().block().text(), "a", msg="plain a stays a")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'A')
        self.assertEqual(self.editor.textCursor().block().text(), "A", msg="plain A stays A")
        self.editor.document().clear()
        # for whatever reason, python puts A before a, so A is default.
        QTest.keyClicks(self.editor, 'a ')
        self.assertEqual(self.editor.textCursor().block().text(), "A ", msg="space bar coersion")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'a')
        QTest.keyClick(self.editor, Qt.Key_Return)
        self.assertEqual(self.editor.textCursor().block().previous().text(), "A", msg="return btn coersion")
        self.editor.document().clear()
        QTest.keyClicks(self.editor, 'a/')
        self.assertEqual(self.editor.textCursor().block().text(), "A/", msg="slash coersion")

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

    def test_handles_contractions(self):
        QTest.keyClicks(self.editor, 'iy\'l ')
        self.assertEqual(self.editor.textCursor().block().text(), "it\'s ")


    def test_handles_starting_symbols(self):
        QTest.keyClicks(self.editor, '?!3""\'"thi ')
        self.assertEqual(self.editor.textCursor().block().text(), '?!3""\'"the ')

    def test_end_of_word_stripping(self):
        QTest.keyClicks(self.editor, 'thi?!"\' ')
        self.assertEqual(self.editor.textCursor().block().text(), 'the?!"\' ')


class TestModeSwitching(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(dest)

    def test_basic(self):
        self.assertEqual(self.editor.mode, Mode.INSERT)
        QTest.keyClick(self.editor, Qt.Key_E, modifier=Qt.ControlModifier)
        self.assertEqual(self.editor.mode, Mode.WORDCHECK)
        QTest.keyClick(self.editor, Qt.Key_I, modifier=Qt.ControlModifier)
        self.assertEqual(self.editor.mode, Mode.INSERT)


class TestWordcheckModeMovement(unittest.TestCase):
    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(dest)

    def test_move_up(self):
        QTest.keyClick(self.editor, Qt.Key_Return)
        QTest.keyClick(self.editor, Qt.Key_Return)
        QTest.keyClick(self.editor, Qt.Key_E, Qt.ControlModifier)
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
        QTest.keyClick(self.editor, Qt.Key_E, Qt.ControlModifier)
        QTest.keyClick(self.editor, Qt.Key_F)
        QTest.keyClick(self.editor, Qt.Key_J)
        self.assertEqual(self.editor.textCursor().blockNumber(), 2)
        self.assertEqual(self.editor.toPlainText(), "\n\n", msg="text modified")

    def test_move_left(self):
        QTest.keyClicks(self.editor, 'the box')
        QTest.keyClick(self.editor, Qt.Key_E, Qt.ControlModifier)
        QTest.keyClick(self.editor, Qt.Key_S)
        QTest.keyClick(self.editor, Qt.Key_H)
        self.assertEqual(self.editor.textCursor().position(), 0)
        self.assertEqual(self.editor.toPlainText(), "the box", msg="text modified")

    def test_move_right(self):
        QTest.keyClicks(self.editor, 'the box is')
        QTest.keyClick(self.editor, Qt.Key_E, Qt.ControlModifier)
        start_cur = self.editor.textCursor()
        start_cur.setPosition(0)
        self.editor.setTextCursor(start_cur)
        QTest.keyClick(self.editor, Qt.Key_G)
        QTest.keyClick(self.editor, Qt.Key_L)
        self.assertEqual(self.editor.textCursor().position(), 8)
        self.assertEqual(self.editor.toPlainText(), "the box is", msg="text modified")


if __name__ == '__main__':
    unittest.main()
