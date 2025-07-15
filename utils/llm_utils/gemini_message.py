import base64
from io import BytesIO
from PIL import Image


def decision_prune_graph_instance_level(task, sceneGraphDatabase, currentInstanceDict):
    """
    INPUTS:
        task: task for planning
        sceneGraphDatabase: SceneGraphDatabase type. Storing the scene graph
        currentInstanceDict: a dict. Key: instance id; Value: pointer to its node in scene graph database. Storing the current kept instances/parts
    """
    instances = []
    instanceLevelRelations = []
    for instID, node in currentInstanceDict.items():
        instanceDescription = f"id: {instID}, instance type: {node.instanceType}"
        instances.append(instanceDescription)
    for _, _, data in sceneGraphDatabase.instancesGraph.edges(data=True):
        subject = data.get('subject', 'unknown')
        object = data.get('object', 'unknown')
        predicate = data.get('predicate', 'unknown')
        relationDescription = f"subject: {subject}, object: {object}, predicate: {predicate}"
        instanceLevelRelations.append(relationDescription)
    
    promptText = f"""
# Robotic Task Planning: Instance Selection

## Task Objective
{task}

## Available Instances

{";".join(instanceDescription)}

## Relationships among the Instances

{";".join(instanceLevelRelations)}

## Scene Graph Context
The environment contains {len(instanceDescription)} objects, and their relations are given.

## Your Task
Select ONLY instances essential for completing the task. Consider:
1. Direct relevance to task completion
2. Functional parts that enable manipulation
3. Kinematic constraints affecting the task
4. Physical access requirements

## Selection Criteria
INCLUDE instances that:
- Are directly manipulated during the task
- Contain functional parts required for the task
- Provide kinematic constraints critical to task success
- Serve as containers/platforms for target objects
- Enable access to target components

EXCLUDE instances that:
- Are decorative or non-functional
- Have no kinematic relevance to the task
- Are not mentioned or implied in the task description
- Would not be touched during task execution

## Output Format
Return STRICTLY valid JSON with this structure:
{{
  "reasoning": "Concise analysis (1-2 sentences)",
  "selected_ids": ["inst_123", "inst_456", ...]
}}

## Critical Rules
- Select the MINIMAL necessary set
- Use ONLY instance IDs from the 'Available Instances' section
- DO NOT include any explanatory text outside the JSON
- If no instances are needed, return: {{"selected_ids": []}}
""".strip()

    return [
        {
            "role": "user",
            "parts": [{"text": promptText}]
        }
    ]

def decision_prune_graph_part_level(task, sceneGraphDatabase, currentInstanceDict):
    """
    INPUTS:
        task: task for planning
        sceneGraphDatabase: SceneGraphDatabase type. Storing the scene graph
        currentInstanceDict: a dict. Key: instance id; Value: pointer to its node in scene graph database. Storing the current kept instances/parts
    """

    