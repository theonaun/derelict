#!/usr/bin/env python3

import sys

from PyQt5.Qt import QApplication
from PyQt5.Qt import QDialog
from PyQt5.Qt import QMainWindow
from PyQt5.Qt import QTimer

from gui.splash import SplashScreen
from gui.main_gui import Ui_MainWindow
from gui.about_gui import Ui_about_dialog

from utilities.key_manager import KeyManager
from utilities.client import Client
from utilities.server import Server
from utilities.codec import Codec

from logic.key_logic import KeyLogic
from logic.comm_logic import CommunicationLogic


class Application(QApplication):

    def __init__(self, args=[]):
        QApplication.__init__(self, args)
        self.VERSION = '0.10.0'
        self.base_window = QMainWindow()
        self.ui_main_window = Ui_MainWindow()
        self.key_manager = KeyManager(self)
        self.codec = Codec(self)
        self.client = Client(self)
        self.server = Server(self)
# DEBUG #         self.server = Server(self)

    def run_splash_processes(self):
        self.key_manager.load_keys()

    def setup(self):
        self.ui_main_window.setupUi(self.base_window)
        self.ui_main_window.actionExit.triggered.connect(self.quit)
        self.key_logic = KeyLogic(self)
        self.key_logic.setup()
        self.comm_logic = CommunicationLogic(self)
        self.comm_logic.setup()
        # About window.
        self.about_dialog = QDialog()
        self.about_ui = Ui_about_dialog()
        self.about_ui.setupUi(self.about_dialog)
        self.ui_main_window.actionAbout.triggered.connect(self.about_dialog.show)

    def run(self):
        self.exec_()
        self.shutdown()

    def shutdown(self):
        pass


if __name__ == '__main__':
    # Create app
    app = Application()
    # Create splash
    splash = SplashScreen(app)
    splash.show()
    # Setup app.
    app.run_splash_processes()
    # Show main window
    app.setup()
    timer = QTimer()
    timer.singleShot(2000, app.base_window.show)
    timer.singleShot(2000, app.base_window.raise_)
    timer.singleShot(2000, app.base_window.activateWindow)
    # Run application
    sys.exit(app.run())