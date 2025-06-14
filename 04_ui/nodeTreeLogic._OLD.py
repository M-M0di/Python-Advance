# ****************************************************************************************
# Content : Contains logic to build a node hierarchy from JSON data.
# -----
# Date:
# Created  : 22/05/2025
# Modified : 01/06/2025
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************
def buildNodeHierarchy(nodesData):
    """Builds a hierarchical structure of nodes from the provided JSON data."""
    hierarchy = []
    stack = []

    for rootName, rootData in reversed(list(nodesData.items())):
        rootNode = {
            "name": rootName,
            "type": rootData.get("type", {}),
            "parm": rootData.get("parm", {}),
            "label": rootData.get("parm_label", {}),
            "children": [],
        }
        hierarchy.append(rootNode)
        stack.append((rootData, rootNode))

    while stack:
        currentData, currentNode = stack.pop()
        childDict = currentData.get("child") or {}

        for childName in reversed(list(childDict.keys())):
            childData = childDict[childName]
            childNode = {
                "name": childName,
                "type": childData.get("type", {}),
                "parm": childData.get("parm", {}),
                "children": [],
            }
            currentNode["children"].append(childNode)
            stack.append((childData, childNode))

    return hierarchy
