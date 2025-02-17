
import sys

from PyQt5.QtWidgets import QApplication

from core.dialog.main_dialog import MainUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ui = TestDesign()
    ui = MainUI()
    ui.show()
    app.exec()
