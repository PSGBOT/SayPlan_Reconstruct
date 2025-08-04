import networkx as nx
import json
import argparse
from utils import sg_utils
from utils.llm_utils.llm_service import *
from utils.llm_utils.gemini_message import *

class Pipeline():
    """
    EFFECTS:
        Used to represent the pipeline described in the SayPlan paper
    ATTRIBUTES:
        sceneGraphDatabase: SceneGraphDatabase that stores the environment scene graph. It should not be modified once the environment is loaded
        keptSG: list of dict, stores the effective parts of the scene graph
        currentLevel: dict, showing the current focusing id-node pair
        task: str, task command
    """
    def __init__(self, sgPath: str, task: str = ""):
        with open(sgPath, 'r') as f:
            sceneGraph = json.load(f)   
        if sceneGraph is None:
            return 
        self.sceneGraphDatabase = sg_utils.SceneGraphDatabase(sceneGraph)
        self.keptSG = []
        self.task = task
        self.llmClient = GeminiVLMClient()

   
    def prune_graph(self):
        """
        EFFECTS:
            Prune the environment graph with LLM recursively
        """
        self.keptSG = []
        instanceMsg = decision_prune_graph_instance_level(self.task, self.sceneGraphDatabase, self.sceneGraphDatabase.instanceNodes)
        instanceResult = self.llmClient.infer(instanceMsg)
        selectedIDs = instanceResult.get("selected_ids", [])
        for selectedID in selectedIDs:
            selectedNode = self.sceneGraphDatabase.instanceNodes[selectedID]
            self.recursive_prune_node(selectedNode)
            self.keptSG.append(selectedID)

            
    def recursive_prune_node(self, instanceNode):
        """
        EFFECTS:
            Helper function to prune the environment graph with LLM recursively, add nodes to nx.MultiDiGraph.
        """
        instanceNode.keptSG = []
        msg = decision_prune_graph_part_level(self.task, instanceNode)
        result = self.llmClient.infer(msg)
        selectedIDs = result.get("selected_ids", [])
        for selectedID in selectedIDs:
            selectedNode = instanceNode.partNodes[selectedID]
            selectedNode.partGraph.add_node(selectedID, node=selectedNode)
            self.recursive_prune_node(selectedNode)
            instanceNode.keptSG.append(selectedID)


    def plan(self):
        """
        EFFECTS: 
            task planning
        TODO: Add iterative re-planning, add kinematic tree to the re-planning only
        """
        planMsg = task_planning(self.keptSG, self.sceneGraphDatabase, self.task)
        plan = self.llmClient.infer(planMsg)
        return plan
    
    def replan(self, jsonPath, plan):
        jsonData = json.load(jsonPath)
        self.sceneGraphDatabase.add_kinematic_relations(jsonData, self.keptSG)
        replanMsg = task_replanning(self.keptSG, self.sceneGraphDatabase, self.task, plan)
        replan = self.llmClient.infer(replanMsg)
        return replan
    
    def run(self, jsonPath):
        self.prune_graph()
        plan = self.plan()
        print(plan)
        replan = self.replan(jsonPath, plan)
        print(replan)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate plans for tasks and environment scene graphs"
    )
    parser.add_argument(
        "--sgPath", type=str, required=True, help="Path to the scene graph JSON file"
    )
    parser.add_argument(
        "--sgKinematicPath", type=str, required=True, help="Path to the scene graph kinematic relations JSON file"
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="Task that the robot is going to complete",
    )

    args = parser.parse_args()
    pipeline = Pipeline(args.sgPath, args.task)
    pipeline.run(args.sgKinematicPath)