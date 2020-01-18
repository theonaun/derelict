import os
import time

from PyQt5.Qt import *

import data

class SplashScreen(QSplashScreen):

    def __init__(self, app):
        self._app = app
        QSplashScreen.__init__(self)
        data_path = data.__path__._path[0]
        logo_path = os.path.join(data_path, "brickton_logo.jpg")
        pixmap = QPixmap(logo_path)
        self.setPixmap(pixmap)
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowStaysOnTopHint)
        # COnnect keymanager to allow for updates.
        app.key_manager.splash_update.connect(self.showMessage)

    def showMessage(self, message):
        if message != "sentinel_value":
            super().showMessage(message,
                                alignment=Qt.AlignRight,
                                color=Qt.white)
            self._app.processEvents()
        else:
            QTimer.singleShot(1000, self._fadeout)

    def _fadeout(self):
        '''For whatever reason, pyqt refuses to play nice with loops.'''
        timer = QTimer()
        timer.singleShot(50, lambda: self.setWindowOpacity(.95))
        timer.singleShot(100, lambda: self.setWindowOpacity(.90))
        timer.singleShot(150, lambda: self.setWindowOpacity(.85))
        timer.singleShot(200, lambda: self.setWindowOpacity(.80))
        timer.singleShot(250, lambda: self.setWindowOpacity(.75))
        timer.singleShot(300, lambda: self.setWindowOpacity(.70))
        timer.singleShot(350, lambda: self.setWindowOpacity(.65))
        timer.singleShot(400, lambda: self.setWindowOpacity(.60))
        timer.singleShot(450, lambda: self.setWindowOpacity(.55))
        timer.singleShot(500, lambda: self.setWindowOpacity(.50))
        timer.singleShot(550, lambda: self.setWindowOpacity(.45))
        timer.singleShot(600, lambda: self.setWindowOpacity(.40))
        timer.singleShot(650, lambda: self.setWindowOpacity(.35))
        timer.singleShot(700, lambda: self.setWindowOpacity(.30))
        timer.singleShot(750, lambda: self.setWindowOpacity(.25))
        timer.singleShot(800, lambda: self.setWindowOpacity(.20))
        timer.singleShot(850, lambda: self.setWindowOpacity(.15))
        timer.singleShot(900, lambda: self.setWindowOpacity(.10))
        timer.singleShot(950, lambda: self.setWindowOpacity(.05))
        timer.singleShot(1000, lambda: self.setWindowOpacity(0))
        self._app.processEvents()
        timer.singleShot(1000, self.close)
