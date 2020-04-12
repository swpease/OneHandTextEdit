import sys
import json
from PySide2.QtWidgets import QApplication
from OHTE.main_window import MainWindow


def _save_dictionary():
    """Saves the dictionary if user modified it. Connected to aboutToQuit signal.
       DICT_SRC and REGEX_MAP taken from outer scope.
    """
    if MainWindow.dict_modified:
        with open(DICT_SRC, 'w') as f:
            json.dump(REGEX_MAP, f)


def main():
    app = QApplication([])

    app.aboutToQuit.connect(_save_dictionary)

    main_win = MainWindow(REGEX_MAP, dict_src=DICT_SRC)
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    DICT_SRC = 'regex_map.json'
    with open(DICT_SRC) as f:
        REGEX_MAP: dict = json.load(f)

    main()
