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
# TO DO   : btn_LoadSelected and btn_Save methods need to be implemented.
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import ast
import copy
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
        self.modifiedNodesDict = {}
        
        self.loadWidgets()
        self.setWidgetsProperties()
        self.setConnections()
     
    def loadWidgets(self):
        self.lineEdit   = self.wgLoader.findChild(QtWidgets.QLineEdit, "filePath")
        self.parmView   = self.wgLoader.findChild(QtWidgets.QTableView, "parmView")
        self.treeWidget = self.wgLoader.findChild(QtWidgets.QTreeWidget, "nodeTree")
        self.selectAllCheckbox = QtWidgets.QCheckBox(self.treeWidget)
        
        self.btnSave    = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Save")
        self.btnEdit    = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Edit")
        self.btnCancel  = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Cancel")
        self.btnBrowse  = self.wgLoader.findChild(QtWidgets.QToolButton, "btn_FilePath")
        self.btnLoadSelected = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_LoadSelected")
        
    def setWidgetsProperties(self):
        self.parmModel = QtGui.QStandardItemModel()
        self.parmModel.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.parmView.setModel(self.parmModel) 
        self.parmView.horizontalHeader().setStretchLastSection(True)
        self.parmView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setHeaderLabels(["       Select All"])
        self.treeWidget.header().setStretchLastSection(False)
        self.treeWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.treeWidget.header().resizeSection(0, 254)

        self.selectAllCheckbox.setText("")
        self.selectAllCheckbox.setTristate(False)
        self.selectAllCheckbox.setChecked(False)
        self.repositionHeaderCheckbox()
        self.treeWidget.header().sectionResized.connect(self.repositionHeaderCheckbox)
        self.treeWidget.header().geometriesChanged.connect(self.repositionHeaderCheckbox)
               
        self.btnEdit.setVisible(True)
        self.btnSave.setVisible(False)
        self.btnCancel.setVisible(False)
        self.wgLoader.setWindowTitle("Houdini Node Template Loader")
    
    def setConnections(self):
        self.btnSave.clicked.connect(self.btn_Save)
        self.btnCancel.clicked.connect(self.btn_Cancel)
        self.btnBrowse.clicked.connect(self.browseJsonFile)
        self.btnEdit.clicked.connect(self.set_btnEditEnabled)
        self.lineEdit.returnPressed.connect(self.loadFromlineEdit)
        self.treeWidget.itemChanged.connect(self.onTreeItemChanged)
        self.btnLoadSelected.clicked.connect(self.btn_LoadSelected)
        self.selectAllCheckbox.stateChanged.connect(self.onSelectAllToggled)
        self.treeWidget.itemSelectionChanged.connect(self.onTreeItemSelected)
        
    def repositionHeaderCheckbox(self):
        header = self.treeWidget.header()
        x = header.sectionPosition(0) + 4
        y = 2
        width = 16
        height = header.height() - 4
        self.selectAllCheckbox.setGeometry(x, y, width, height)
        self.selectAllCheckbox.raise_()

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
            currentNodes, currentParent = queue.popleft()

            for node in currentNodes:
                label = f"{node['name']} ({node['type']})"
                item = QtWidgets.QTreeWidgetItem([label])
                item.setCheckState(0, QtCore.Qt.Unchecked)
                item.setData(0, QtCore.Qt.UserRole, node['name'])

                if currentParent is None:
                    self.treeWidget.addTopLevelItem(item)
                else:
                    currentParent.addChild(item)

                if node.get("children"):
                    queue.append((node["children"], item))

    def onSelectAllToggled(self, state):
        self.treeWidget.blockSignals(True)
        checkState = QtCore.Qt.Checked if state == QtCore.Qt.Checked else QtCore.Qt.Unchecked
        topLevelCount = self.treeWidget.topLevelItemCount()

        for topIndex in range(topLevelCount):
            topItem = self.treeWidget.topLevelItem(topIndex)
            topItem.setCheckState(0, checkState)

            childCount = topItem.childCount()
            for childIndex in range(childCount):
                childItem = topItem.child(childIndex)
                childItem.setCheckState(0, checkState)

                grandChildCount = childItem.childCount()
                for grandChildIndex in range(grandChildCount):
                    grandChildItem = childItem.child(grandChildIndex)
                    grandChildItem.setCheckState(0, checkState)

        self.treeWidget.blockSignals(False)

    def onTreeItemChanged(self, item):
        self.treeWidget.blockSignals(True)
        state = item.checkState(0)
        
        for child_id in range(item.childCount()):
            child = item.child(child_id)
            child.setCheckState(0, state)
            
        self.treeWidget.blockSignals(False)

    def onTreeItemSelected(self, editable=False):
        selectedItems = self.treeWidget.selectedItems()
        if not selectedItems:
            self.parmModel.setRowCount(0)
            return

        item = selectedItems[0]
        nodeName = item.data(0, QtCore.Qt.UserRole)

        nodeData = self.modifiedNodesDict.get(nodeName) or self.nodesDict.get(nodeName)

        if nodeData:
            parmData = nodeData.get("parm", {})
            labelData = nodeData.get("parm_label", {})
        else:
            parmData = {}
            labelData = {}
            for sourceDict in (self.modifiedNodesDict, self.nodesDict):
                for parentData in sourceDict.values():
                    childData = parentData.get("child", {}).get(nodeName)
                    if childData:
                        parmData = childData.get("parms", {})
                        break
                if parmData:
                    break

        self.parmModel.setRowCount(0)

        for key, value in parmData.items():
            label = labelData.get(key, key)  # fallback to key if no label
            value_str = str(value)
            labelItem = QtGui.QStandardItem(label)
            valueItem = QtGui.QStandardItem(value_str)

            labelItem.setFlags(labelItem.flags() & ~QtCore.Qt.ItemIsEditable)

            if not editable:
                valueItem.setFlags(valueItem.flags() & ~QtCore.Qt.ItemIsEditable)
            else:
                valueItem.setFlags(valueItem.flags() | QtCore.Qt.ItemIsEditable)

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
            
    def btn_Edit(self, enabled):
        self.btnEdit.setVisible(not enabled)
        self.btnSave.setVisible(enabled)
        self.btnCancel.setVisible(enabled)

        self.onTreeItemSelected(editable=enabled)

    def btn_LoadSelected(self):
        """TO DO: Load selected nodes and their parameters into the application"""
        pass

    def set_btnEditEnabled(self):
        self.btn_Edit(True)
        
    def btn_Save(self):
        selectedItems = self.treeWidget.selectedItems()
        if not selectedItems:
            return

        item = selectedItems[0]
        nodeName = item.data(0, QtCore.Qt.UserRole)
        if nodeName not in self.modifiedNodesDict:
            original = self.nodesDict.get(nodeName)
            if not original:
                return
            self.modifiedNodesDict[nodeName] = copy.deepcopy(original)
        
        nodeData = self.modifiedNodesDict[nodeName]
        parmData = nodeData.get("parm", {})

        for row in range(self.parmModel.rowCount()):
            key = self.parmModel.item(row, 0).text()
            value_str = self.parmModel.item(row, 1).text()
            original = parmData.get(key)
            
            # Convert value_str back to original type
            if isinstance(original, list):
                value = ast.literal_eval(value_str)
            elif isinstance(original, bool):
                value = value_str.lower() in ("1", "true", "yes")
            elif isinstance(original, int):
                value = int(value_str)
            elif isinstance(original, float):
                value = float(value_str)
            else:
                value = value_str

        nodeData["parm"] = parmData
        self.modifiedNodesDict[nodeName] = nodeData

        self.btn_Edit(False)
        self.onTreeItemSelected(editable=False)
        
    def btn_Cancel(self):
        self.btn_Edit(False)
        self.onTreeItemSelected(editable=False)
    
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