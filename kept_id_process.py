import ast
import os
import shutil

jsonStr = "[{'mask0.png': {'parts': [{'mask0/mask2.png': {'parts': []}}, {'mask0/mask0.png': {'parts': []}}, {'mask0/mask1.png': {'parts': []}}]}}]"
idPath= "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset/id 6"
outputPath = "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset_for_kaf/id 6"

def recursive_post_processing(data, level: int, idPath: str, instanceLevel: dict):
    """
    Recursively traverses the data structure to populate the instanceLevel dictionary.

    Args:
        data: The current node (dict) or list of nodes to process.
        level: The current depth in the tree.
        idPath: The base directory path for constructing full paths.
        instanceLevel: The dictionary to populate with level-organized paths.
    """
    # If the current data is a list, iterate through its items.
    if isinstance(data, list):
        for item in data:
            recursive_post_processing(item, level, idPath, instanceLevel)
            
    # If the current data is a dictionary, it's a node with a mask path.
    elif isinstance(data, dict):
        # Each dictionary represents a node with a single key (the relative path).
        for relativePath, details in data.items():
            # Create a platform-independent full path and ensure forward slashes.
            fullPath = os.path.join(idPath, relativePath).replace("\\", "/")
            
            # Add the full path to the list for the current level.
            # setdefault() conveniently initializes the list if the key doesn't exist yet.
            instanceLevel.setdefault(level, []).append(fullPath)
            
            # If there are 'parts' (children), recurse into them at the next level.
            children = details.get('parts', [])
            if children:
                recursive_post_processing(children, level + 1, idPath, instanceLevel)


def post_processing(jsonStr: str, idPath: str):
    instanceLevel = {} # dict of list, key = integer starting from 0, value is the list storing the paths of level {x}
    currentLevel = 0
    jsonData = ast.literal_eval(jsonStr)
    recursive_post_processing(jsonData, currentLevel, idPath, instanceLevel)
    print(instanceLevel)
    src_img_path = os.path.join(idPath, "src_img.png")

    # Check if the main source image exists to avoid errors
    if not os.path.exists(src_img_path):
        print(f"Warning: Common source image not found at '{src_img_path}'.")
        return # Exit if the main image is missing

    # --- File Copying Logic ---
    # Iterate through the dictionary of levels and their corresponding image paths
    for level, paths in instanceLevel.items():
        # Define the target directory path for the current level (e.g., ".../id 6/level_0")
        level_output_dir = os.path.join(outputPath, f"level_{level}")
        
        # Create the directory, including any parent directories.
        # exist_ok=True prevents an error if the directory already exists.
        os.makedirs(level_output_dir, exist_ok=True)
        print(f"Created directory: {level_output_dir}")
        
        # Copy all the mask images for the current level
        for mask_path in paths:
            if os.path.exists(mask_path):
                shutil.copy(mask_path, level_output_dir)
            else:
                print(f"  - Warning: Mask not found, skipping: {mask_path}")
        
        # Copy the common source image into the current level's directory
        shutil.copy(src_img_path, level_output_dir)
        print(f"  - Copied {len(paths)} mask(s) and src_img.png to level_{level}")

        
        
        
post_processing(jsonStr, idPath)