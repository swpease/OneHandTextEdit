import json
from typing import Callable

from PySide2.QtCore import QFile, QSaveFile, QFileInfo, QPoint, QSettings, QSize, Qt, QTextStream, QRegExp
from PySide2.QtGui import QIcon, QKeySequence, QRegExpValidator
from PySide2.QtWidgets import QAction, QApplication, QFileDialog, QMainWindow, QMessageBox, QDialog, QTextEdit
from PySide2.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from OHTE.textedit import MyPlainTextEdit
from OHTE.validating_dialog import ValidatingDialog
from OHTE.regex_map import add_word_to_dict, del_word_from_dict

import ohte_rc


class MainWindow(QMainWindow):
    sequence_number = 1
    window_list = []
    dict_modified = False

    def __init__(self, regex_map, file_name='', dict_src='regex_map.json'):
        super().__init__()

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.is_untitled = True
        self.cur_file = ''
        self.dict_src = dict_src
        self.regex_map = regex_map
        self.text_edit = MyPlainTextEdit(regex_map)
        self.md_text_edit = QTextEdit()
        self.md_text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()

        self.read_settings()

        # self.text_edit.document().contentsChanged.connect(self.document_was_modified)
        self.text_edit.textChanged.connect(self.document_was_modified)
        self.text_edit.textChanged.connect(lambda: self.md_text_edit.document().setMarkdown(self.text_edit.document().toPlainText()))

        if file_name:
            self.load_file(file_name)
        else:
            self.set_current_file('')

    def closeEvent(self, event):
        if self.maybe_save():
            self.write_settings()
            # TODO: move to slot.
            if MainWindow.dict_modified:
                with open(self.dict_src, 'w') as f:
                    json.dump(self.regex_map, f)
                MainWindow.dict_modified = False
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

    def print_(self):
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec_() == QDialog.Accepted:
            self.text_edit.print_(printer)

    def print_markdown(self):
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("Print as Markdown")  # Does nothing on Mac
        if print_dialog.exec_() == QDialog.Accepted:
            self.md_text_edit.print_(printer)

    def show_markdown(self):
        self.md_text_edit.move(self.x() + self.size().width(), self.y())
        self.md_text_edit.resize(self.size())
        self.md_text_edit.show()
        self.md_text_edit.raise_()
        self.md_text_edit.activateWindow()

    # noinspection PyAttributeOutsideInit
    def create_actions(self):
        # File
        self.new_act = QAction(QIcon(':/images/new.png'), "&New", self,
                               statusTip="Create a new file",
                               triggered=self.new_file)
        self.new_act.setShortcuts([QKeySequence.New, QKeySequence(Qt.CTRL + Qt.Key_B)])

        self.open_act = QAction(QIcon(':/images/open.png'), "&Open...", self,
                                statusTip="Open an existing file",
                                triggered=self.open)
        self.open_act.setShortcuts([QKeySequence.Open, QKeySequence(Qt.CTRL + Qt.Key_T)])

        self.save_act = QAction(QIcon(':/images/save.png'), "&Save", self,
                                statusTip="Save the document to disk", triggered=self.save)
        self.save_act.setShortcuts([QKeySequence.Save, QKeySequence(Qt.CTRL + Qt.Key_L)])

        self.save_as_act = QAction("Save &As...", self,
                                   statusTip="Save the document under a new name",
                                   triggered=self.save_as)
        self.save_as_act.setShortcuts([QKeySequence.SaveAs, QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_L)])

        self.print_act = QAction(QIcon(':/images/print.png'), "&Print", self,
                                 statusTip="Print the document",
                                 triggered=self.print_)
        self.print_act.setShortcuts([QKeySequence.Print, QKeySequence(Qt.CTRL + Qt.Key_R)])

        self.print_markdown_act = QAction("Print &Markdown", self, triggered=self.print_markdown)
        self.print_markdown_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_P),
                                              QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_R)])

        self.close_act = QAction("&Close", self,
                                 statusTip="Close this window", triggered=self.close)
        self.close_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.Key_W), QKeySequence(Qt.CTRL + Qt.Key_BracketRight)])

        self.exit_act = QAction("E&xit", self,
                                statusTip="Exit the application",
                                triggered=QApplication.instance().closeAllWindows)
        self.exit_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.Key_Q), QKeySequence(Qt.CTRL + Qt.Key_BracketLeft)])

        # Edit
        self.undo_act = QAction("Undo", self,
                                enabled=False,
                                triggered=self.text_edit.undo)
        self.undo_act.setShortcuts([QKeySequence.Undo, QKeySequence(Qt.CTRL + Qt.Key_Slash)])

        self.redo_act = QAction("Redo", self,
                                enabled=False,
                                triggered=self.text_edit.redo)
        self.redo_act.setShortcuts([QKeySequence.Redo, QKeySequence(Qt.CTRL + Qt.Key_Y)])

        self.cut_act = QAction(QIcon(':/images/cut.png'), "Cu&t", self,
                               enabled=False,
                               statusTip="Cut the current selection's contents to the clipboard",
                               triggered=self.text_edit.cut)
        self.cut_act.setShortcuts([QKeySequence.Cut, QKeySequence(Qt.CTRL + Qt.Key_Period)])

        self.copy_act = QAction(QIcon(':/images/copy.png'), "&Copy", self,
                                enabled=False,
                                statusTip="Copy the current selection's contents to the clipboard",
                                triggered=self.text_edit.copy)
        self.copy_act.setShortcuts([QKeySequence.Copy, QKeySequence(Qt.CTRL + Qt.Key_Comma)])

        self.paste_act = QAction(QIcon(':/images/paste.png'), "&Paste", self,
                                 statusTip="Paste the clipboard's contents into the current selection",
                                 triggered=self.text_edit.paste)
        self.paste_act.setShortcuts([QKeySequence.Paste, QKeySequence(Qt.CTRL + Qt.Key_M)])

        self.select_all_act = QAction("Select All", self, triggered=self.text_edit.selectAll)
        self.select_all_act.setShortcuts([QKeySequence.SelectAll, QKeySequence(Qt.CTRL + Qt.Key_Semicolon)])

        # About
        self.about_act = QAction("&About", self,
                                 statusTip="Show the application's About box",
                                 triggered=self.about)

        self.about_Qt_act = QAction("About &Qt", self,
                                    statusTip="Show the Qt library's About box",
                                    triggered=QApplication.instance().aboutQt)

        # View
        self.zoom_in_act = QAction("Zoom In", self,
                                   triggered=self.text_edit.zoomIn,
                                   shortcut=QKeySequence.ZoomIn)

        self.zoom_out_act = QAction("Zoom Out", self,
                                    triggered=self.text_edit.zoomOut,
                                    shortcut=QKeySequence.ZoomOut)

        self.show_markdown_act = QAction("Show Markdown", self, triggered=self.show_markdown)
        self.show_markdown_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_M),
                                             QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_C)])

        # Dictionary
        self.add_word_act = QAction(QIcon(':/images/icons8-plus-64.png'), "Add Word", self,
                                    statusTip="Add a word to the dictionary",
                                    triggered=self.show_add_word_dialog)
        self.add_word_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.Key_J), QKeySequence(Qt.CTRL + Qt.Key_G)])

        self.delete_word_act = QAction(QIcon(':/images/icons8-delete-64.png'), "Delete Word", self,
                                       statusTip="Delete a word from the dictionary",
                                       triggered=self.show_del_word_dialog)
        self.delete_word_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.Key_D), QKeySequence(Qt.CTRL + Qt.Key_U)])

        self.toggle_mode_act = QAction("Switch Mode", self,
                                       triggered=self.text_edit.handle_mode_toggle)
        self.toggle_mode_act.setShortcuts([QKeySequence(Qt.CTRL + Qt.Key_I), QKeySequence(Qt.CTRL + Qt.Key_E)])

        # Connections
        self.text_edit.copyAvailable.connect(self.cut_act.setEnabled)
        self.text_edit.copyAvailable.connect(self.copy_act.setEnabled)
        self.text_edit.undoAvailable.connect(self.undo_act.setEnabled)
        self.text_edit.redoAvailable.connect(self.redo_act.setEnabled)

    # noinspection PyAttributeOutsideInit
    def create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_act)
        self.file_menu.addAction(self.open_act)
        self.file_menu.addAction(self.save_act)
        self.file_menu.addAction(self.save_as_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.close_act)
        self.file_menu.addAction(self.exit_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.print_act)
        self.file_menu.addAction(self.print_markdown_act)

        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.undo_act)
        self.edit_menu.addAction(self.redo_act)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.cut_act)
        self.edit_menu.addAction(self.copy_act)
        self.edit_menu.addAction(self.paste_act)
        self.edit_menu.addAction(self.select_all_act)

        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.show_markdown_act)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.zoom_in_act)
        self.view_menu.addAction(self.zoom_out_act)

        self.dict_menu = self.menuBar().addMenu('&Dictionary')
        self.dict_menu.addAction(self.add_word_act)
        self.dict_menu.addAction(self.delete_word_act)
        self.dict_menu.addSeparator()
        self.dict_menu.addAction(self.toggle_mode_act)

        self.menuBar().addSeparator()

        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.about_act)
        self.help_menu.addAction(self.about_Qt_act)

    # noinspection PyAttributeOutsideInit
    def create_tool_bars(self):
        self.file_tool_bar = self.addToolBar("File")
        self.file_tool_bar.addAction(self.new_act)
        self.file_tool_bar.addAction(self.open_act)
        self.file_tool_bar.addAction(self.save_act)
        self.file_tool_bar.addAction(self.print_act)

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
            MainWindow.dict_modified = True
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
            MainWindow.dict_modified = True
        else:
            QMessageBox.information(self, "One Hand Text Edit", "Word not found in dictionary")


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    dict_src = 'regex_map.json'
    with open(dict_src) as f:
        regx_map: dict = json.load(f)

    mainWin = MainWindow(regx_map, dict_src=dict_src)
    mainWin.show()
    sys.exit(app.exec_())
