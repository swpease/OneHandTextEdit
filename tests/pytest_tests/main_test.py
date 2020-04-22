import pytest
from unittest.mock import MagicMock, mock_open, patch

from PySide2.QtCore import QStandardPaths, QDir

from OHTE.main_window import MainWindow
from OHTE import main


class TestSave(object):
    def test_saves_to_app_data_location(self, tmp_path):
        open_spy = mock_open()
        with patch('builtins.open', open_spy):
            QStandardPaths.writableLocation = MagicMock(return_value=str(tmp_path))
            MainWindow.dict_modified = True
            main.save_dictionary('x.json', 'x.json', {'k': 'l'})
        open_spy.assert_called_with(QDir(str(tmp_path)).filePath('x.json'), 'w')

    def test_saves_internally_if_unable_to_save_to_user_filesystem(self, tmp_path):
        open_spy = mock_open()
        with patch('builtins.open', open_spy):
            QStandardPaths.writableLocation = MagicMock(return_value=str(tmp_path))
            MainWindow.dict_modified = True
            main.save_dictionary('x.json', 'y.json', {'k': 'l'})  # gets you to the same place...
        open_spy.assert_called_with('y.json', 'w')
