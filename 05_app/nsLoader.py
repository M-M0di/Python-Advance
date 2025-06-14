# ****************************************************************************************
# Content : Loader class for loading nodes from a JSON file and displaying them in a UI.
# -----
# Date:
# Created  : 22/05/2025
# Modified : 13/06/2025
# -----
# Dependencies = os, ast, hou, copy, json, collections.deque, QtWidgets, QtCompat, QtCore,
#               QtGui, functools.wraps, nodeTreeLogic, nodeSnapLogic
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import ast
import copy
import json
from functools import wraps
from collections import deque

from Qt import QtWidgets, QtCompat, QtCore, QtGui

import hou
import nodeTreeLogic
from nodeSnapLogic import NodeSnapLogic

TITLE = os.path.splitext(os.path.basename(__file__))[0]
PARENT = hou.ui.mainQtWindow()

class NsLoader(QtCore.QObject):
    def __init__(self, parent=None):
        super(NsLoader, self).__init__(parent)
        self.ui_path = os.path.join(os.path.dirname(__file__), "ui", TITLE + ".ui")
        self.wgLoader = QtCompat.loadUi(self.ui_path)
        self.logic = NodeSnapLogic()
        self.nodesDict = {}
        self._editInProgress = False
        self._previousTreeSelection = None

        self.applyCustomStyle()
        self.loadWidgets()
        self.setWidgetsProperties()
        self.setConnections()
        
        self.tabsmetaData.parentWidget().hide()
        self.wgLoader.installEventFilter(self)
        self.treeWidget.viewport().installEventFilter(self)
        self.parmView.viewport().installEventFilter(self)
        
        self.wgLoader.setWindowTitle("Node Snapshot Loader")

    def loadWidgets(self):
        self.lineEdit = self.wgLoader.findChild(QtWidgets.QLineEdit, "filePath")
        self.splitter = self.wgLoader.findChild(QtWidgets.QSplitter, "splitter")
        self.parmView = self.wgLoader.findChild(QtWidgets.QTableView, "parmView")
        self.treeWidget = self.wgLoader.findChild(QtWidgets.QTreeWidget, "nodeTree")
        self.metaDataContainer = self.wgLoader.findChild(QtWidgets.QWidget, "metaDataContainer")
        
        self.btnSave = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Save")
        self.btnEdit = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Edit")
        self.btnHelp = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Help")
        self.btnReset  = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Reset")
        self.btnCancel = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_Cancel")
        self.btnBrowse = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_FilePath")
        self.tabsmetaData = self.wgLoader.findChild(QtWidgets.QTabWidget, "tabs_metaData")
        self.btnInfoTabShow  = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_infoTabShow")
        self.btnLoadSelected = self.wgLoader.findChild(QtWidgets.QPushButton, "btn_LoadSelected")
        
        self.rightPaneWidget = self.splitter.widget(1)
   
    def setWidgetsProperties(self):
        self.metaDataLayout = self.metaDataContainer.layout()
        if self.metaDataLayout is None:
            self.metaDataLayout = QtWidgets.QFormLayout()
            self.metaDataContainer.setLayout(self.metaDataLayout)
        
        self.selectAllCheckbox = QtWidgets.QCheckBox(self.treeWidget)
        
        self.parmModel = QtGui.QStandardItemModel()
        self.parmModel.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.parmView.setModel(self.parmModel)

        self.parmView.setShowGrid(False)
        self.parmView.setAlternatingRowColors(True)
        self.parmView.verticalHeader().setVisible(False)
        self.parmView.horizontalHeader().setStretchLastSection(True)
        self.parmView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.parmView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.parmView.setUpdatesEnabled(False)
        self.parmView.resizeRowsToContents()
        self.parmView.resizeColumnsToContents()
        self.parmView.setUpdatesEnabled(True)
                         
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setHeaderLabels(["       Select All"])
        self.treeWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
  
        self.selectAllCheckbox.setText("")
        self.selectAllCheckbox.setTristate(False)
        self.selectAllCheckbox.setChecked(False)
        self.selectAllCheckbox.setFont(QtGui.QFont("Segoe UI", 9))
        self.selectAllCheckbox.setFixedSize(16, 16)
        self.selectAllCheckbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)

        self.repositionHeaderCheckbox()
        self.treeWidget.header().sectionResized.connect(self.repositionHeaderCheckbox)
        self.treeWidget.header().geometriesChanged.connect(self.repositionHeaderCheckbox)

        self.btnEdit.setEnabled(False)
        self.btnSave.setVisible(False)
        self.btnReset.setVisible(False)
        self.btnCancel.setVisible(False)
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
            
    def setConnections(self):
        self.btnSave.clicked.connect(self.btn_Save)
        self.btnReset.clicked.connect(self.btn_Reset)
        self.btnCancel.clicked.connect(self.btn_Cancel)
        self.btnBrowse.clicked.connect(self.browseJsonFile)
        self.btnEdit.clicked.connect(self.set_btnEditEnabled)
        self.lineEdit.returnPressed.connect(self.loadFromlineEdit)
        self.treeWidget.itemChanged.connect(self.onTreeItemChanged)
        self.btnLoadSelected.clicked.connect(self.btn_LoadSelected)
        self.btnInfoTabShow.clicked.connect(self.toggleRightPane)
        self.selectAllCheckbox.stateChanged.connect(self.onSelectAllToggled)
        self.treeWidget.itemSelectionChanged.connect(self._handleTreeItemSelectionChange)
        self.parmView.selectionModel().selectionChanged.connect(self._handleParmSelectionChange)
        
    def repositionHeaderCheckbox(self):
        header = self.treeWidget.header()
        checkbox_width = self.selectAllCheckbox.width()
        checkbox_height = self.selectAllCheckbox.height()

        x = header.sectionPosition(0) + 6
        y = (header.height() - checkbox_height) // 2 

        self.selectAllCheckbox.setGeometry(x, y, checkbox_width, checkbox_height)
        self.selectAllCheckbox.raise_()
        
    def toggleRightPane(self):
        rightWidget = self.tabsmetaData.parentWidget()
        if rightWidget.isVisible():
            rightWidget.hide()
        else:
            rightWidget.show()

        self.splitter.updateGeometry()
        self.wgLoader.adjustSize()
        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.treeWidget.clearSelection()
                self.treeWidget.setCurrentIndex(QtCore.QModelIndex())
                self.treeWidget.clearFocus()
                self.parmView.clearSelection()
                self.parmView.setCurrentIndex(QtCore.QModelIndex())
                self.parmView.clearFocus()
                return True

        elif event.type() == QtCore.QEvent.MouseButtonPress:
            pos_tree = self.treeWidget.viewport().mapFromGlobal(QtGui.QCursor.pos())
            index_tree = self.treeWidget.indexAt(pos_tree)
            if index_tree.isValid() and self.treeWidget.selectionModel().isSelected(index_tree):
                self.treeWidget.clearSelection()
                self.treeWidget.setCurrentIndex(QtCore.QModelIndex())
                self.treeWidget.clearFocus()
                return True

            pos_table = self.parmView.viewport().mapFromGlobal(QtGui.QCursor.pos())
            index_table = self.parmView.indexAt(pos_table)
            if index_table.isValid() and self.parmView.selectionModel().isSelected(index_table):
                self.parmView.clearSelection()
                self.parmView.setCurrentIndex(QtCore.QModelIndex())
                self.parmView.clearFocus()
                return True

        return False
               
    def loadJsonFile(self, filePath):
        with open(filePath, "r") as f:
            data = json.load(f)

        nodesData = data.get("nodes", {})
        self.nodesDict = nodesData
        self.workingNodesDict = copy.deepcopy(nodesData)
        self.treeWidget.clear()
        hierarchy = nodeTreeLogic.buildNodeHierarchy(nodesData)
        self.add_ItemsToTree(hierarchy)
        
        if self.treeWidget.topLevelItemCount() > 0:
            self.btnEdit.setEnabled(True)
        
        meta = data.get("meta", {})
        self.populateMetaLabels(meta)
        
        return nodesData
    
    def browseJsonFile(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self.wgLoader, "Select JSON File", "", "JSON Files (*.json);;All Files (*)")
        if filePath:
            self.lineEdit.setText(filePath)
            self.loadJsonFile(filePath)
            
    def loadFromlineEdit(self):
        filePath = self.lineEdit.text()
        if filePath and os.path.exists(filePath):
            self.loadJsonFile(filePath)
            
        if self.treeWidget.topLevelItemCount() > 0:
            self.btnEdit.setEnabled(True)
            
    def populateMetaLabels(self, metaDict):
        while self.metaDataLayout.count():
            item = self.metaDataLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for key, value in metaDict.items():
            labelKey = QtWidgets.QLabel(f"{key}:")
            labelKey.setStyleSheet("font-weight: bold; color: #DDDDDD;")
            labelKey.setAlignment(QtCore.Qt.AlignTop)

            labelValue = QtWidgets.QLabel(str(value))
            labelValue.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            labelValue.setWordWrap(True)
            labelValue.setStyleSheet("color: #DDDDDD; padding-left: 6px;")
            self.metaDataLayout.addRow(labelKey, labelValue)
            self.metaDataLayout.addRow(QtWidgets.QLabel(""))

    def add_ItemsToTree(self, nodes):
        queue = deque()
        queue.append((nodes, None, 0))

        while queue:
            currentNodes, currentParent, depth = queue.popleft()

            for node in currentNodes:
                label = f"{node['name']} ({node['type']})"
                item = QtWidgets.QTreeWidgetItem([label])
                item.setCheckState(0, QtCore.Qt.Unchecked)
                item.setData(0, QtCore.Qt.UserRole, node['name'])

                if currentParent is None:
                    self.treeWidget.addTopLevelItem(item)
                else:
                    currentParent.addChild(item)

                if depth < 2:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                    item.setData(0, QtCore.Qt.CheckStateRole, None) 
                        
                if node.get("children"):
                    queue.append((node["children"], item, depth + 1))

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

        self.treeWidget.blockSignals(False)

    def onTreeItemChanged(self, changedItem):
        self.treeWidget.blockSignals(True)
        newState = changedItem.checkState(0)

        for childIndex in range(changedItem.childCount()):
            childItem = changedItem.child(childIndex)
            childItem.setCheckState(0, newState)

        self.treeWidget.blockSignals(False)
        
    def resolvedNodeData(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            selectedItems = self.treeWidget.selectedItems()
            nodeName = selectedItems[0].data(0, QtCore.Qt.UserRole) if selectedItems else None

            parmData = {}
            labelData = {}

            if nodeName:
                nodeData = self.workingNodesDict.get(nodeName)
                if nodeData:
                    parmData = nodeData.get("parm", {}) or nodeData.get("parms", {})
                    labelData = nodeData.get("parm_label", {}) or nodeData.get("label", {})
                else:
                    for parentData in self.workingNodesDict.values():
                        childData = parentData.get("child", {}).get(nodeName)
                        if childData:
                            parmData = childData.get("parm", {}) or childData.get("parms", {})
                            labelData = childData.get("parm_label", {}) or childData.get("label", {})
                            break
            return func(self, parmData, labelData, *args, **kwargs)
        return wrapper
 
    @resolvedNodeData           
    def onTreeItemSelected(self, parmData, labelData, editable=False):
        selectedItems = self.treeWidget.selectedItems()
        self._previousTreeSelection = selectedItems[0] if selectedItems else None

        if not selectedItems:
            self.parmModel.setRowCount(0)
            self.btnEdit.setEnabled(False)
            self.btnSave.setVisible(False)
            self.btnCancel.setVisible(False)
            self.btnReset.setVisible(False)
            return

        self.parmModel.setRowCount(0)

        for key, value in parmData.items():
            label = labelData.get(key)
            isVector = isinstance(value, list) and all(isinstance(v, (int, float)) for v in value)

            if isVector and not label:
                numeric_suffixes = [str(index) for index in range(1, len(value) + 1)]
                component_suffixes = list("xyzwrgba")
                suffixes = numeric_suffixes + component_suffixes

                for suffix in suffixes:
                    candidate_key = f"{key}{suffix}"
                    if candidate_key in labelData:
                        label = labelData[candidate_key]
                        break
                else:
                    label = key

            if not isVector:
                label = label or key

            valueStr = str(value)

            labelItem = QtGui.QStandardItem(label)
            valueItem = QtGui.QStandardItem(valueStr)

            labelItem.setFlags(labelItem.flags() & ~QtCore.Qt.ItemIsEditable)
            labelItem.setData(key, QtCore.Qt.UserRole)
            valueItem.setFlags(valueItem.flags() & ~QtCore.Qt.ItemIsEditable)

            self.parmModel.appendRow([labelItem, valueItem])

        self.btnEdit.setEnabled(False)
        self.parmView.clearSelection()      
        
    def _handleParmSelectionChange(self, selected, deselected):
        hasValueSelection = any(index.column() == 1 for index in selected.indexes())
        self.btnEdit.setEnabled(hasValueSelection)

    def _handleTreeItemSelectionChange(self):
        if not self.treeWidget.hasFocus():
            return

        if self._editInProgress:
            reply = QtWidgets.QMessageBox.question(
                self.wgLoader,
                "Edit in Progress",
                "You are attempting to select another item. Do you wish to cancel current edit?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.No:
                self.treeWidget.itemSelectionChanged.disconnect()
                self.treeWidget.setCurrentItem(self._previousTreeSelection)
                self.treeWidget.itemSelectionChanged.connect(self._handleTreeItemSelectionChange)
                return
            else:
                self.btn_Cancel()

        self._previousTreeSelection = self.treeWidget.currentItem()
        self.onTreeItemSelected(editable=False)

    def findNodeByName(self, name, sourceDict):
        stack = list(sourceDict.items())

        while stack:
            current_name, current_data = stack.pop()
            if current_name == name:
                return current_data

            for child_name, child_data in current_data.get("child", {}).items():
                if child_name == name:
                    return child_data
        return None
        
    def btn_LoadSelected(self):
        checkedNodeData = {}
        treeItemsToProcess = [
            self.treeWidget.topLevelItem(index)
            for index in range(self.treeWidget.topLevelItemCount())
        ]

        while treeItemsToProcess:
            currentItem = treeItemsToProcess.pop()
            nodeName = currentItem.data(0, QtCore.Qt.UserRole)

            if currentItem.checkState(0) == QtCore.Qt.Checked:
                nodeInfo = self.findNodeByName(nodeName, self.workingNodesDict)
                if nodeInfo:
                    checkedNodeData[nodeName] = nodeInfo

            for childIndex in range(currentItem.childCount()):
                treeItemsToProcess.append(currentItem.child(childIndex))

        # Flatten selected nodes and all nested children
        allNodeData = {}
        nodesToProcess = list(checkedNodeData.items())

        while nodesToProcess:
            currentName, currentInfo = nodesToProcess.pop()
            allNodeData[currentName] = currentInfo

            for childName, childInfo in currentInfo.get("child", {}).items():
                nodesToProcess.append((childName, childInfo))

        nodeDataDict = {"nodes": allNodeData}

        self.logic.importNodesFromJson(allNodeData, nodeDataDict)
        self.logic.setNodeDataFromJson(allNodeData, nodeDataDict)

        self.cleanup()
        
    def btn_Edit(self, enabled):
        self.btnEdit.setVisible(not enabled)
        self.btnSave.setVisible(enabled)
        self.btnCancel.setVisible(enabled)
        self.btnReset.setVisible(enabled)

        self.btnSave.setEnabled(enabled)
        self.btnReset.setEnabled(enabled)
        self.btnCancel.setEnabled(enabled)

        for row in range(self.parmModel.rowCount()):
            valueItem = self.parmModel.item(row, 1)
            valueItem.setFlags(valueItem.flags() | QtCore.Qt.ItemIsEditable if enabled else valueItem.flags() & ~QtCore.Qt.ItemIsEditable)

        self._editInProgress = enabled
        
    def set_btnEditEnabled(self):
        self.btn_Edit(True)
        
    def findAndUpdateNode(self, container, targetName):
        stack = [container]

        while stack:
            current = stack.pop()

            if targetName in current:
                return current[targetName]

            for nodeData in current.values():
                childDict = nodeData.get("child", {})
                if targetName in childDict:
                    return childDict[targetName]

                stack.append(childDict)
                
        return None
        
    def btn_Save(self):
        selectedItems = self.treeWidget.selectedItems()
        if not selectedItems:
            return

        item = selectedItems[0]
        nodeName = item.data(0, QtCore.Qt.UserRole)
        nodeDataRef = self.findAndUpdateNode(self.workingNodesDict, nodeName)
        if nodeDataRef is None:
            return
        parmData = nodeDataRef.get("parm", {})

        for row in range(self.parmModel.rowCount()):
            key = self.parmModel.item(row, 0).data(QtCore.Qt.UserRole)
            valueStr = self.parmModel.item(row, 1).text()
            original = parmData.get(key)

            if isinstance(original, list):
                parsed = ast.literal_eval(valueStr)
                itemType = type(original[0]) if original else str
                if not isinstance(parsed, list):
                    parsed = [itemType(parsed)] * len(original)
                value = [itemType(v) for v in parsed]
            else:
                value = {
                    bool: lambda v: v.strip().lower() in ("1", "true", "yes"),
                    int: int,
                    float: float
                }.get(type(original), str)(valueStr)

            parmData[key] = value
        nodeDataRef["parm"] = parmData

        self._editInProgress = False
        self.btn_Edit(False)
        self.treeWidget.clearSelection()
        self.treeWidget.setCurrentItem(item)
        self.onTreeItemSelected(editable=False)
        
    def btn_Reset(self):
        selectedItems = self.treeWidget.selectedItems()
        item = selectedItems[0]
        nodeName = item.data(0, QtCore.Qt.UserRole)
        originalNode = self.nodesDict.get(nodeName)

        # Reset 
        self.workingNodesDict[nodeName] = copy.deepcopy(originalNode)

        self.treeWidget.clearSelection()
        self.treeWidget.setCurrentItem(item)
        self.onTreeItemSelected(editable=True)

        self._editInProgress = True
        self.btn_Edit(True)
        
    def btn_Cancel(self):
        self._editInProgress = False
        self.btn_Edit(False)
        self.onTreeItemSelected(editable=False)
               
    def applyCustomStyle(self):
        self.wgLoader.setStyle(QtWidgets.QStyleFactory.create("Fusion"))

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
        self.wgLoader.setPalette(dark_palette)

        self.wgLoader.setStyleSheet("""
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

        QCheckBox {
            background: transparent;
            border: 1px solid #888;
        }
        QCheckBox:focus {
            outline: none;
        }
               
        QTreeView::indicator:unchecked {
            background-color: #333;
            border: 1px solid #666;
        }
                    
        QHeaderView::section {
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a3a3a, stop:0.5 #353535, stop:1 #2e2e2e);
            color: #ccc;
            padding: 2px 4px;
            border-top: 1px solid #111;
            border-bottom: 1px solid #111;
            border-left: 1px solid #111;
            border-right: 1px solid #111;
            min-height: 18px;
            max-height: 20px;
        }

        QTableView QHeaderView::section:vertical {
            min-width: 30px;
            max-width: 40px;
            background-color: #2c2c2c;
            border-right: none;
            border-left: none;
            border-top: 0px;
        }
        
        QTreeWidget, QTableView{
            background-color: #1f1f1f;
            alternate-background-color: #2a2a2a;
            selection-background-color: transparent;
            selection-color: white;
            border-left: 1px solid #111;
            border-right: 1px solid #111;
            border-bottom: 1px solid #111;
        }
        
        QTreeWidget::item:hover,
        QTableView::item:hover {
            background-color: rgba(220, 220, 220, 30);
        }

        QTreeWidget::item:selected {
            background-color: rgba(255, 153, 0, 90);
            border: 1px solid rgb(255, 204, 82);
            color: white;
        }

        QTableView::item:selected:active {
            background-color: rgba(255, 153, 0, 90);
            border: 1px solid rgb(255, 204, 82);
            color: white;
        }
        
        QTableView::item {
            border: none;
            padding: 0px;
            margin: 0px;
        }
        
        QTableView::item {
            border-left: 1px solid #111;	
            padding: 0px;
            margin: 0px;
        }
           
        QScrollBar:vertical {
            background: #2a2a2a;
            width: 12px;
            margin: 0px 0 30px 0;
        }

        QScrollBar::handle:vertical {
            background: #5a5a5a;
            min-height: 20px;
            border: 1px solid #333;
        }

        QScrollBar::handle:vertical:hover {
            background: #7a7a7a;
        }

        QScrollBar::sub-line:vertical {
            background: #3d3d3d;
            height: 15px;
            subcontrol-origin: margin;
            subcontrol-position: bottom;
            border: 1px solid #222;
            margin-bottom: 15px;
        }
        
        QScrollBar::add-line:vertical {
            background: #3d3d3d;
            height: 15px;
            subcontrol-origin: margin;
            subcontrol-position: bottom;
            border: 1px solid #222;
        }

        QScrollBar::sub-line:vertical:hover,
        QScrollBar::add-line:vertical:hover {
            background: #5a5a5a;
        }

        QPushButton:disabled {
            color: #666;
        }
        
        QTabWidget::pane {
            border: 1px solid #111;    
            background-color: #1f1f1f;
            top: -1px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3a3a3a, stop:0.5 #353535, stop:1 #2e2e2e);
            border: 1px solid #111;
            border-bottom: 0px;
            padding: 4px 10px;
            margin-right: 0px;
            color: #ccc;
            font-family: "Segoe UI";
            font-size: 12px;
        }

        QTabBar::tab:selected, QTabBar::tab:hover {
            background-color: #2e2e2e;
            color: white;
        }
        
        QAbstractScrollArea {
            padding: 0px;
        }
                
        """)
        
    def cleanup(self):
        self.nodesDict.clear()
        self.workingNodesDict.clear()
        self.wgLoader.close()
    
    def closeEvent(self, event):
        self.nodesDict.clear()
        self.workingNodesDict.clear()
        event.accept()
    
    def show(self):
        self.wgLoader.closeEvent = self.closeEvent
        self.wgLoader.setParent(PARENT, QtCore.Qt.Tool)
        self.wgLoader.show()
        self.wgLoader.raise_()
        self.wgLoader.activateWindow()
        
