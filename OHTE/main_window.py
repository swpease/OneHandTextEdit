import json
from typing import Callable

from PySide2.QtCore import QFile, QSaveFile, QFileInfo, QPoint, QSettings, QSize, Qt, QTextStream, QRegExp
from PySide2.QtGui import QIcon, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import QAction, QApplication, QFileDialog, QMainWindow, QMessageBox

from OHTE.textedit import MyPlainTextEdit
from OHTE.validating_dialog import ValidatingDialog
from OHTE.regex_map import add_word_to_dict, del_word_from_dict

import ohte_rc


class MainWindow(QMainWindow):
    sequence_number = 1
    window_list = []

    def __init__(self, regex_map, file_name=''):
        super().__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.is_untitled = True
        self.cur_file = ''
        self.dict_modified = False
        self.regex_map = regex_map
        self.text_edit = MyPlainTextEdit(regex_map)
        self.setCentralWidget(self.text_edit)

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()

        self.read_settings()

        # self.text_edit.document().contentsChanged.connect(self.document_was_modified)
        self.text_edit.textChanged.connect(self.document_was_modified)
        if file_name:
            self.load_file(file_name)
        else:
            self.set_current_file('')

    def closeEvent(self, event):
        if self.maybe_save():
            self.write_settings()
            event.accept()
        else:
            event.ignore()

    def document_was_modified(self):
        self.setWindowModified(True)

    def new_file(self):
        other = MainWindow(self.regex_map)
        MainWindow.window_list.append(other)
        other.move(self.x() + 40, self.y() + 40)
        other.show()

    def open(self):
        file_name, _ = QFileDialog.getOpenFileName(self, filter="Text files (*.txt)")
        if file_name:
            existing = self.find_main_window(file_name)
            if existing is not None:
                existing.show()
                existing.raise_()
                existing.activateWindow()
                return

            if self.is_untitled and self.text_edit.document().isEmpty() and not self.isWindowModified():
                self.load_file(file_name)
            else:
                other = MainWindow(self.regex_map, file_name)
                if other.is_untitled:  # impossible?
                    del other
                    return

                MainWindow.window_list.append(other)
                other.move(self.x() + 40, self.y() + 40)
                other.show()

    def about(self):
        QMessageBox.about(self, "About OneHandTextEdit", "Aptly named, a text editor for use with one hand.")

    def create_actions(self):
        self.new_act = QAction(QIcon(':/images/new.png'), "&New", self,
                               shortcut=QKeySequence.New, statusTip="Create a new file",
                               triggered=self.new_file)

        self.open_act = QAction(QIcon(':/images/open.png'), "&Open...", self,
                                shortcut=QKeySequence.Open, statusTip="Open an existing file",
                                triggered=self.open)

        self.save_act = QAction(QIcon(':/images/save.png'), "&Save", self,
                                shortcut=QKeySequence.Save,
                                statusTip="Save the document to disk", triggered=self.save)

        self.save_as_act = QAction("Save &As...", self,
                                   shortcut=QKeySequence.SaveAs,
                                   statusTip="Save the document under a new name",
                                   triggered=self.save_as)

        self.close_act = QAction("&Close", self, shortcut="Ctrl+W",
                                 statusTip="Close this window", triggered=self.close)

        self.exit_act = QAction("E&xit", self, shortcut="Ctrl+Q",
                                statusTip="Exit the application",
                                triggered=QApplication.instance().closeAllWindows)

        self.cut_act = QAction(QIcon(':/images/cut.png'), "Cu&t", self,
                               enabled=False, shortcut=QKeySequence.Cut,
                               statusTip="Cut the current selection's contents to the clipboard",
                               triggered=self.text_edit.cut)

        self.copy_act = QAction(QIcon(':/images/copy.png'), "&Copy", self,
                                enabled=False, shortcut=QKeySequence.Copy,
                                statusTip="Copy the current selection's contents to the clipboard",
                                triggered=self.text_edit.copy)

        self.paste_act = QAction(QIcon(':/images/paste.png'), "&Paste", self,
                                 shortcut=QKeySequence.Paste,
                                 statusTip="Paste the clipboard's contents into the current selection",
                                 triggered=self.text_edit.paste)

        self.about_act = QAction("&About", self,
                                 statusTip="Show the application's About box",
                                 triggered=self.about)

        self.about_Qt_act = QAction("About &Qt", self,
                                    statusTip="Show the Qt library's About box",
                                    triggered=QApplication.instance().aboutQt)

        self.add_word_act = QAction(QIcon(':/images/icons8-plus-64.png'), "Add Word", self,
                                    statusTip="Add a word to the dictionary",
                                    triggered=self.show_add_word_dialog)

        self.delete_word_act = QAction(QIcon(':/images/icons8-delete-64.png'), "Delete Word", self,
                                       statusTip="Delete a word from the dictionary",
                                       triggered=self.show_del_word_dialog)

        self.text_edit.copyAvailable.connect(self.cut_act.setEnabled)
        self.text_edit.copyAvailable.connect(self.copy_act.setEnabled)

    def create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_act)
        self.file_menu.addAction(self.open_act)
        self.file_menu.addAction(self.save_act)
        self.file_menu.addAction(self.save_as_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.close_act)
        self.file_menu.addAction(self.exit_act)

        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.cut_act)
        self.edit_menu.addAction(self.copy_act)
        self.edit_menu.addAction(self.paste_act)

        self.dict_menu = self.menuBar().addMenu('&Dictionary')
        self.dict_menu.addAction(self.add_word_act)
        self.dict_menu.addAction(self.delete_word_act)

        self.menuBar().addSeparator()

        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.about_act)
        self.help_menu.addAction(self.about_Qt_act)

    def create_tool_bars(self):
        self.file_tool_bar = self.addToolBar("File")
        self.file_tool_bar.addAction(self.new_act)
        self.file_tool_bar.addAction(self.open_act)
        self.file_tool_bar.addAction(self.save_act)

        self.edit_tool_bar = self.addToolBar("Edit")
        self.edit_tool_bar.addAction(self.cut_act)
        self.edit_tool_bar.addAction(self.copy_act)
        self.edit_tool_bar.addAction(self.paste_act)

        self.dict_tool_bar = self.addToolBar('Dictionary')
        self.dict_tool_bar.addAction(self.add_word_act)
        self.dict_tool_bar.addAction(self.delete_word_act)

    def create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def read_settings(self):
        settings = QSettings('PMA', 'OneHandTextEdit')
        pos = settings.value('pos', QPoint(200, 200))
        size = settings.value('size', QSize(400, 400))
        self.move(pos)
        self.resize(size)

    def write_settings(self):
        settings = QSettings('PMA', 'OneHandTextEdit')
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())

    def maybe_save(self):
        if self.text_edit.document().isModified():
            ret = QMessageBox.warning(self, "OneHandTextEdit",
                    "The document has been modified.\nDo you want to save your changes?",
                    QMessageBox.Save | QMessageBox.Discard |
                    QMessageBox.Cancel)

            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False

        return True

    def save(self):
        if self.is_untitled:
            return self.save_as()
        else:
            return self.save_file(self.cur_file)

    def save_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save As", self.cur_file)
        if not file_name:
            return False

        return self.save_file(file_name)

    def save_file(self, file_name):
        """

        :param file_name: A canonical file path.
        :return: boolean for use in closeEvent method.
        """
        error = None

        QApplication.setOverrideCursor(Qt.WaitCursor)
        file = QSaveFile(file_name)
        if file.open(QFile.WriteOnly | QFile.Text):
            outstr = QTextStream(file)
            outstr << self.text_edit.toPlainText()
            if not file.commit():
                error = "Cannot write file {}:\n{}.".format(file_name, file.errorString())
        else:
            error = "Cannot open file {}:\n{}.".format(file_name, file.errorString())
        QApplication.restoreOverrideCursor()

        if error:
            QMessageBox.warning(self, "OneHandTextEdit", error)
            return False

        self.set_current_file(file_name)
        self.statusBar().showMessage("File saved", 2000)
        return True

    def load_file(self, file_name):
        file = QFile(file_name)
        if not file.open(QFile.ReadOnly | QFile.Text):
            QMessageBox.warning(self, "OneHandTextEdit",
                                "Cannot read file {}:\n{}.".format(file_name, file.errorString()))
            return

        instr = QTextStream(file)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.text_edit.setPlainText(instr.readAll())
        QApplication.restoreOverrideCursor()

        self.set_current_file(file_name)
        self.statusBar().showMessage("File loaded", 2000)

    def set_current_file(self, file_name: str):
        self.is_untitled = not file_name
        if self.is_untitled:
            self.cur_file = "document{!s}.txt".format(MainWindow.sequence_number)
            MainWindow.sequence_number += 1
        else:
            self.cur_file = QFileInfo(file_name).canonicalFilePath()

        self.text_edit.document().setModified(False)
        self.setWindowModified(False)

        stripped_name = QFileInfo(self.cur_file).fileName()
        self.setWindowTitle("{}[*]".format(stripped_name))

    def find_main_window(self, file_name):
        canonical_file_path = QFileInfo(file_name).canonicalFilePath()

        for widget in QApplication.instance().topLevelWidgets():
            if isinstance(widget, MainWindow) and widget.cur_file == canonical_file_path:
                return widget

        return

    def show_validating_dialog(self, input_label: str, handler: Callable[[str], None]):
        regex = QRegExp(r'[A-Za-z]+([A-Za-z\'-]+[A-Za-z]+|[A-Za-z]*)')
        validator = QRegExpValidator(regex)
        # TODO set VD as parent.
        help_dialog = QMessageBox(QMessageBox.Information, "OneHandTextEdit",
                                  "A word can only contain letters (upper or lower case) and "
                                  "contain (but not start or end with) - (dashes) and ' (apostrophes).",
                                  buttons=QMessageBox.Ok)
        dialog = ValidatingDialog(validator, help_dialog, input_label=input_label, parent=self)
        dialog.submitted.connect(handler)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_add_word_dialog(self):
        self.show_validating_dialog("Add word:", self.handle_add_word)

    def show_del_word_dialog(self):
        self.show_validating_dialog("Remove word:", self.handle_delete_word)

    def handle_add_word(self, word: str):
        """
        Adds word to dictionary and marks dictionary as modified.
        :param word: Word to add to dictionary.
        :return:
        """
        added: bool = add_word_to_dict(word, self.regex_map)
        if added:
            self.dict_modified = True
        else:
            QMessageBox.information(self, "One Hand Text Edit", "Word already in your dictionary")

    def handle_delete_word(self, word: str):
        """
        Deletes word from dictionary and marks dictionary as modified.
        :param word: Word to remove from dictionary.
        :return:
        """
        deleted: bool = del_word_from_dict(word, self.regex_map)
        if deleted:
            self.dict_modified = True
        else:
            QMessageBox.information(self, "One Hand Text Edit", "Word not found in dictionary")


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    with open('regex_map.json') as f:
        regx_map: dict = json.load(f)

    mainWin = MainWindow(regx_map)
    mainWin.show()
    sys.exit(app.exec_())
