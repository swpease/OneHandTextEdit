import unittest
from unittest.mock import MagicMock, mock_open, patch
import os
import json

from PySide2.QtCore import QStandardPaths

from src.main.python.main_window import MainWindow
from src.main.python import main


QStandardPaths.locate = MagicMock(return_value='')


DEST = 'regex_map.json'


def setUpModule():
    with open(DEST, 'w') as f:
        f.write("hi")


def tearDownModule():
    os.remove(DEST)


class TestMain(unittest.TestCase):
    # ONLY CALL ONE PER RUN OR ELSE CRASHES B/C QAPP NOT DELETED FOR SOME REASON
    def test_save_dictionary_called_on_close(self):
        MainWindow.dict_modified = True
        main.save_dictionary = MagicMock()
        fake_dict = {'cat': {'default': 'cat', 'words': ['may', 'cat']}}
        json.load = MagicMock(return_value=fake_dict)
        with self.assertRaises(SystemExit) as se:
            main.main()
        main.save_dictionary.assert_called_once()
        main.save_dictionary.assert_called_with(DEST, DEST, fake_dict)

    def test_opens_default_src_when_not_found_in_users_file_system(self):
        open_spy = mock_open()
        with patch('builtins.open', open_spy):
            fake_dict = {'cat': {'default': 'cat', 'words': ['may', 'cat']}}
            json.load = MagicMock(return_value=fake_dict)
            with self.assertRaises(SystemExit) as se:
                main.main()
        open_spy.assert_called_with(DEST)


if __name__ == '__main__':
    unittest.main()
