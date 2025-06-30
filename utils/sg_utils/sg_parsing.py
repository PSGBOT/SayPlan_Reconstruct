import os
import json

from utils.type_util import *

def build_sg_dataset(sgDir: str) -> list[PLSGTree]:
    """ Inputs:
            sgDir: string, the directory storing the part-level scene graph
        Output: 
            sgTree: a dictionary that stores self-defined tree that stores the scene-graphs
        Effects: 
            Read and store all the scene graphs in the sgDir folder and its children folders to  
    """
    sg_trees = []
    
    for root, _, files in os.walk(sgDir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        sg_tree = PLSGTree(data)
                        sg_trees.append(sg_tree)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_path}: {e}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
    
    return sg_trees
    