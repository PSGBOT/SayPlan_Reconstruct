import json
import networkx as nx
from collections import defaultdict
import pandas as pd

class SceneGraphDatabase:
    def __init__(self, scene_graph=None):
        self.objects = nx.DiGraph()
        self.parts = nx.DiGraph()
        self.obj_obj_rels = nx.DiGraph()
        self.obj_part_owns = nx.DiGraph()
        self.part_part_rels = nx.DiGraph()
        
        if scene_graph:
            self.load_from_scene_graph(scene_graph)
    
    def load_from_scene_graph(self, scene_graph):
        index_to_uid = {}
        
        # Process objects and their parts
        for idx, obj in enumerate(scene_graph["objects"]):
            obj_uid = f"{obj['level']}_{obj['id']}"
            index_to_uid[idx] = obj_uid
            
            # Add object to objects graph
            self.objects.add_node(obj_uid, **{
                "level": obj["level"],
                "kaf_name": obj["kaf_name"],
                "kaf_index": obj["kaf_index"],
                "overlap_score": obj["overlap_score"],
                "bbox": obj["bbox"]
            })
            
            # Add object to obj_part_owns even if it has no parts
            if obj_uid not in self.obj_part_owns:
                self.obj_part_owns.add_node(obj_uid)
            
            # Process parts
            for part in obj["parts"]:
                part_uid = f"{obj_uid}_{part['part_id']}"
                
                # Add part to parts graph
                self.parts.add_node(part_uid, **{
                    "description": part["description"],
                    "center": part["center"],
                    "convergence": part["convergence"]
                })
                
                # Add ownership relationship
                self.obj_part_owns.add_edge(obj_uid, part_uid, relationship="ownership")
        
        # Process kinematic relationships
        for obj in scene_graph["objects"]:
            obj_uid = f"{obj['level']}_{obj['id']}"
            
            for rel in obj["kinematic_relations"]:
                parent_uid = f"{obj_uid}_{rel['root']}"
                child_uid = f"{obj_uid}_{rel['object']}"
                
                # Only add if both parts exist
                if parent_uid in self.parts and child_uid in self.parts:
                    self.part_part_rels.add_edge(parent_uid, child_uid, **{
                        "joint_type": rel["joint_type"],
                        "controllable": rel["controllable"],
                        "subject_function": rel["subject"],
                        "object_function": rel["object_function"]
                    })
        
        # Process object-object relationships
        for rel in scene_graph.get("relationships", []):
            subject_idx = rel["subject"]
            object_idx = rel["object"]
            
            if subject_idx in index_to_uid and object_idx in index_to_uid:
                subject_uid = index_to_uid[subject_idx]
                object_uid = index_to_uid[object_idx]
                
                # Add relationship if both objects exist
                if subject_uid in self.objects and object_uid in self.objects:
                    self.obj_obj_rels.add_edge(subject_uid, object_uid, 
                                               predicate=rel["predicate"])
    
    def get_object_parts(self, obj_uid):
        """Get all parts belonging to an object"""
        if obj_uid in self.obj_part_owns:
            return list(self.obj_part_owns.successors(obj_uid))
        return []
    
    def get_part_kinematics(self, part_uid):
        """Get kinematic relationships for a part"""
        if part_uid not in self.part_part_rels:
            return {"parents": [], "children": []}
        
        return {
            "parents": list(self.part_part_rels.predecessors(part_uid)),
            "children": list(self.part_part_rels.successors(part_uid))
        }
    
    def get_object_relationships(self, obj_uid):
        """Get semantic relationships for an object"""
        if obj_uid not in self.obj_obj_rels:
            return {"outgoing": [], "incoming": []}
        
        return {
            "outgoing": list(self.obj_obj_rels.successors(obj_uid)),
            "incoming": list(self.obj_obj_rels.predecessors(obj_uid))
        }
    
    def prune_low_confidence(self, obj_threshold=0.4, part_threshold=0.4):
        """Prune low-confidence objects and parts"""
        # Prune objects
        to_remove_objs = [node for node, data in self.objects.nodes(data=True) 
                         if data.get("overlap_score", 0) < obj_threshold]
        
        for obj_uid in to_remove_objs:
            # Remove from all graphs
            self.objects.remove_node(obj_uid)
            
            if obj_uid in self.obj_obj_rels:
                self.obj_obj_rels.remove_node(obj_uid)
                
            if obj_uid in self.obj_part_owns:
                # Remove all parts first
                for part_uid in list(self.obj_part_owns.successors(obj_uid)):
                    self.parts.remove_node(part_uid)
                    if part_uid in self.part_part_rels:
                        self.part_part_rels.remove_node(part_uid)
                self.obj_part_owns.remove_node(obj_uid)
        
        # Prune parts
        to_remove_parts = [node for node, data in self.parts.nodes(data=True) 
                          if data.get("convergence", 0) < part_threshold]
        
        for part_uid in to_remove_parts:
            # Remove from parts and relationships
            self.parts.remove_node(part_uid)
            if part_uid in self.part_part_rels:
                self.part_part_rels.remove_node(part_uid)
            
            # Remove from ownership graph
            for owner in list(self.obj_part_owns.predecessors(part_uid)):
                self.obj_part_owns.remove_edge(owner, part_uid)
    
    def to_dataframes(self):
        """Convert to pandas DataFrames"""
        return {
            "objects": pd.DataFrame([{"uid": n, **d} for n, d in self.objects.nodes(data=True)]),
            "parts": pd.DataFrame([{"uid": n, **d} for n, d in self.parts.nodes(data=True)]),
            "obj_obj_rels": pd.DataFrame([
                {"source": u, "target": v, **d} 
                for u, v, d in self.obj_obj_rels.edges(data=True)
            ]),
            "obj_part_owns": pd.DataFrame([
                {"object": u, "part": v} 
                for u, v in self.obj_part_owns.edges()
            ]),
            "part_part_rels": pd.DataFrame([
                {"parent": u, "child": v, **d} 
                for u, v, d in self.part_part_rels.edges(data=True)
            ])
        }

# Load scene graph
with open("C:\\PartLevelProject\\SayPlan_Reconstruct\\sample_scene_graph.json", "r") as f:
    scene_graph = json.load(f)

# Create database
sg_db = SceneGraphDatabase(scene_graph)

# Example usage
toilet = "level2_0"
print(f"Object: {toilet}")
if toilet in sg_db.objects:
    print(sg_db.objects.nodes[toilet])
    print("Parts:", sg_db.get_object_parts(toilet))
else:
    print("Object not found in database")

# Save to GraphML
for name, graph in [
    ("objects", sg_db.objects),
    ("parts", sg_db.parts),
    ("obj_obj_rels", sg_db.obj_obj_rels),
    ("obj_part_owns", sg_db.obj_part_owns),
    ("part_part_rels", sg_db.part_part_rels)
]:
    # Convert attributes to strings for GraphML compatibility
    for node, data in graph.nodes(data=True):
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = ",".join(map(str, value))
            elif not isinstance(value, (str, int, float)):
                data[key] = str(value)
    
    nx.write_graphml(graph, f"{name}.graphml")