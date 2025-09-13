import ast
import os
import shutil
import json

jsonStr = "[{'mask0.png': {'parts': [{'mask0/mask2.png': {'parts': []}}, {'mask0/mask0.png': {'parts': []}}, {'mask0/mask1.png': {'parts': []}}]}}]"
idPath = "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset/id 6"
outputPath = "C:/PartLevelProject/scene_part_seg_dataset/sample_part_seg_dataset_for_kaf/id 6"

def collect_directories_with_parts(data):
    """
    Traverses the data structure to find all directories that should be created.
    Each directory contains the masks at that level.
    
    Args:
        data: The parsed JSON data structure.
    
    Returns:
        dict: Dictionary where keys are directory paths and values are lists of mask files.
    """
    directories_to_keep = {}
    
    def traverse(node_data, current_path=""):
        if isinstance(node_data, list):
            for item in node_data:
                traverse(item, current_path)
        elif isinstance(node_data, dict):
            # Collect all masks at current level
            current_level_masks = []
            
            for mask_path, details in node_data.items():
                children = details.get('parts', [])
                current_level_masks.append(mask_path)
                
                # If this mask has children, we need to process them
                if children:
                    # Determine the directory path for the children
                    if current_path == "":
                        # Root level mask with children
                        child_dir = mask_path.replace('.png', '')
                    else:
                        # Subdirectory mask with children - build full path
                        child_dir = current_path + "/" + mask_path.replace('.png', '')
                    
                    # Traverse children at the new directory level
                    traverse(children, child_dir)
            
            # Add current level masks to the directory
            if current_level_masks:
                if current_path not in directories_to_keep:
                    directories_to_keep[current_path] = []
                directories_to_keep[current_path].extend(current_level_masks)
    
    traverse(data)
    
    # Remove duplicates and sort
    for key in directories_to_keep:
        directories_to_keep[key] = list(set(directories_to_keep[key]))
    
    return directories_to_keep

def post_processing(jsonStr: str, idPath: str, maskPath: str, outputPath: str):
    """
    Main processing function that creates directories only for nodes with parts.
    
    Args:
        jsonStr: JSON string containing the hierarchical structure.
        idPath: Source directory path.
        outputPath: Root output directory path.
    """
    # Parse the JSON string
    jsonData = ast.literal_eval(jsonStr)
    
    # Extract scene ID from idPath (last part of the path)
    scene_id = os.path.basename(idPath.rstrip('/\\'))
    
    # Create the root output directory
    os.makedirs(outputPath, exist_ok=True)
    print(f"Root output directory: {outputPath}")
    
    # Check if the main source image exists
    src_img_path = os.path.join(idPath, "original.jpg")
    if not os.path.exists(src_img_path):
        print(f"Warning: Source image not found at '{src_img_path}'.")
        return
    
    # Collect directories that should be kept
    directories_to_keep = collect_directories_with_parts(jsonData)
    print(f"Directories to keep: {directories_to_keep}")
    
    # Create directories and copy files
    for dirPath, maskFiles in directories_to_keep.items():
        # Create directory name
        if dirPath == "":
            # Root level - use scene ID as directory name
            dirName = scene_id
        else:
            # Subdirectory - use path with underscores
            dirName = dirPath.replace("/", "_")
        
        # Create the output directory
        outputDir = os.path.join(outputPath, dirName)
        os.makedirs(outputDir, exist_ok=True)
        print(f"Created directory: {outputDir}")
        
        # Copy src_img.png to this directory
        dest_filename = "src_img.jpg"
        
        # 2. Construct the full destination path including the new filename
        dest_img_path = os.path.join(outputDir, dest_filename)
        
        # 3. Copy the source file to the new destination path, which renames it
        shutil.copy(src_img_path, dest_img_path)
        
        # 4. Update the print statement for clarity
        print(f"  - Copied '{os.path.basename(src_img_path)}' and renamed to '{dest_filename}'")
        
        
        # Copy mask files for this directory level
        for maskFile in maskFiles:
            sourceMaskPath = os.path.join(maskPath, maskFile)
            if os.path.exists(sourceMaskPath):
                shutil.copy(sourceMaskPath, outputDir)
                print(f"  - Copied mask: {os.path.basename(maskFile)}")
            else:
                print(f"  - Warning: Mask not found: {sourceMaskPath}")
    
    print("Processing completed!")

    
# Example usage:
# print("=== Processing with improved logic ===")
# post_processing_improved(jsonStr, idPath, outputPath)