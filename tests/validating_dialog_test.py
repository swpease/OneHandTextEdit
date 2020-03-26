import unittest

from PySide2.QtCore import Qt
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QApplication, QMessageBox, QLabel
from PySide2.QtTest import QTest

from OHTE.validating_dialog import ValidatingDialog


def setUpModule():
    app = QApplication([])


class TestWidget(unittest.TestCase):

    def label_slot(self, text):
        self.label.setText(text)

    def setUp(self) -> None:
        self.label = QLabel()

        validator = QRegExpValidator(r'(x|xxx)')
        help_popup = QMessageBox(QMessageBox.Information, "hi", "hi")
        self.vd = ValidatingDialog(validator, help_popup)
        self.vd.show()
        self.vd.submitted.connect(self.label_slot)

    def test_btns(self):
        self.assertFalse(self.vd.ok_btn.isEnabled())
        self.assertFalse(self.vd.ok_btn.isDefault())
        self.assertTrue(self.vd.help_btn.isDefault())

        QTest.keyClick(self.vd.line_edit, Qt.Key_X)
        self.assertTrue(self.vd.ok_btn.isEnabled())
        self.assertTrue(self.vd.ok_btn.isDefault())
        self.assertFalse(self.vd.help_btn.isDefault())

        QTest.keyClick(self.vd.line_edit, Qt.Key_X)
        self.assertFalse(self.vd.ok_btn.isEnabled())
        self.assertFalse(self.vd.ok_btn.isDefault())
        self.assertTrue(self.vd.help_btn.isDefault())

        QTest.keyClick(self.vd.line_edit, Qt.Key_X)
        self.assertTrue(self.vd.ok_btn.isEnabled())
        self.assertTrue(self.vd.ok_btn.isDefault())
        self.assertFalse(self.vd.help_btn.isDefault())

    def test_ok(self):
        # Relies on default buttons clickable via Enter
        QTest.keyClick(self.vd.line_edit, Qt.Key_X)
        QTest.keyClick(self.vd.line_edit, Qt.Key_Enter)
        self.assertTrue(self.vd.isHidden())
        self.assertEqual(self.label.text(), 'x')

    def test_cancel(self):
        # This is blocking... not sure how to get around it.
        pass

    def test_help(self):
        # This is blocking... not sure how to get around it.
        pass


if __name__ == '__main__':
    unittest.main()
