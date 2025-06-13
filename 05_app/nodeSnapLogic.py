# ****************************************************************************************
# Content : Contains logic for exporting/importing nodes and their data
# -----
# Date:
# Created  : 29/04/2025
# Modified : 13/06/2025
# -----
# Dependencies = hou
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

import hou

class NodeSnapLogic:
    def __init__(self):
        self.createdNodes = {}

    def exportSelectedNodesToJson(self):
        selectedNodes = hou.selectedNodes()
        outputNodes = {"nodes": {}}

        for node in selectedNodes:
            path = node.parent().path().rstrip("/")
            rootPath = "/".join(path.split("/")[:2]) + "/"

            nodeDict = {
                "path"          : node.parent().path().rstrip("/") + "/",
                "type"          : node.type().name(),
                "root_parent":    {
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
                "child": {}
            }

            for child in node.children():
                childData = {
                    "name"          : child.name(),
                    "path"          : child.parent().path().rstrip("/") + "/",
                    "type"          : child.type().name(),
                    "child_parent"  : {
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
                    "grandchild"    : child.childrenAsData() if hasattr(child, 'childrenAsData') else {}
                }

                nodeDict["child"][child.name()] = childData

            outputNodes["nodes"][node.name()] = nodeDict

        return outputNodes

    def createNodeIfNeeded(self, nodeName, nodeInfo, nodeDataDict):
        if nodeName in self.createdNodes:
            self.createdNodes[nodeName]
            
        nodeType = nodeInfo["type"]
        rootPath = nodeInfo.get("root")
        rootNode = hou.node(rootPath)
        parentNode = rootNode

        if "child_parent" in nodeInfo:
            parentInfo = nodeInfo["child_parent"]
            parentName = parentInfo["name"]
            parentType = parentInfo["type"]
            parentPath = f"{rootPath}{parentName}"
            parentNode = hou.node(parentPath)
            
            if not parentNode:
                if parentName in nodeDataDict["nodes"]:
                    parentNode = self.createNodeIfNeeded(parentName, nodeDataDict["nodes"][parentName], nodeDataDict)
                else:
                    parentNode = rootNode.createNode(parentType, parentName)
                    
                self.createdNodes[parentName] = parentNode

        finalPath = f"{parentNode.path()}/{nodeName}"
        existingNode = hou.node(finalPath)
        
        if existingNode:
            self.createdNodes[nodeName] = existingNode
            return existingNode

        newNode = parentNode.createNode(nodeType, nodeName)
        self.createdNodes[nodeName] = newNode
        
        return newNode

    def importNodesFromJson(self, allNodeData, nodeDataDict):
        self.createdNodes = {}
        
        for nodeName, nodeInfo in allNodeData.items():
            self.createNodeIfNeeded(nodeName, nodeInfo, nodeDataDict)
            
        return self.createdNodes

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
                node.setChildrenFromData(grandchildParameterData)

            inputData = nodeInfo.get("input")
            if inputData:
                node.setInputsFromData(inputData)

            flagData = nodeInfo.get("flag", {})
            flagMethods = {
                "display": getattr(node, "setDisplayFlag", None),
                "render": getattr(node, "setRenderFlag", None),
                "template": getattr(node, "setTemplateFlag", None),
                "bypass": getattr(node, "bypass", None)
            }

            for flagName, flagMethod in flagMethods.items():
                if flagData.get(flagName) and flagMethod:
                    flagMethod(True)

            node.moveToGoodPosition()