
# ****************************************************************************************
# Content : This script provides a UI for saving node snapshots in Houdini.
# -----
# Date:
# Created  : 26/05/2025
# Modified : 15/06/2025
# -----
# Dependencies = os, hou, json, datetime, QtWidgets, QtCompat, QtCore, QtGui, 
#                nodeSnapLogic, webbrowser                 
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import json
import getpass
import webbrowser
from datetime import datetime

from Qt import QtWidgets, QtCompat, QtCore, QtGui

import hou
from nodeSnapLogic import NodeSnapLogic

TITLE  = os.path.splitext(os.path.basename(__file__))[0]
PARENT = hou.ui.mainQtWindow()

class NsSave():
    def __init__(self):
            self.ui_path = os.path.join(os.path.dirname(__file__), "ui", TITLE + ".ui")
            self.wgSave = QtCompat.loadUi(self.ui_path)
            self.logic = NodeSnapLogic()

            self.loadWidgets()
            self.setWidgetsProperties()
            self.setConnections()
            self.applyCustomStyle()
            self.wgSave.setWindowTitle("Save Node Snapshot")
            
    def loadWidgets(self):
        self.btnHelp = self.wgSave.findChild(QtWidgets.QPushButton, "btn_Help")
        self.btnSave = self.wgSave.findChild(QtWidgets.QPushButton, "btn_Save")
        self.btnBrowse = self.wgSave.findChild(QtWidgets.QPushButton, "btn_FilePath")
        
        self.lblAuthorName = self.wgSave.findChild(QtWidgets.QLabel, "lbl_AuthorName")
        self.lblDateAndTime = self.wgSave.findChild(QtWidgets.QLabel, "lbl_DateAndTime")
        
        self.leFilePath = self.wgSave.findChild(QtWidgets.QLineEdit, "le_FilePath")
        self.leComments = self.wgSave.findChild(QtWidgets.QPlainTextEdit, "le_Comments")
    
    def setWidgetsProperties(self):
        self.btnHelp.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0px;
                qproperty-iconSize: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 10);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 30);
                border: 1px inset rgba(255, 255, 255, 40);
                border-radius: 3px;
            }
        """)
        
        self.btnHelp.setToolTip("Open wiki")
        self.btnBrowse.setToolTip("Open file browser")    
    
    def setConnections(self):
        self.btnSave.clicked.connect(self.exportNodes)
        self.btnHelp.clicked.connect(self.openHelpPage)
        self.btnBrowse.clicked.connect(lambda: self.selectFilePath())
        self.leFilePath.returnPressed.connect(self.SaveFromlineEdit)
        self.leComments.textChanged.connect(self.enforceCommentCharLimit)
    
    def applyCustomStyle(self):
        self.wgSave.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(208, 208, 208))
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(255, 255, 255))
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(0, 0, 0))
        dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(208, 208, 208))
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 48))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(208, 208, 208))
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(60, 100, 150))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        self.wgSave.setPalette(dark_palette)
        
        self.wgSave.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: #dcdcdc;
            font-size: 12px;
            font-family: "Segoe UI", sans-serif;
        }

        QLineEdit {
            background-color: #3b3b3b;
            border: 1px solid #222;
            padding: 2px 4px;
        }
        
        QPlainTextEdit {
            background-color: #3b3b3b;
            border: 1px solid #222;
            padding: 2px 4px;
        }
        
        """)
        
    def enforceCommentCharLimit(self):
        text = self.leComments.toPlainText()
        max_chars = 500

        if len(text) > max_chars:
            trimmed_text = text[:max_chars]
            cursor = self.leComments.textCursor()
            pos = cursor.position()

            self.leComments.blockSignals(True)
            self.leComments.setPlainText(trimmed_text)
            self.leComments.blockSignals(False)

            cursor.setPosition(min(pos, len(trimmed_text)))
            self.leComments.setTextCursor(cursor)

            QtWidgets.QToolTip.showText(
                self.leComments.mapToGlobal(QtCore.QPoint(0, 0)),
                "Comment limit: 500 characters max.",
                self.leComments
            )
            
    def SaveFromlineEdit(self):
        filePath = self.leFilePath.text()
        if filePath and os.path.exists(filePath):   
            self.path = filePath
            
    def selectFilePath(self):
        hip_dir = os.path.dirname(hou.hipFile.path()) or os.getcwd()

        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.wgSave,
            "Save JSON File",
            hip_dir,
            "JSON Files (*.json);;All Files (*)"
        )

        if filePath:
            if not filePath.lower().endswith(".json"):
                filePath += ".json"

            self.leFilePath.setText(filePath)
            self.path = filePath
    
    def exportNodes(self):
        if self.path:
            self.CreateJsonFile()
            nodesData = self.logic.exportSelectedNodesToJson()

            nodesData["meta"] = {
                "File Name"       : hou.hipFile.basename(),
                "File Path"       : self.path,
                "Comments"        : self.getComments(),
                "Author"          : self.getAuthorName(),
                "Creation"        : self.getDateAndTime(),
                "Houdini Version" : hou.applicationVersionString(),
            }

            with open(self.path, "w") as f:
                json.dump(nodesData, f, indent=4)

            self.lblAuthorName.setText(nodesData["meta"]["Author"])
            self.lblDateAndTime.setText(nodesData["meta"]["Creation"])

            self.wgSave.close()
        
    def CreateJsonFile(self):
        with open(self.path, "w") as f:
            json.dump({}, f, indent=4)
            
    def getComments(self):
        return self.leComments.toPlainText().strip() or " "
        
    def getAuthorName(self):
        return getpass.getuser() 
    
    def getDateAndTime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def openHelpPage(self):
        webbrowser.open("https://github.com/M-M0di/Python-Advance")

    def show(self):
        self.lblAuthorName.setText(self.getAuthorName())
        self.lblDateAndTime.setText(self.getDateAndTime())
        self.wgSave.setParent(PARENT, QtCore.Qt.Tool)
        self.wgSave.show()
        self.wgSave.raise_()
        self.wgSave.activateWindow()