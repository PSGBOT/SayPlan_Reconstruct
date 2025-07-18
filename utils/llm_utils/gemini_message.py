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

def decision_prune_graph_part_level(task, currentInstanceDict):
    """
    INPUTS:
        task: task for planning
        sceneGraphDatabase: SceneGraphDatabase type. Storing the scene graph
        currentInstanceDict: a dict. Key: instance id; Value: pointer to its node in scene graph database. Storing the current kept instances/parts
    """
    parts = []
    partLevelRelations = []
    for instanceID, node in currentInstanceDict.items():
        partNodes = node.partNodes
        partGraph = node.partGraph
        for partID, partNode in partNodes.items():
            partDescription = f"id: {partID}, type: {partNode.type}, from kept object id: {instanceID}, type: {node.type}"
            parts.append(partDescription)
        for _, _, data in partGraph.edges(data=True):
            subject = data.get("subject", "")
            object = data.get("object", "")
            jointType = data.get("joint_type", "")
            controllable = data.get("controllable", "")
            root = data.get("root", "")
            subjectFunction = data.get("subject_function", "")
            objectFunction = data.get("object_function", "")
            subjectDesc = data.get("subject_desc", "")
            objectDesc = data.get("object_desc", "")
            relationDescription = f"subject: {subject}, object: {object}, joint type: {jointType}, controllable: {controllable}, root: {root}, subject function: {subjectFunction}, object function: {objectFunction}, subject description: {subjectDesc}, object description: {objectDesc}"
            partLevelRelations.append(relationDescription)
    promptText = f"""
# Robotic Task Planning: Instance Selection

## Task Objective
{task}

## Available Parts

{";".join(parts)}

## Kinematic Relationships among the Parts

{";".join(partLevelRelations)}

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
    
    
def task_planning(keptSG, sceneGraphDatabase, task: str):
    """
    INPUTS: 
        keptSG, list of dict
        sceneGraphDatabase: SceneGraphDatabase
        task: str, task
    FIXME: add the kinematic relations into consideration. Proposed solution: update the kinematic relations for the previous level in each round
    """
    itemLists = []
    for levelDict in keptSG:
        itemList = []
        for itemID, itemNode in levelDict.items():
            if itemNode.owner == "":
                itemDescription = f"id: {itemID}, type: {itemNode.type}, level: instance"
            else:
                itemDescription = f"id: {itemID}, type: {itemNode.type}, is part of: {itemNode.owner}"
            itemList.append(itemDescription)
        itemLists.append(itemList)
    promptText = f"""
# Robotic Task Planning: Instance Selection

## Task Objective
{task}

## Task Related Environment

{('\n'.join(';'.join(itemList) for itemList in itemLists))}

## Your Task
Think step-by-step and produce a concise, ordered action plan that the robot can execute to achieve the objective.  
For each step include:
1. Action verb (e.g., pick, place, navigate, open, close).
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
    