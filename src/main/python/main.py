import sys
import functools
import json
from typing import Dict

from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QStandardPaths, QDir

from main_window import MainWindow


def save_dictionary(file_name: str, dict_src: str, regex_map, appctxt):
    """Saves the dictionary if user modified it. Connected to aboutToQuit signal."""
    if MainWindow.dict_modified:
        if dict_src == appctxt.get_resource(file_name):
            app_data_loc: str = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if app_data_loc:  # Qt found a place we could save (may not exist)
                dir_exists = QDir().mkpath(app_data_loc)
                if dir_exists:  # Exists / created
                    abs_dir = QDir(app_data_loc)
                    dict_src = abs_dir.filePath(file_name)

        with open(dict_src, 'w') as f:
            json.dump(regex_map, f)


def main():
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

    QApplication.setApplicationName("OneHandTextEdit")
    QApplication.setOrganizationName("PMA")

    file_name = 'regex_map.json'
    dict_src: str = QStandardPaths.locate(QStandardPaths.AppDataLocation, file_name)
    if not dict_src:
        dict_src = appctxt.get_resource(file_name)
    with open(dict_src) as f:
        regex_map: dict = json.load(f)

    appctxt.app.aboutToQuit.connect(functools.partial(save_dictionary, file_name, dict_src, regex_map, appctxt))

    main_win = MainWindow(regex_map, dict_src=dict_src)
    main_win.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

