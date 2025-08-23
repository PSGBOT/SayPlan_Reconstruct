import json

def decision_prune_graph_instance_level(task, sceneGraphDatabase, currentInstanceDict):
    """
    INPUTS:
        task: task for planning
        sceneGraphDatabase: SceneGraphDatabase type. Storing the scene graph
        currentInstanceDict: a dict. Key: instance id; Value: pointer to its node in scene graph database. Storing the current kept instances
    """
    instances = []
    instanceLevelRelations = []
    for instID, node in currentInstanceDict.items():
        instanceDescription = f"id: {instID}, instance type: {node.nodeType}"
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

{";".join(instances)}

## Relationships among the Instances

{";".join(instanceLevelRelations)}

## Scene Graph Context
The environment contains {len(instanceDescription)} objects, and their relations are given.

## Your Task
Select ONLY instances essential for completing the task. Consider:
1. Direct relevance to task completion
2. Having relations that affect the task
3. Having unneglegible relations with instances affecting the task
4. Physical access requirements

## Selection Criteria
INCLUDE instances that:
- Are directly manipulated during the task
- Have relations critical to task success
- Serve as containers/platforms for target objects
- Enable access to target components

EXCLUDE instances that:
- Are decorative or non-functional
- Have no relation to the task
- Have no relation to the instances essential to the task
- Are not mentioned or implied in the task description
- Would not be touched during task execution

## Output Format
Return STRICTLY valid JSON with this structure:
{{
  "reasoning": "Concise analysis (1-2 sentences)",
  "selected_ids": ["id 1", "id 2", ...]
}}

## Critical Rules
- Select the MINIMAL necessary set
- Use ONLY instance IDs from the 'Available Instances' section
- DO NOT include any explanatory text outside the JSON
- If no instances are needed, return: {{""reasoning": "", selected_ids": []}}
""".strip()

    return [
        {
            "role": "user",
            "parts": [{"text": promptText}]
        }
    ]

def decision_prune_graph_part_level(task, currentInstance):
    """
    INPUTS:
        task: task for planning
        sceneGraphDatabase: SceneGraphDatabase type. Storing the scene graph
        currentInstance: a node in scene graph database. Storing the current kept instances/parts
    """
    parts = []
    # partLevelRelations = []
    partNodes = currentInstance.partNodes
    # partGraph = currentInstance.partGraph
    for partID, partNode in partNodes.items():
        partDescription = f"id: {partID}, type: {partNode.nodeType}, from kept object id: {currentInstance.nodeID}, type: {currentInstance.nodeType}"
        parts.append(partDescription)
    if parts == []:
        partStr = "There is no parts"
    else:
        partStr = {";".join(parts)}
    # for _, _, data in partGraph.edges(data=True):
    #     subject = data.get("subject", "")
    #     object = data.get("object", "")
    #     jointType = data.get("joint_type", "")
    #     controllable = data.get("controllable", "")
    #     root = data.get("root", "")
    #     subjectFunction = data.get("subject_function", "")
    #     objectFunction = data.get("object_function", "")
    #     subjectDesc = data.get("subject_desc", "")
    #     objectDesc = data.get("object_desc", "")
    #     relationDescription = f"subject: {subject}, object: {object}, joint type: {jointType}, controllable: {controllable}, root: {root}, subject function: {subjectFunction}, object function: {objectFunction}, subject description: {subjectDesc}, object description: {objectDesc}"
    #     partLevelRelations.append(relationDescription)
    promptText = f"""
# Robotic Task Planning: Instance Selection

## Task Objective
{task}

## Available Parts

{partStr}

## Scene Graph Context
Only parts of the kept instances and parts are listed in previous sections, and their relations are given

## Your Task
Select ONLY parts essential for completing the task. Consider:
1. Direct relevance to task completion
2. Having relations that affect the task
3. Having unneglegible relations with instances or parts affecting the task
4. Physical access requirements

## Selection Criteria
INCLUDE parts that:
- Are directly manipulated during the task
- Have relations critical to task success
- Serve as containers/platforms for target objects
- Enable access to target components

EXCLUDE parts that:
- Are decorative or non-functional
- Have no relation to the task
- Have no relation to the instances essential to the task
- Are not mentioned or implied in the task description
- Would not be touched during task execution

## Output Format
Return STRICTLY valid JSON with this structure:
{{
  "reasoning": "Concise analysis (1-2 sentences)",
  "selected_ids": ["id 1", "id 2", ...]
}}

## Critical Rules
- Select the MINIMAL necessary set
- Use ONLY instance IDs from the 'Available Parts' section
- DO NOT include any explanatory text outside the JSON
- If no instances are needed, return: {{""reasoning": "", selected_ids": []}}
""".strip()

    return [
        {
            "role": "user",
            "parts": [{"text": promptText}]
        }
    ]
    
    
def recursive_add_item(node) -> dict:   
    """
    INPUTS: 
        node, node
    """
    itemDict = {}
    partList = []
    for keptnode in node.keptSG:
        partList.append(recursive_add_item(node.partNodes[keptnode]))
    if node.owner == "":
        itemDescription = f"id: {node.nodeID}, type: {node.nodeType}, level: instance"
    else:
        itemDescription = f"id: {node.nodeID}, type: {node.nodeType}"
    itemDict["description"] = itemDescription
    itemDict["parts"] = partList
    return itemDict

def task_planning(keptSG, sceneGraphDatabase, task: str):
    """
    INPUTS: 
        keptSG, list of dict
        sceneGraphDatabase: SceneGraphDatabase
        task: str, task
    TODO: add the kinematic relations into consideration. Proposed solution: update the kinematic relations for the previous level in each round
    """
    itemDict = {}
    instanceList = []
    for keptInstance in keptSG:
        instanceList.append(recursive_add_item(sceneGraphDatabase.instanceNodes[keptInstance]))
    itemDict["instances"] = instanceList
    scene_graph_json = json.dumps(itemDict, indent=2)
    promptText = f"""
# Robotic Task Planning: Task Planning

## Task Objective
{task}

## Task Related Environment Scene Graph Tree
```json
{scene_graph_json}
```
## Your Task
Think step-by-step and produce a concise, ordered action plan that the robot can execute to achieve the objective.  
For each step include:
1. High-level action verb (e.g., pick, place, navigate, open, close).
2. Target object(s) or location(s) (use exact names from the environment list).
3. Any pre-conditions or spatial constraints (e.g., “after opening the drawer”, “while holding the cup”).

Format the plan as a numbered list:

1. ...
2. ...
3. ...

End with a short confirmation line: “Plan complete.”
""".strip()

    return [
        {
            "role": "user",
            "parts": [{"text": promptText}]
        }
    ]


def recursive_add_item_replanning(node) -> dict:   
    """
    INPUTS: 
        node, node
    """
    itemDict = {}
    partList = []
    relations = []
    for keptnode in node.keptSG:
        partList.append(recursive_add_item(node.partNodes[keptnode]))
    if node.owner == "":
        itemDescription = f"id: {node.nodeID}, type: {node.nodeType}, level: instance"
    else:
        itemDescription = f"id: {node.nodeID}, type: {node.nodeType}"
    for u, v, data in node.partGraph.edges(data=True):
        joint_type = data.get('joint_type', 'N/A')
        is_controllable = data.get('controllable', False)
        root = data.get('root', '')
        subject_function = data.get('subject_function', [])
        object_function = data.get('object_function', [])
        subject_desc = data.get('subject_desc', '')
        object_desc = data.get('object_desc', '')
        relation = {
            'subject_id': u,
            'object_id': v,
            'joint_type': joint_type,
            'is_controllable': is_controllable,
            'root': root,
            'subject_function': subject_function,
            'object_function': object_function,
            'subject_desc': subject_desc,
            'object_desc': object_desc
        }
        relations.append(relation)

    itemDict["description"] = itemDescription
    itemDict["parts"] = partList
    itemDict["kinematic_relations"] = relations
    return itemDict


def task_replanning(keptSG, sceneGraphDatabase, task: str, currentPlan: str):
    """
    INPUTS: 
        keptSG, list of dict
        sceneGraphDatabase: SceneGraphDatabase
        task: str, task
    TODO: add the kinematic relations into consideration. Proposed solution: update the kinematic relations for the previous level in each round
    """
    itemDict = {}
    instanceList = []
    relations = []
    for keptInstance in keptSG:
        instanceList.append(recursive_add_item_replanning(sceneGraphDatabase.instanceNodes[keptInstance]))
    for u, v, data in sceneGraphDatabase.instancesGraph.edges(data=True):
        subject = data.get("subject", "")
        object = data.get("object", "")
        predicate = data.get("predicate", "")
        relation = {
            "subject": subject,
            "object": object,
            "predicate": predicate
        }
        relations.append(relation)
    itemDict["instances"] = instanceList
    itemDict["relations"] = relations
    scene_graph_json = json.dumps(itemDict, indent=2)
    promptText = f"""
# Robotic Task Planning: Refine Task Planning

## Task Objective
{task}

## Current Plan
{currentPlan}

## Task Related Environment Scene Graph Tree With Kinematic Relations
```json
{scene_graph_json}
```
## Your Task
Think step-by-step and produce a concise, ordered action plan that the robot can execute to achieve the objective.  
For each step include:
1. Action verb, showing how to manipulate the parts/objects kinematically (e.g., horizontally rotate).
2. Target object(s) or location(s) (use exact names from the environment list).
3. Any pre-conditions or spatial constraints (e.g., “after opening the drawer”, “while holding the cup”).

Format the plan as a numbered list:

1. ...
2. ...
3. ...

End with a short confirmation line: “Plan complete.”
""".strip()

    return [
        {
            "role": "user",
            "parts": [{"text": promptText}]
        }
    ]
