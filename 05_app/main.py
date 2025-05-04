import os
import json
import hou

class NodesToJson:
 
    def __init__(self):
        self.hip = hou.expandString("$HIP")
        self.default_path = os.path.join(self.hip, "data", "nodeExportData.json").replace("\\", "/")

    def checkJsonPathExists(self):

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.default_path), exist_ok=True)

        # Ensure the file exists
        if not os.path.exists(self.default_path):
            with open(self.default_path, "w") as f:
                json.dump({}, f)

    def exportSelectedNodesToJson(self):
   
        # Get selected nodes
        selected_nodes = hou.selectedNodes()

        output_nodes = {"nodes": {}}

        for node in selected_nodes:
            # Get the path of the node's root 
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
                          "template" : node.node.isTemplateFlagSet() if hasattr(node, 'isTemplateFlagSet') else False,
                          "bypass"   : node.isBypassed() if hasattr(node, 'isBypassed') else False
                          },
                "child" : {} 

            }

            # Check if the node has children and may need to be unlocked
            if node.type().name().endswith(("solver", "net", "vop")):
                
                node.allowEditingOfContents()  # Unlock node

                children = node.childrenAsData() if hasattr(node, 'childrenAsData') else {}
                node_dict["child"] = children

                node.matchCurrentDefinition()  # Lock node
                
            else:

                children = node.childrenAsData() if hasattr(node, 'childrenAsData') else {}
                node_dict["child"] = children

            # Add to the output dictionary
            output_nodes["nodes"][node.name()] = node_dict

        # Ensure directory and JSON file exists
        self.checkJsonPathExists()

        # Write it to a JSON file
        with open(self.default_path, "w") as f:
            json.dump(out, f, indent=4)

        return output_nodes
    
    def importNodesFromJson(self):
   
        # Ensure directory and JSON file exists
        self.checkJsonPathExists()

        # Load the JSON file
        with open(self.default_path, "r") as f:
            data = json.load(f)

        created_nodes = {}  # Create dict to hold imported nodes

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

            # Add imported nodes to dict by name
            created_nodes[node_name] = node

        return created_nodes

    def setNodeDataFromJson(self):

        # Ensure directory and JSON file exists
        self.checkJsonPathExists()

        # Load the JSON file
        with open(self.default_path, "r") as f:
            data = json.load(f)

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
    
            if flag_data.get("display"):
                node.setDisplayFlag(True)
        
            if flag_data.get("render"):
                node.setRenderFlag(True)

            if flag_data.get("template"):
                node.setTemplateFlag(True)
        
            if flag_data.get("bypass"):
                node.bypass(True)
        
            #Tidy Up
            node.moveToGoodPosition()

# For testing purpose only
if __name__ == "__main__":
    pass