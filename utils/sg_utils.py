import networkx as nx

class Node():
    """
    EFFECTS: 
        Used for representation of both instance and part.
    ATTRIBUTES: 
        nodeID: unique id of the instance/part. Instance id will be an string index; Part id will be sample_{x}_mask{y}
        nodeType: the name of the instance/part
        partGraph: an nx.DiGraph. Nodes of the DiGraph will be Nodes storing the parts of the instance/part described by this Node. Edges of the DiGraph will be the (kinematic) relationships among the parts.
        partNodes: a dict that stores all the parts of this node
    """
    def __init__(self, nodeID: str = "-1", nodeType: str = "null", partGraph: nx.DiGraph = nx.DiGraph(), partNodes = {}, owner: str = ""):
        self.nodeID = nodeID
        self.nodeType = nodeType
        self.partGraph = partGraph
        self.partNodes = partNodes
        self.owner = owner
    
def recursive_tree_constructor(part, ownerID) -> Node:
    """
    INPUT: 
        part: JSON format description of the part
        ownerID: str, father node; "" if adding nodes for instances
    EFFECTS:
        Recursively parse through the input json to construct the node
    OUTPUT: 
        output: a Node storing all information about a part and its parts
    """
    instanceID = part.get("id", "")
    instanceType = part.get("kaf_name", "")
    kinematicRelations = part.get("kinematic_relations", [])
    partGraph = nx.DiGraph()
    partList = part.get("parts", [])
    partNodes = {}
    for subpart in partList:
        partNode = recursive_tree_constructor(subpart, instanceID)
        partID = partNode.nodeID
        partNodes[partID] = partNode
        partGraph.add_node(partID, node=partNode)
    for kinematicRelation in kinematicRelations:
        subject = partNodes[kinematicRelation.get("subject", "")]
        obj = partNodes[kinematicRelation.get("object", "")]
    
        if subject in partNodes and obj in partNodes:
            partGraph.add_edge(
                subject,
                obj,
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
            instancesGraph: an nx.DiGraph. Nodes will be instances in the scene graph; Edges will be instance level relations
            instanceNodes: a dict. Stores all the instance-level objectsd. Helps in LLM pruning for task planning
        """
        self.instancesGraph = nx.DiGraph()
        self.instanceNodes = {}
        if sceneGraph:
            self.load_from_scene_graph(sceneGraph)
            
    def load_from_scene_graph(self, sceneGraph):
        """
        INPUT: 
            sceneGraph: loaded json
        EFFECTS: 
            Construct the objects graph based on the input loaded json. The object-part tree would be constructed recursively.
        """
        for instance in sceneGraph.get("objects", []):
            instanceNode = recursive_tree_constructor(instance, "")
            instanceID = instanceNode.nodeID
            self.instanceNodes[instanceID] = instanceNode
            self.instancesGraph.add_node(instanceID, node=instanceNode)
        for relationship in sceneGraph.get("relationships", []):
            subject = relationship.get("subject", "")
            object = relationship.get("object", "")
            predicate = relationship.get("predicate", "")
            self.instancesGraph.add_edge(subject, object, predicate=predicate)
        