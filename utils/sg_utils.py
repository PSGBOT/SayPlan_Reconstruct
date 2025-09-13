import networkx as nx

class Node():
    """
    EFFECTS: 
        Used for representation of both instance and part.
    ATTRIBUTES: 
        nodeID: unique id of the instance/part. Instance id will be an string index; Part id will be sample_{x}_mask{y}
        nodeType: the name of the instance/part
        partGraph: an nx.MultiDiGraph. Nodes of the MultiDiGraph will be Nodes storing the parts of the instance/part described by this Node. Edges of the MultiDiGraph will be the (kinematic) relationships among the parts. NOTE: only nodes effective to the current task would be placed in the nx.MultiDiGraph()
        partNodes: a dict that stores all the parts of this node
        keptSG: a list storing the effective parts for a certain task, need to be refreshed for each pruning
        owner: id of the father node; "" for instances
    """
    def __init__(self, nodeID: str = "-1", nodeType: str = "null", description: str = "nil", partGraph: nx.MultiDiGraph = nx.MultiDiGraph(), partNodes = {}, owner: str = ""):
        self.nodeID = nodeID
        self.nodeType = nodeType
        self.description = description
        self.partGraph = partGraph
        self.partNodes = partNodes
        self.keptSG = []
        self.owner = owner
    
def recursive_tree_constructor_without_kinematic(part, ownerID) -> Node:
    """
    INPUTS: 
        part: JSON format description of the part; NOTE: without kinematic relationships!!!
        ownerID: str, father node; "" if adding nodes for instances
    EFFECTS:
        Recursively parse through the input json to construct the node
    OUTPUT: 
        output: a Node storing all information about a part and its parts
    """
    instanceID = part.get("id", "")
    instanceDes = part.get("instance description", {})
    if instanceDes == "":
        instanceDes = {}
    instanceType = instanceDes.get("name", part.get("kaf_name", ""))
    if ownerID == "":
        instanceDescription = part.get("instance description", "")
    else:
        instanceDescription = "nil"
    partGraph = nx.MultiDiGraph()
    partList = part.get("children", [])
    partNodes = {}
    for subpart in partList:
        partNode = recursive_tree_constructor_without_kinematic(subpart, instanceID)
        partID = partNode.nodeID
        partNodes[partID] = partNode
    instanceNode = Node(
        nodeID=str(instanceID),
        nodeType=instanceType,
        description=instanceDescription,
        partGraph=partGraph,
        partNodes=partNodes,
        owner=ownerID
    )
    return instanceNode

def recursive_tree_constructor_add_kinematic(parts, node):
    """
    INPUTS: 
        part: JSON format description of the part; NOTE: with kinematic relationships!!!
        node: node to be added kinematic relationships 
    EFFECTS:
        Recursively parse through the input json to construct the kinematic relations under this node
    """
    partList = parts.get("children", [])
    kinematicRelations = parts.get("kinematic_relations", [])
    partGraph = node.partGraph
    for part in node.keptSG:
        for subpart in partList:
            if part == subpart.get("id", ""):
                recursive_tree_constructor_add_kinematic(subpart, node.partNodes[part])
    for kinematicRelation in kinematicRelations:
        subject_id = kinematicRelation.get("subject")
        object_id = kinematicRelation.get("object")
        if subject_id in node.keptSG and object_id in node.keptSG:
            partGraph.add_edge(
                subject_id,
                object_id,
                subject=kinematicRelation.get("subject", ""),
                object=kinematicRelation.get("object", ""),
                joint_type=kinematicRelation.get("joint_type", ""),
                controllable=kinematicRelation.get("controllable", ""),
                root=kinematicRelation.get("root", ""),
                subject_function=kinematicRelation.get("subject_function", []),
                object_function=kinematicRelation.get("object_function", []),
                subject_desc=kinematicRelation.get("subject_desc", ""),
                object_desc=kinematicRelation.get("object_desc", "")
            )
    
    return
        
def recursive_tree_constructor_with_kinematic(part, ownerID) -> Node:
    """
    INPUTS: 
        part: JSON format description of the part; NOTE: with kinematic relationships!!!
        ownerID: str, father node; "" if adding nodes for instances
    EFFECTS:
        Recursively parse through the input json to construct the node
    OUTPUT: 
        output: a Node storing all information about a part and its parts
    """
    instanceID = part.get("id", "")
    instanceType = part.get("instance description", {}).get("name", part.get("kaf_name", ""))
    kinematicRelations = part.get("kinematic_relations", [])
    partGraph = nx.MultiDiGraph()
    partList = part.get("children", [])
    partNodes = {}
    for subpart in partList:
        partNode = recursive_tree_constructor_with_kinematic(subpart, instanceID)
        partID = partNode.nodeID
        partNodes[partID] = partNode
        partGraph.add_node(partID, node=partNode)
    for kinematicRelation in kinematicRelations:
        subject_id = kinematicRelation.get("subject")
        object_id = kinematicRelation.get("object")
        if subject_id in partNodes and object_id in partNodes:
            partGraph.add_edge(
                subject_id,
                object_id,
                subject=kinematicRelation.get("subject", ""),
                object=kinematicRelation.get("object", ""),
                joint_type=kinematicRelation.get("joint_type", ""),
                controllable=kinematicRelation.get("controllable", ""),
                root=kinematicRelation.get("root", ""),
                subject_function=kinematicRelation.get("subject_function", []),
                object_function=kinematicRelation.get("object_function", []),
                subject_desc=kinematicRelation.get("subject_desc", ""),
                object_desc=kinematicRelation.get("object_desc", "")
            )
    instanceNode = Node(
        nodeID=str(instanceID),
        nodeType=instanceType,
        partGraph=partGraph,
        partNodes=partNodes,
        owner=ownerID
    )
    return instanceNode

class SceneGraphDatabase:
    def __init__(self, sceneGraph=None):
        """
        INPUT: 
            sceneGraph: loaded json 
        ATTRIBUTES:
            instancesGraph: an nx.MultiDiGraph. Nodes will be instances in the scene graph; Edges will be instance level relations
            instanceNodes: a dict. Stores all the instance-level objectsd. Helps in LLM pruning for task planning
        """
        self.instancesGraph = nx.MultiDiGraph()
        self.instanceNodes = {}
        if sceneGraph:
            self.load_from_scene_graph(sceneGraph, 1)
            
    def add_kinematic_relations(self, sceneGraph, keptSG):
        for instanceID in keptSG:
            for instance in sceneGraph.get("objects", []):
                if instance.get("id") == instanceID:
                    instanceNode = self.instanceNodes[instanceID]
                    recursive_tree_constructor_add_kinematic(instance,instanceNode)
            
    
    def load_from_scene_graph(self, sceneGraph, mode):
        """
        INPUT: 
            sceneGraph: loaded json
            mode: 0: construct the tree with kinematic relations. 1, construct the node-only tree, leave kinematic relations for later stages
        EFFECTS: 
            Construct the objects graph based on the input loaded json. The object-part tree would be constructed recursively.
        """
        if mode == 0:
            for instance in sceneGraph.get("objects", []):
                instanceNode = recursive_tree_constructor_with_kinematic(instance, "")
                instanceID = instanceNode.nodeID
                self.instanceNodes[instanceID] = instanceNode
                self.instancesGraph.add_node(instanceID, node=instanceNode)
        if mode == 1:
            for instance in sceneGraph.get("objects", []):
                instanceNode = recursive_tree_constructor_without_kinematic(instance, "")
                instanceID = instanceNode.nodeID
                self.instanceNodes[instanceID] = instanceNode
                self.instancesGraph.add_node(instanceID, node=instanceNode)
        for relationship in sceneGraph.get("relationships", []):
                subject = relationship.get("subject", "")
                object = relationship.get("object", "")
                predicate = relationship.get("predicate", "")
                self.instancesGraph.add_edge(subject, object, predicate=predicate)