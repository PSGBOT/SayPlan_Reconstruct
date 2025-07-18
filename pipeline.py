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
        self.sceneGraphDatabase = sg_utils.SceneGraphDatabase(sceneGraph)
        self.keptSG = []
        self.currentLevel = self.sceneGraphDatabase.instanceNodes
        self.task = task
        self.llmClient = GeminiVLMClient()


    def get_pruned_level(self, llmOutputJson):
        """
        INPUTS: 
            llmOutputJson: json format output.
        EFFECTS: 
            Update the keptSG, add the kept nodes in the current level; Update the currentLevel with nodes in the next level
        OUTPUTS:
            end: bool, false if llm outputs an empty json
        """
        selectedIDs = llmOutputJson.get("selected_ids", [])
        if selectedIDs == []:
            return False
        levelDict = {}
        nextLevelDict = {}
        for selectedID in selectedIDs:
            selectedNode = self.currentLevel[selectedID]
            levelDict[selectedID] = selectedNode
            nextLevelDict.update(selectedNode.partNodes)
        self.keptSG.append(levelDict)
        self.currentLevel = nextLevelDict
        return True
        
    
    def prune_graph(self):
        """
        EFFECTS:
            Prune the environment graph with LLM
        """
        instanceMsg = decision_prune_graph_instance_level(self.task, self.sceneGraphDatabase, self.currentLevel)
        instanceResult = self.llmClient.infer(instanceMsg)
        prune = self.get_pruned_level(instanceResult)
        while prune:
            partMsg = decision_prune_graph_part_level(self.task, self.currentLevel)
            partResult = self.llmClient.infer(partMsg)
            prune = self.get_pruned_level(partResult)


    def plan(self):
        """
        EFFECTS: 
            task planning
        """
        planMsg = task_planning(self.keptSG, self.sceneGraphDatabase, self.task)
        plan = self.llmClient.infer(planMsg)
        return plan
    
    def run(self):
        self.prune_graph()
        plan = self.plan()
        print(plan)
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate plans for tasks and environment scene graphs"
    )
    parser.add_argument(
        "--sgPath", type=str, required=True, help="Path to the scene graph JSON file"
    )
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="Task that the robot is going to complete",
    )

    args = parser.parse_args()
    pipeline = Pipeline(args.sgPath, args.task)
    pipeline.run()