import ast
import os
import shutil

jsonStr = "[{'mask0.png': {'parts': [{'mask0/mask2.png': {'parts': []}}, {'mask0/mask0.png': {'parts': []}}, {'mask0/mask1.png': {'parts': []}}]}}]"
idPath = "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset/id 6"
outputPath = "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset_for_kaf/id 6"

def collect_directories_with_parts(data, idPath: str, parentPath: str = ""):
    """
    Recursively traverses the data structure to find directories that have parts (children).
    
    Args:
        data: The current node (dict) or list of nodes to process.
        idPath: The base directory path for source files.
        parentPath: The current path prefix for building full paths.
    
    Returns:
        dict: Dictionary where keys are directory paths and values are lists of mask files in that directory.
    """
    directories_to_keep = {}
    
    # If the current data is a list, iterate through its items.
    if isinstance(data, list):
        for item in data:
            child_dirs = collect_directories_with_parts(item, idPath, parentPath)
            directories_to_keep.update(child_dirs)
            
    # If the current data is a dictionary, it's a node with a mask path.
    elif isinstance(data, dict):
        # Each dictionary represents a node with a single key (the relative path).
        for relativePath, details in data.items():
            # Get the directory path (remove the filename to get the directory)
            if "/" in relativePath:
                currentDirPath = os.path.dirname(relativePath)
                maskFileName = os.path.basename(relativePath)
            else:
                currentDirPath = ""  # Root level
                maskFileName = relativePath
            
            # Build the full directory path
            if parentPath:
                fullDirPath = os.path.join(parentPath, currentDirPath).replace("\\", "/") if currentDirPath else parentPath
            else:
                fullDirPath = currentDirPath if currentDirPath else ""
            
            # Check if this node has parts (children)
            children = details.get('parts', [])
            if children:
                # This directory should be kept because it has children
                # Collect all mask files at this level
                if fullDirPath not in directories_to_keep:
                    directories_to_keep[fullDirPath] = []
                
                # Add current mask to the directory
                directories_to_keep[fullDirPath].append(relativePath)
                
                # Add all sibling masks (other children at the same level)
                for child in children:
                    if isinstance(child, dict):
                        for childPath, _ in child.items():
                            if childPath not in directories_to_keep[fullDirPath]:
                                directories_to_keep[fullDirPath].append(childPath)
                
                # Recursively process children
                child_dirs = collect_directories_with_parts(children, idPath, 
                                                          relativePath if not parentPath else os.path.join(parentPath, relativePath).replace("\\", "/"))
                directories_to_keep.update(child_dirs)
    
    return directories_to_keep

def post_processing(jsonStr: str, idPath: str, outputPath: str):
    """
    Main processing function that creates directories only for nodes with parts.
    
    Args:
        jsonStr: JSON string containing the hierarchical structure.
        idPath: Source directory path.
        outputPath: Root output directory path.
    """
    # Parse the JSON string
    jsonData = ast.literal_eval(jsonStr)
    
    # Create the root output directory
    os.makedirs(outputPath, exist_ok=True)
    print(f"Root output directory: {outputPath}")
    
    # Check if the main source image exists
    src_img_path = os.path.join(idPath, "src_img.png")
    if not os.path.exists(src_img_path):
        print(f"Warning: Common source image not found at '{src_img_path}'.")
        return
    
    # Collect directories that should be kept (those with parts)
    directories_to_keep = collect_directories_with_parts(jsonData, idPath)
    
    print(f"Directories to keep: {list(directories_to_keep.keys())}")
    
    # Create directories and copy files
    for dirPath, maskFiles in directories_to_keep.items():
        # Create directory name for output
        if dirPath == "":
            # Root level directory
            dirName = "root"  # or you could use the first mask name without extension
        else:
            dirName = dirPath.replace("/", "_")
        
        # Create the output directory
        outputDir = os.path.join(outputPath, dirName)
        os.makedirs(outputDir, exist_ok=True)
        print(f"Created directory: {outputDir}")
        
        # Copy src_img.png to this directory
        shutil.copy(src_img_path, outputDir)
        print(f"  - Copied src_img.png")
        
        # Copy all mask files for this directory level
        for maskFile in maskFiles:
            sourceMaskPath = os.path.join(idPath, maskFile).replace("\\", "/")
            if os.path.exists(sourceMaskPath):
                shutil.copy(sourceMaskPath, outputDir)
                print(f"  - Copied mask: {maskFile}")
            else:
                print(f"  - Warning: Mask not found: {sourceMaskPath}")
    
    print("Processing completed!")

# Improved version with better logic for collecting masks at each level
def collect_directories_with_parts_improved(data, idPath: str):
    """
    Improved version that correctly identifies directories with parts and collects all masks at each level.
    """
    directories_to_keep = {}
    
    def traverse(node_data, current_path_parts=[]):
        if isinstance(node_data, list):
            for item in node_data:
                traverse(item, current_path_parts)
        elif isinstance(node_data, dict):
            for relativePath, details in node_data.items():
                children = details.get('parts', [])
                
                if children:
                    # This node has children, so its directory should be kept
                    # The directory path is everything except the filename
                    path_parts = relativePath.split('/')
                    if len(path_parts) > 1:
                        dir_path = '/'.join(path_parts[:-1])
                    else:
                        dir_path = ""  # Root level
                    
                    # Add this directory to keep
                    if dir_path not in directories_to_keep:
                        directories_to_keep[dir_path] = set()
                    
                    # Add the current mask
                    directories_to_keep[dir_path].add(relativePath)
                    
                    # Add all sibling masks (all children at this level)
                    for child in children:
                        if isinstance(child, dict):
                            for child_path, _ in child.items():
                                directories_to_keep[dir_path].add(child_path)
                    
                    # Continue traversing children
                    traverse(children, current_path_parts + [relativePath])
    
    traverse(data)
    
    # Convert sets to lists for easier handling
    return {k: list(v) for k, v in directories_to_keep.items()}

def post_processing_improved(jsonStr: str, idPath: str, outputPath: str):
    """
    Improved main processing function.
    """
    jsonData = ast.literal_eval(jsonStr)
    os.makedirs(outputPath, exist_ok=True)
    print(f"Root output directory: {outputPath}")
    
    src_img_path = os.path.join(idPath, "src_img.png")
    if not os.path.exists(src_img_path):
        print(f"Warning: Common source image not found at '{src_img_path}'.")
        return
    
    directories_to_keep = collect_directories_with_parts_improved(jsonData, idPath)
    print(f"Directories to keep: {directories_to_keep}")
    
    for dirPath, maskFiles in directories_to_keep.items():
        # Create directory name
        if dirPath == "":
            dirName = "mask0"  # Root level gets the base name
        else:
            dirName = dirPath.replace("/", "_")
        
        outputDir = os.path.join(outputPath, dirName)
        os.makedirs(outputDir, exist_ok=True)
        print(f"Created directory: {outputDir}")
        
        # Copy src_img.png
        shutil.copy(src_img_path, outputDir)
        print(f"  - Copied src_img.png")
        
        # Copy all masks for this level
        for maskFile in maskFiles:
            sourceMaskPath = os.path.join(idPath, maskFile).replace("\\", "/")
            if os.path.exists(sourceMaskPath):
                # Just copy the filename, not the full path structure
                shutil.copy(sourceMaskPath, outputDir)
                print(f"  - Copied mask: {os.path.basename(maskFile)}")
            else:
                print(f"  - Warning: Mask not found: {sourceMaskPath}")

# Example usage:
print("=== Processing with improved logic ===")
post_processing_improved(jsonStr, idPath, outputPath)