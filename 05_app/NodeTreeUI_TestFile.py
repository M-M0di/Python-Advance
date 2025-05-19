# ****************************************************************************************
# Content : Early UI test for node tree view during node import
# -----
# Date:
# Created  : 19/05/2025
# Modified : 19/05/2025
# -----
# Dependencies = json, os, hou
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import copy
import json

from PySide2 import QtWidgets, QtCore

import hou
import NodesToJson

class NodeTreeViewer(QtWidgets.QDialog):

    def __init__(self):
        super(NodeTreeViewer, self).__init__(hou.qt.mainWindow())
        self.setWindowTitle("Node Tree Viewer")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.tree_widget)
        self.setLayout(self.layout)

        self.tool = NodesToJson.NodesToJson()
        self.load_and_display_json()

    def load_and_display_json(self):

            with open(self.tool.defaultPath, "r") as f:
                data = json.load(f)

            copied_data = copy.deepcopy(data)
            nodes_data = copied_data.get("nodes", {})

            self.build_tree(nodes_data)

    def build_tree(self, nodes_data):

        stack = []

        for root_name, root_data in reversed(list(nodes_data.items())):
            root_item = QtWidgets.QTreeWidgetItem([f"{root_name} ({root_data.get('type')})"])
            root_item.setData(0, QtCore.Qt.UserRole, root_name)
            self.tree_widget.addTopLevelItem(root_item)
            stack.append((root_name, root_data, root_item))

        while stack:
            node_name, node_data, parent_item = stack.pop()

            children = node_data.get("child", {})
            for child_name in reversed(list(children.keys())):
                child_data = children[child_name]
                child_item = QtWidgets.QTreeWidgetItem([f"{child_name} ({child_data.get('type')})"])
                child_item.setData(0, QtCore.Qt.UserRole, child_name)
                parent_item.addChild(child_item)

                stack.append((child_name, child_data, child_item))

        self.tree_widget.expandAll()

    def on_item_clicked(self, item, column):
        node_name = item.data(0, QtCore.Qt.UserRole)
        QtWidgets.QMessageBox.information(self, "Node Selected", f"You selected: {node_name}")

def show_node_tree_viewer():
    viewer = NodeTreeViewer()
    viewer.exec()
    
show_node_tree_viewer()