# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'brickton_about.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_about_dialog(object):
    def setupUi(self, about_dialog):
        about_dialog.setObjectName("about_dialog")
        about_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        about_dialog.resize(600, 600)
        about_dialog.setMinimumSize(QtCore.QSize(600, 600))
        about_dialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(about_dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(about_dialog)
        self.label.setMinimumSize(QtCore.QSize(500, 500))
        self.label.setMaximumSize(QtCore.QSize(500, 500))
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)

        self.retranslateUi(about_dialog)
        QtCore.QMetaObject.connectSlotsByName(about_dialog)

    def retranslateUi(self, about_dialog):
        _translate = QtCore.QCoreApplication.translate
        about_dialog.setWindowTitle(_translate("about_dialog", "About"))
        self.label.setText(_translate("about_dialog", "<html><head/><body><p><span style=\" font-weight:600;\">Brickton</span></p><p>Version 2.0.1</p><p>Brickton is a Qt-based one-time pad communication program and key distribution protocol.</p><p>Copyright (C) 2016, Theo Naunheim</p><p>This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. </p><p>This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. </p><p>You should have received a copy of the GNU General Public License along with this program. If not, see &lt;<span style=\" font-family:\'Courier New,courier\';\">http://www.gnu.org/licenses/&gt;.</span></p><p><br/></p></body></html>"))

