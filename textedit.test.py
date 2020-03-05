import unittest
import os

from PySide2.QtCore import Qt, QEvent
from PySide2.QtGui import QTextCursor, QKeyEvent
from PySide2.QtWidgets import QApplication, QPlainTextEdit
from PySide2.QtTest import QTest

from textedit import MyPlainTextEdit, Mode
from regex_map import create_regex_map


class TestInsertMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = QApplication([])
        cls.src = 'test_words.txt'
        cls.dest = 'test_out.json'
        words = ["A", "a", "the", "and", "ax", "it's"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map(cls.src, cls.dest)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(self.dest)

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
    @classmethod
    def setUpClass(cls) -> None:
        cls.src = 'test_words.txt'
        cls.dest = 'test_out.json'
        words = ["A", "a", "the", "and", "ax"]
        with open(cls.src, 'w') as f:
            for word in words:
                f.write("%s\n" % word)
        create_regex_map(cls.src, cls.dest)

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.src)
        os.remove(cls.dest)

    def setUp(self) -> None:
        self.editor = MyPlainTextEdit(self.dest)

    def test_basic(self):
        self.assertEqual(self.editor.mode, Mode.INSERT)
        QTest.keyClick(self.editor, Qt.Key_E, modifier=Qt.ControlModifier)
        self.assertEqual(self.editor.mode, Mode.WORDCHECK)
        QTest.keyClick(self.editor, Qt.Key_I, modifier=Qt.ControlModifier)
        self.assertEqual(self.editor.mode, Mode.INSERT)


if __name__ == '__main__':
    unittest.main()
