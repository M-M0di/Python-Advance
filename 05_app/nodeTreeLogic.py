# ****************************************************************************************
# Content : Contains logic for building node hierarchy from JSON data
# -----
# Date:
# Created  : 22/05/2025
# Modified : 13/06/2025
# -----
# Author  : Mayank Modi
# Email   : mayank_modi@outlook.com
# ****************************************************************************************

def buildNodeHierarchy(nodesData):
    hierarchy = []
    stack = []

    child_keys = ["child", "grandchild"]

    for rootName, rootData in reversed(list(nodesData.items())):
        rootNode = {
            "name"      : rootName,
            "type"      : rootData.get("type", ""),
            "parm"      : rootData.get("parm", {}) or rootData.get("parms", {}),
            "label"     : rootData.get("parm_label", {}),
            "children"  : []
        }
        hierarchy.append(rootNode)
        stack.append((rootData, rootNode))

    while stack:
        currentData, currentNode = stack.pop()

        for key in child_keys:
            childDict = currentData.get(key)
            if not isinstance(childDict, dict):
                continue

            for childName, childData in reversed(list(childDict.items())):
                parm_data = childData.get("parm") or childData.get("parms") or {}
                label_data = childData.get("parm_label", {})

                childNode = {
                    "name"      : childName,
                    "type"      : childData.get("type", ""),
                    "parm"      : parm_data,
                    "label"     : label_data,
                    "children"  : []
                }
                currentNode["children"].append(childNode)
                stack.append((childData, childNode))

    return hierarchy