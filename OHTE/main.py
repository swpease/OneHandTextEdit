import sys
import json
from PySide2.QtWidgets import QApplication
from OHTE.main_window import MainWindow


app = QApplication([])

dict_src = 'regex_map.json'
with open(dict_src) as f:
    regex_map: dict = json.load(f)

main_win = MainWindow(regex_map, dict_src=dict_src)
main_win.show()
sys.exit(app.exec_())
