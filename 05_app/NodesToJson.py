# ****************************************************************************************
# Content : Contains classes and functions for exporting/importing nodes and their data
# -----
# Date:
# Created  : 29/04/2025
# Modified : 19/05/2025
# -----
# Dependencies = json, os, hou, wraps from functools
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import os
import json
from functools import wraps

import hou 
class NodesToJson:
    """
    Class contains functions that allows user to export/import selected nodes to/from a Json file.
    """    
    def __init__(self):
        self.hip = hou.expandString("$HIP")
        self.defaultPath = os.path.join(self.hip, "data", "nodeExportData.json").replace("\\", "/")

    def _checkJsonPathExists(self):
      
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.default_path), exist_ok=True)

        # Ensure the file exists
        if not os.path.exists(self.default_path):
            with open(self.defaultPath, "w") as f:
                json.dump({}, f)

    def openJsonFile(func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self._checkJsonPathExists()
            with open(self.defaultPath, "r") as f:
                data = json.load(f)
            return func(self, data, *args, **kwargs)
        return wrapper

    def exportSelectedNodesToJson(self):

        selected_nodes = hou.selectedNodes()
        output_nodes = {"nodes": {}}

        for node in selected_nodes:
            path = node.parent().path().rstrip("/")
            root_path = "/".join(path.split("/")[:2]) + "/"

            # Build node data dictionary
            node_dict = {

                "path"  : node.parent().path().rstrip("/") + "/",
                "type"  : node.type().name(),
                "parent": {
                          "name" : node.parent().name(),
                          "type" : node.parent().type().name()
                          },
                "root"  : root_path,
                "parm"  : node.parmsAsData(),
                "input" : node.inputsAsData(),
                "flag"  : {
                          "display"  : node.isDisplayFlagSet() if hasattr(node, 'isDisplayFlagSet') else False,
                          "render"   : node.isRenderFlagSet() if hasattr(node, 'isRenderFlagSet') else False,
                          "template" : node.isTemplateFlagSet() if hasattr(node, 'isTemplateFlagSet') else False,
                          "bypass"   : node.isBypassed() if hasattr(node, 'isBypassed') else False
                          },
                "child" : {} 

            }

            # Check if the node has children and may need to be unlocked
            if node.type().name().endswith(("solver", "net", "vop")):
                node.allowEditingOfContents() 
                children = node.childrenAsData() if hasattr(node, 'childrenAsData') else {}
                node_dict["child"] = children
                node.matchCurrentDefinition()               
            else:
                children = node.childrenAsData() if hasattr(node, 'childrenAsData') else {}
                node_dict["child"] = children
            output_nodes["nodes"][node.name()] = node_dict

        self._checkJsonPathExists()
        with open(self.defaultPath, "w") as f:
            json.dump(output_nodes, f, indent=4)

        return output_nodes
    
    @openJsonFile
    def importNodesFromJson(self, data):

        created_nodes = {}

        for node_name, info in data["nodes"].items():
            type_name = info["type"]
            root_path = info[("root")]
            root = hou.node(root_path)
            path = info["path"]
            parent = hou.node(path)

            # Check if parent node exists. If not, then creates parent node first
            if parent is None:
                parent_data = info.get("parent", {})
                parent_name = parent_data.get("name")
                parent_type = parent_data.get("type")
                parent = root.createNode(parent_type, parent_name)
            
            # Create nodes from data
            node = parent.createNode(type_name, node_name)
            created_nodes[node_name] = node

        return created_nodes

    @openJsonFile
    def setNodeDataFromJson(self, data):

        for node_name, info in data["nodes"].items():
            path = info["path"]
            full_node_path = path + node_name
            node = hou.node(full_node_path)
    
            # Set parameters
            parms = info.get("parm", {})
            if parms:
                node.setParmsFromData(parms)

            # Set children parameters
            children_data = info.get("child") or {}
            if children_data:
                node.setChildrenFromData(children_data)
        
            # Set Inputs
            if "input" in info:
                node.setInputsFromData(info["input"])
        
            # Set Flags
            flag_data = info.get("flag", {})
            flag_methods = {
                "display"   : getattr(node, "setDisplayFlag", None),
                "render"    : getattr(node, "setRenderFlag", None),
                "template"  : getattr(node, "setTemplateFlag", None),
                "bypass"    : getattr(node, "bypass", None)
            }

            for flag, method in flag_methods.items():
                if flag_data.get(flag) and method is not None: # Check if the method exists
                    method(True)
        
            node.moveToGoodPosition()
