# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/huaicai/atom/cad/src/GroundPropDialog.ui'
#
# Created: Tue Sep 28 12:02:22 2004
#      by: The PyQt User Interface Compiler (pyuic) 3.12
#
# WARNING! All changes made in this file will be lost!


from qt import *

image0_data = \
    "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d" \
    "\x49\x48\x44\x52\x00\x00\x00\x16\x00\x00\x00\x16" \
    "\x08\x06\x00\x00\x00\xc4\xb4\x6c\x3b\x00\x00\x01" \
    "\xdc\x49\x44\x41\x54\x78\x9c\xed\x95\xbf\x6f\xda" \
    "\x40\x18\x40\xdf\x45\x54\x71\xc7\x66\x81\x20\x45" \
    "\xa9\xd8\x88\x17\x26\x24\xbb\x62\x00\x4a\xba\xa4" \
    "\x52\x5a\x24\x48\x3d\x32\xe3\x89\x81\x29\xa0\x46" \
    "\xe9\xc0\x40\x93\x36\xa3\x49\x47\x8b\xa1\x19\xd9" \
    "\x9a\x09\xc9\x64\x24\x03\x12\x2c\x0c\x41\x32\x7f" \
    "\x42\x61\xba\x4e\x58\x20\x5a\x4c\x52\xba\xf5\x6d" \
    "\xf7\xeb\xdd\x77\x77\xdf\xdd\x09\xc7\x71\xf8\x17" \
    "\x6c\x3d\xa6\x73\xe0\x59\x40\x6e\x54\x2c\xb6\x84" \
    "\xac\x56\xab\x32\xfb\x3e\xcb\xf5\xb7\x6b\x29\x91" \
    "\xbe\x13\xac\x25\xae\x9c\x56\x08\x85\x42\x5c\x7e" \
    "\xb9\x64\xd0\x1f\xd0\x6c\x36\x7d\xc7\xf8\x8a\xb7" \
    "\x95\x6d\xd9\xef\xf7\x39\x7e\x77\x8c\xa6\x69\xa4" \
    "\xd2\x29\xee\x3a\x77\xbe\xe2\x80\x5f\x87\xe9\x64" \
    "\x2a\x0e\xdf\x1c\xca\x8b\xcf\x17\xdc\xa7\xef\xb9" \
    "\xf9\x7e\x43\x2e\x97\xfb\xfb\x88\x01\x0a\x85\x02" \
    "\xfa\x2b\x9d\xb3\x8f\x67\x9c\x7c\x38\xe1\xe8\xed" \
    "\xd1\x66\xc4\x02\x21\xe2\xf1\x38\x00\xd1\x68\x94" \
    "\xe9\x64\x2a\x36\x22\x7e\x0a\xff\xc5\x1e\x5e\xba" \
    "\xe9\xba\xee\xdd\x26\x55\x55\xb1\x2c\xcb\xf7\x80" \
    "\x66\x94\xcb\x65\xd9\x6e\xb7\xbd\xb2\xe3\x38\x62" \
    "\x29\x62\xab\x61\x3d\x4a\x0a\x50\xab\xd5\x84\xd5" \
    "\xb0\x08\x06\x83\x5e\xdd\x82\xd8\x6a\x58\x54\x4e" \
    "\x2b\xb8\x63\x77\xed\xc7\x06\xc0\x1d\xbb\xf2\xea" \
    "\xeb\x15\xe7\x9f\xce\x97\xc5\xaa\xaa\xa2\x1e\xa8" \
    "\xc2\x30\x0c\xcc\xa2\xb9\xb6\xdc\x1d\xbb\xd2\x2c" \
    "\x9a\x64\x32\x19\xd4\x03\x55\x24\x12\x09\x60\x6e" \
    "\x8f\x67\xcb\xcf\x66\xb3\x02\x90\x66\xd1\x24\x9f" \
    "\xcf\xcb\xbd\xbd\x3d\xf6\x5f\xee\x33\x7a\x18\x01" \
    "\x30\x7a\x18\xa1\x28\x8a\x1c\xf4\x07\xb8\xae\x8b" \
    "\x6d\xdb\x18\x86\x31\x1b\x47\xad\x56\x13\x0b\xe2" \
    "\x79\x66\x72\xdb\xb6\xbd\xd5\xcc\x68\xb5\x5a\xd0" \
    "\x82\x5e\xaf\x07\xb0\x20\x9d\x47\xac\xfa\x41\xdc" \
    "\xb1\x2b\x3b\x4e\x87\x7a\xbd\xbe\xd4\x56\x2a\x95" \
    "\xd0\x74\x8d\xf0\x6e\xf8\xb7\x07\xbd\xf2\x75\x0b" \
    "\xef\x86\x45\x32\x95\x94\x08\xb8\xfd\x71\x4b\xb7" \
    "\xdb\x25\x16\x8b\x91\x7e\x9d\x26\x99\x4c\xb2\xf3" \
    "\x62\xe7\x8f\xd9\xb3\x32\xe2\x19\xca\x73\x45\x0e" \
    "\x87\x43\x3a\x4e\x07\x4d\xd7\x88\x44\x22\x4c\x7e" \
    "\x4e\x56\xa6\xe4\x5a\xe2\xa7\xf0\x0b\x4f\xe7\xa9" \
    "\xed\xa4\xbd\x35\x69\x00\x00\x00\x00\x49\x45\x4e" \
    "\x44\xae\x42\x60\x82"

class GroundPropDialog(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        self.image0 = QPixmap()
        self.image0.loadFromData(image0_data,"PNG")
        if not name:
            self.setName("GroundPropDialog")

        self.setIcon(self.image0)
        self.setSizeGripEnabled(1)


        self.okPushButton = QPushButton(self,"okPushButton")
        self.okPushButton.setGeometry(QRect(21,101,82,27))
        self.okPushButton.setAutoDefault(1)
        self.okPushButton.setDefault(1)

        self.cancelPushButton = QPushButton(self,"cancelPushButton")
        self.cancelPushButton.setGeometry(QRect(119,101,82,27))
        self.cancelPushButton.setAutoDefault(1)
        self.cancelPushButton.setDefault(0)

        self.colorPixmapLabel = QLabel(self,"colorPixmapLabel")
        self.colorPixmapLabel.setGeometry(QRect(223,51,40,27))
        self.colorPixmapLabel.setPaletteBackgroundColor(QColor(0,0,0))
        self.colorPixmapLabel.setScaledContents(1)

        self.colorTextLabel = QLabel(self,"colorTextLabel")
        self.colorTextLabel.setGeometry(QRect(171,51,44,27))
        self.colorTextLabel.setAlignment(QLabel.AlignVCenter | QLabel.AlignRight)

        self.nameTextLabel = QLabel(self,"nameTextLabel")
        self.nameTextLabel.setGeometry(QRect(11,11,42,26))
        self.nameTextLabel.setAlignment(QLabel.AlignVCenter | QLabel.AlignRight)

        self.nameLineEdit = QLineEdit(self,"nameLineEdit")
        self.nameLineEdit.setEnabled(1)
        self.nameLineEdit.setGeometry(QRect(58,11,211,21))
        self.nameLineEdit.setFrameShape(QLineEdit.LineEditPanel)
        self.nameLineEdit.setFrameShadow(QLineEdit.Sunken)

        self.colorSelectorPushButton = QPushButton(self,"colorSelectorPushButton")
        self.colorSelectorPushButton.setEnabled(1)
        self.colorSelectorPushButton.setGeometry(QRect(272,51,30,27))

        self.atomsTextLabel = QLabel(self,"atomsTextLabel")
        self.atomsTextLabel.setGeometry(QRect(11,51,42,23))
        self.atomsTextLabel.setMouseTracking(0)

        self.atomsComboBox = QComboBox(0,self,"atomsComboBox")
        self.atomsComboBox.setGeometry(QRect(59,51,85,23))

        self.applyPushButton = QPushButton(self,"applyPushButton")
        self.applyPushButton.setEnabled(0)
        self.applyPushButton.setGeometry(QRect(217,101,82,27))

        self.languageChange()

        self.resize(QSize(339,161).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.cancelPushButton,SIGNAL("clicked()"),self,SLOT("reject()"))
        self.connect(self.okPushButton,SIGNAL("clicked()"),self,SLOT("accept()"))
        self.connect(self.colorSelectorPushButton,SIGNAL("clicked()"),self.changeGroundColor)
        self.connect(self.nameLineEdit,SIGNAL("textChanged(const QString&)"),self.propertiesChanged)
        self.connect(self.applyPushButton,SIGNAL("clicked()"),self.applyButtonPressed)



    def languageChange(self):
        self.setCaption(self.__tr("Ground Properties"))
        self.okPushButton.setText(self.__tr("&OK"))
        self.okPushButton.setAccel(self.__tr("Alt+O"))
        self.cancelPushButton.setText(self.__tr("&Cancel"))
        self.cancelPushButton.setAccel(self.__tr("Alt+C"))
        self.colorTextLabel.setText(self.__tr("Color:"))
        self.nameTextLabel.setText(self.__tr("Name:"))
        self.nameLineEdit.setText(QString.null)
        self.colorSelectorPushButton.setText(self.__tr("..."))
        self.atomsTextLabel.setText(self.__tr("Atoms:"))
        self.applyPushButton.setText(self.__tr("Apply"))


    def applyButtonPressed(self):
        print "GroundPropDialog.applyButtonPressed(): Not implemented yet"

    def changeGroundColor(self):
        print "GroundPropDialog.changeGroundColor(): Not implemented yet"

    def propertiesChanged(self):
        print "GroundPropDialog.propertiesChanged(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("GroundPropDialog",s,c)
