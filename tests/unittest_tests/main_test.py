import unittest
from unittest.mock import MagicMock
import os
import json

from OHTE.regex_map import create_regex_map
from OHTE.main_window import MainWindow
from OHTE import main


src = 'test_words.txt'
dest = 'test_out.json'
main.DICT_SRC = dest
regex_map: dict = {}
main.REGEX_MAP = regex_map


def setUpModule():
    words = ["e", "i"]
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


class TestSaveDict(unittest.TestCase):
    # only test one of these at a time, or else multiple instances of QApplication are created and it breaks.
    def test_save(self):
        MainWindow.dict_modified = True
        json.dump = MagicMock()
        with self.assertRaises(SystemExit) as se:
            main.main()
        json.dump.assert_called_once()


if __name__ == '__main__':
    unittest.main()
