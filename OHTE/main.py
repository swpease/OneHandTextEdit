import sys
import functools
import json
from typing import Dict

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QStandardPaths, QDir

from OHTE.main_window import MainWindow
from OHTE.regex_map import Entry


def save_dictionary(file_name: str, dict_src: str, regex_map: Dict[str, Entry]):
    """Saves the dictionary if user modified it. Connected to aboutToQuit signal."""
    if MainWindow.dict_modified:
        if dict_src == file_name:  # TODO: change for deploy? check sig too
            app_data_loc: str = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if app_data_loc:  # Qt found a place we could save (may not exist)
                dir_exists = QDir().mkpath(app_data_loc)
                if dir_exists:  # Exists / created
                    abs_dir = QDir(app_data_loc)
                    dict_src = abs_dir.filePath(file_name)

        with open(dict_src, 'w') as f:
            json.dump(regex_map, f)


def main():
    app = QApplication([])

    QApplication.setApplicationName("OneHandTextEdit")
    QApplication.setOrganizationName("PMA")

    file_name = 'regex_map.json'
    dict_src: str = QStandardPaths.locate(QStandardPaths.AppDataLocation, file_name)
    if not dict_src:
        dict_src = file_name  # TODO Change to app's packaged resource for deploy.
    with open(dict_src) as f:
        regex_map: dict = json.load(f)

    app.aboutToQuit.connect(functools.partial(save_dictionary, file_name, dict_src, regex_map))

    main_win = MainWindow(regex_map, dict_src=dict_src)
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

