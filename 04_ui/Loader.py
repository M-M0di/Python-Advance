# ****************************************************************************************
# Content : Loader class for loading nodes from a JSON file and displaying them in a UI.
# -----
# Date:
# Created  : 22/05/2025
# Modified : 01/06/2025
# -----
# Dependencies = os, json, collections.deque, QtWidgets, QtCompat, QtCore, QtGui, 
#                nodeTreeLogic
# -----
# TO DO   : btn_LoadSelected and btn_Edit methods need to be implemented.
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import json
from collections import deque

from Qt import QtWidgets, QtCompat, QtCore, QtGui

import nodeTreeLogic

TITLE = os.path.splitext(os.path.basename(__file__))[0]
class Loader:
    """Loader class handles loading and displaying nodes from a JSON file in a UI"""
    def __init__(self):
        ui_path = "/".join([os.path.dirname(__file__), "ui", TITLE + ".ui"])
        self.wgLoader   = QtCompat.loadUi(ui_path)
        self.nodes_dict = {}
        
        self.treeWidget = self.wgLoader.findChild(QtWidgets.QTreeWidget, "nodeTree")
        self.selectAll  = self.wgLoader.findChild(QtWidgets.QCheckBox, "selectAll")
        self.lineEdit   = self.wgLoader.findChild(QtWidgets.QLineEdit, "filePath")
        self.btnBrowse  = self.wgLoader.findChild(QtWidgets.QToolButton, "btn_FilePath")
        self.btnEdit    = self.wgLoader.findChild(QtWidgets.QToolButton, "btn_Edit")
        self.parmView   = self.wgLoader.findChild(QtWidgets.QTableView, "parmView")
        self.btnLoadSelected = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_LoadSelected")
        
        self.parmModel = QtGui.QStandardItemModel()
        self.parmModel.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.parmView.setModel(self.parmModel) 
        self.parmView.horizontalHeader().setStretchLastSection(True)
        self.parmView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.wgLoader.setWindowTitle("Houdini Node Template Loader")
        self.treeWidget.setHeaderHidden(True)

        self.treeWidget.itemChanged.connect(self.onTreeItemChanged)
        self.selectAll.stateChanged.connect(self.onSelectAllToggled)
        self.treeWidget.itemSelectionChanged.connect(self.onTreeItemSelected)
        self.btnBrowse.clicked.connect(self.browseJsonFile)
        self.btnLoadSelected.clicked.connect(self.btn_LoadSelected)
        self.lineEdit.returnPressed.connect(self.loadFromlineEdit)

    def loadJsonFile(self, filePath):
        with open(filePath, "r") as f:
            data = json.load(f)

        nodesData = data.get("nodes", {})
        self.nodesDict = nodesData
        self.treeWidget.clear()
        hierarchy = nodeTreeLogic.buildNodeHierarchy(nodesData)
        self.add_ItemsToTree(hierarchy)
        
        return nodesData

    def add_ItemsToTree(self, nodes):
        queue = deque()
        queue.append((nodes, None))

        while queue:
            current_nodes, current_parent = queue.popleft()

            for node in current_nodes:
                label = f"{node['name']} ({node['type']})"
                item = QtWidgets.QTreeWidgetItem([label])
                item.setCheckState(0, QtCore.Qt.Unchecked)
                item.setData(0, QtCore.Qt.UserRole, node['name'])

                if current_parent is None:
                    self.treeWidget.addTopLevelItem(item)
                else:
                    current_parent.addChild(item)

                if node.get("children"):
                    queue.append((node["children"], item))

    def onSelectAllToggled(self, state):
        self.treeWidget.blockSignals(True) 
        checkState = QtCore.Qt.Checked if state == QtCore.Qt.Checked else QtCore.Qt.Unchecked
        topLevelCount = self.treeWidget.topLevelItemCount()

        for topLevelIndex in range(topLevelCount):
            topLevelItem = self.treeWidget.topLevelItem(topLevelIndex)
            topLevelItem.setCheckState(0, checkState)

            descendantsToProcess = []
            for child_index in range(topLevelItem.childCount()):
                descendantsToProcess.append(topLevelItem.child(child_index))

            currentIndex = 0
            while currentIndex < len(descendantsToProcess):
                currentItem = descendantsToProcess[currentIndex]
                currentItem.setCheckState(0, checkState)
                for grandchildIndex in range(currentItem.childCount()):
                    descendantsToProcess.append(currentItem.child(grandchildIndex))
                currentIndex += 1

        self.treeWidget.blockSignals(False)

    def onTreeItemChanged(self, item):
        self.treeWidget.blockSignals(True)
        state = item.checkState(0)
        
        for child_id in range(item.childCount()):
            child = item.child(child_id)
            child.setCheckState(0, state)
            
        self.treeWidget.blockSignals(False)

    def onTreeItemSelected(self):
        selected_items = self.treeWidget.selectedItems()
        if not selected_items:
            self.parmModel.setRowCount(0)
            return

        item = selected_items[0]
        nodeName = item.data(0, QtCore.Qt.UserRole)

        if nodeName in self.nodesDict:
            nodeData = self.nodesDict[nodeName]
            parmData = nodeData.get("parm", {})
            labelData = nodeData.get("parm_label", {})
        else:
            for parentName, parentData in self.nodesDict.items():
                childData = parentData.get("child", {}).get(nodeName)
                if childData:
                    parmData = childData.get("parms", {})
                    labelData = {}
                    break
            else:
                parmData = {}
                labelData = {}
        
        self.parmModel.setRowCount(0)

        for key, value in parmData.items():
            label = labelData.get(key, key)  # fallback to key if no label
            value_str = str(value)
            labelItem = QtGui.QStandardItem(label)
            valueItem = QtGui.QStandardItem(value_str)
            labelItem.setFlags(labelItem.flags() & ~QtCore.Qt.ItemIsEditable)
            valueItem.setFlags(valueItem.flags() & ~QtCore.Qt.ItemIsEditable)
            self.parmModel.appendRow([labelItem, valueItem])

    def browseJsonFile(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self.wgLoader, "Select JSON File", "", "JSON Files (*.json);;All Files (*)")
        if filePath:
            self.lineEdit.setText(filePath)
            self.loadJsonFile(filePath)
            
    def loadFromlineEdit(self):
        filePath = self.lineEdit.text()
        if filePath and os.path.exists(filePath):
            self.loadJsonFile(filePath)

    def btn_LoadSelected(self):
        """TO DO: Load selected nodes and their parameters into the application"""
        pass

    def btn_Edit(self):
        """TO DO: Allow editing of the selected node's parameters"""	
        pass
    
    def show(self):
        self.wgLoader.show()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    
    app.setStyle(QtWidgets.QStyleFactory.create("fusion"))
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))
    dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(208, 208, 208))
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(208, 208, 208))
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(208, 208, 208))
    dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(208, 208, 208))
    dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 48))
    dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(208, 208, 208))
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.black)
    app.setPalette(dark_palette)
    
    loader = Loader()
    loader.show()
    app.exec_()