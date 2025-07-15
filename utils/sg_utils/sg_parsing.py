import json
import networkx as nx
from collections import defaultdict
import pandas as pd

class Node():
    """
    Used for representation of both instance and part.
    nodeID: unique id of the instance/part. Instance id will be an string index; Part id will be sample_{x}_mask{y}
    nodeType: the name of the instance/part
    parts: an nx.DiGraph. Nodes of the DiGraph will be Nodes storing the parts of the instance/part described in this Node. Edges of the DiGraph will be the (kinematic) relationships among the parts.
    """
    def __init__(self, nodeID: str = "-1", nodeType: str = "null", parts: nx.DiGraph = nx.DiGraph()):
        self.nodeID = nodeID
        self.nodeType = nodeType
        self.parts = parts
    
def recursive_tree_constructor(part) -> Node:
    """
    INPUT: 
        part: JSON format description of the part
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
    for part in partList:
        partNode = recursive_tree_constructor(part)
        partID = partNode.nodeID
        partNodes[partID] = partNode
        partGraph.add_node(partID, node=partNode)
    for kinematicRelation in kinematicRelations:
        subject = kinematicRelation.get("subject", "")
        obj = kinematicRelation.get("object", "")
    
        if subject in partNodes and obj in partNodes:
            partGraph.add_edge(
                subject,
                obj,
                joint_type=kinematicRelation.get("joint_type", ""),
                controllable=kinematicRelation.get("controllable", ""),
                root=kinematicRelation.get("root", ""),
                subject_function=kinematicRelation.get("subjectt_function", []),
                object_function=kinematicRelation.get("object_function", []),
                subject_desc=kinematicRelation.get("subject_desc", ""),
                object_desc=kinematicRelation.get("object_desc", "")
            )
    instanceNode = Node(
        nodeID=str(instanceID),
        nodeType=instanceType,
        parts=partGraph
    )
    return instanceNode

class SceneGraphDatabase:
    def __init__(self, sceneGraph=None):
        """
        INPUT: 
            sceneGraph: loaded json 
        ATTRIBUTES:
            instancesGraph: an nx.DiGraph, nodes will be instances in the scene graph, edges will be instance level relations
        """
        self.instancesGraph = nx.DiGraph()
        if sceneGraph:
            self.load_from_scene_graph(sceneGraph)
    
    def load_from_scene_graph(self, sceneGraph):
        """
        INPUT: 
            sceneGraph: loaded json
        EFFECT: 
            Construct the objects graph based on the input loaded json. The object-part tree would be constructed recursively.
        """
        instanceNodes = {}
        for instance in sceneGraph.get("objects", []):
            instanceNode = recursive_tree_constructor(instance)
            instanceID = instanceNode.nodeID
            instanceNodes[instanceID] = instanceNode
            self.instancesGraph.add_node(instanceID, node=instanceNode)
        for relationship in sceneGraph.get("relationships", []):
            subject = relationship.get("relationship", "")
            object = relationship.get("object", "")
            predicate = relationship.get("predicate", "")
            self.instancesGraph.add_edge(subject, object, predicate=predicate)
        
