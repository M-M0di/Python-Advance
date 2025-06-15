# ****************************************************************************************
# Content : Contains logic for exporting/importing nodes and their data
# -----
# Date:
# Created  : 29/04/2025
# Modified : 15/06/2025
# -----
# Dependencies = hou
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import hou

class NodeSnapLogic:
    def __init__(self):
        pass

    def exportSelectedNodesToJson(self):
        selectedNodes = hou.selectedNodes()
        outputNodes   = {"nodes": {}}

        for node in selectedNodes:
            path     = node.parent().path().rstrip("/")
            rootPath = "/".join(path.split("/")[:2]) + "/"

            nodeDict = {
                "path"          : node.parent().path().rstrip("/") + "/",
                "type"          : node.type().name(),
                "parent"        : {
                    "name"      : node.parent().name(),
                    "type"      : node.parent().type().name()
                                  },
                "root"          : rootPath,
                "parm"          : node.parmsAsData(),
                "parm_label"    : {parm.name(): parm.description() for parm in node.parms()},
                "input"         : node.inputsAsData(),
                "flag"          : {
                    "display"   : node.isDisplayFlagSet() if hasattr(node, 'isDisplayFlagSet') else False,
                    "render"    : node.isRenderFlagSet() if hasattr(node, 'isRenderFlagSet') else False,
                    "template"  : node.isTemplateFlagSet() if hasattr(node, 'isTemplateFlagSet') else False,
                    "bypass"    : node.isBypassed() if hasattr(node, 'isBypassed') else False
                                  },
                "child"         : {}
            }

            for child in node.children():
                childData = {
                    "name"          : child.name(),
                    "path"          : child.parent().path().rstrip("/") + "/",
                    "type"          : child.type().name(),
                    "parent"        : {
                        "name"      : child.parent().name(),
                        "type"      : child.parent().type().name()
                                      },
                    "root"          : rootPath,
                    "parm"          : child.parmsAsData(),
                    "parm_label"    : {parm.name(): parm.description() for parm in child.parms()},
                    "input"         : child.inputsAsData(),
                    "flag"          : {
                        "display"   : child.isDisplayFlagSet() if hasattr(child, 'isDisplayFlagSet') else False,
                        "render"    : child.isRenderFlagSet() if hasattr(child, 'isRenderFlagSet') else False,
                        "template"  : child.isTemplateFlagSet() if hasattr(child, 'isTemplateFlagSet') else False,
                        "bypass"    : child.isBypassed() if hasattr(child, 'isBypassed') else False
                                      },
                    "grandchild": {}
                }

                if child.type().name().endswith(("solver", "net", "vop")):
                    child.allowEditingOfContents()
                    childData["grandchild"] = child.childrenAsData()
                    child.matchCurrentDefinition()
                else:
                    for grandchild in child.children():
                        grandchildData = {
                            "name"          : grandchild.name(),
                            "path"          : grandchild.parent().path().rstrip("/") + "/",
                            "type"          : grandchild.type().name(),
                            "parent"        : {
                                "name"      : grandchild.parent().name(),
                                "type"      : grandchild.parent().type().name()
                                              },
                            "root"          : rootPath,
                            "parm"          : grandchild.parmsAsData(),
                            "parm_label"    : {parm.name(): parm.description() for parm in grandchild.parms()},
                            "input"         : grandchild.inputsAsData(),
                            "flag"          : {
                                "display"   : grandchild.isDisplayFlagSet() if hasattr(grandchild, 'isDisplayFlagSet') else False,
                                "render"    : grandchild.isRenderFlagSet() if hasattr(grandchild, 'isRenderFlagSet') else False,
                                "template"  : grandchild.isTemplateFlagSet() if hasattr(grandchild, 'isTemplateFlagSet') else False,
                                "bypass"    : grandchild.isBypassed() if hasattr(grandchild, 'isBypassed') else False
                                              }
                        }
                        
                        childData["grandchild"][grandchild.name()] = grandchildData

                nodeDict["child"][child.name()] = childData

            outputNodes["nodes"][node.name()] = nodeDict

        return outputNodes

    def importNodesFromJson(self, allNodeData, nodeDataDict):
        createdNodes = {}

        for node_name, info in allNodeData.items():
            if node_name in createdNodes:
                continue

            type_name = info["type"]
            root_path = info["root"]
            path = info["path"]
            parent_info = info.get("parent", {})
            parent_name = parent_info.get("name")
            parent_type = parent_info.get("type")

            existing_node = hou.node(f"{path}{node_name}")
            if existing_node:
                createdNodes[node_name] = existing_node
                continue

            parent = (
                hou.node(path) or
                createdNodes.get(parent_name) or
                hou.node(f"{root_path.rstrip('/')}/{parent_name}")
            )
            
            if not parent and (root := hou.node(root_path)):
                parent = root.createNode(parent_type, parent_name)
                createdNodes[parent_name] = parent

            if parent:
                node = parent.createNode(type_name, node_name)
                createdNodes[node_name] = node

    def setNodeDataFromJson(self, checkedNodeData, nodeDataDict):
        if not checkedNodeData:
            return

        for nodeName, nodeInfo in nodeDataDict["nodes"].items():
            nodePath = nodeInfo["path"] + nodeName
            node = hou.node(nodePath)
            
            parameterData = nodeInfo.get("parm", {})
            if parameterData:
                node.setParmsFromData(parameterData)

            childParameterData = nodeInfo.get("child") or {}
            if childParameterData:
                node.setParmsFromData(childParameterData)

            grandchildParameterData = nodeInfo.get("grandchild") or {}
            if grandchildParameterData:
                if node.type().name().endswith(("solver", "net", "vop")):
                    node.setChildrenFromData(grandchildParameterData)
                else:
                    node.setParmsFromData(grandchildParameterData)

            inputData = nodeInfo.get("input")
            if inputData:
                node.setInputsFromData(inputData)

            flagData    = nodeInfo.get("flag", {})
            flagMethods =     {
                "display"   : getattr(node, "setDisplayFlag", None),
                "render"    : getattr(node, "setRenderFlag", None),
                "template"  : getattr(node, "setTemplateFlag", None),
                "bypass"    : getattr(node, "bypass", None)
                              }

            for flagName, flagMethod in flagMethods.items():
                if flagData.get(flagName) and flagMethod:
                    flagMethod(True)
                    
            node.matchCurrentDefinition()
            node.moveToGoodPosition()