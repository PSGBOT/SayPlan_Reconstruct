# SayPlan Reconstruction & Improvements

## Acknowledgement

@inproceedings{
        rana2023sayplan,
        title={SayPlan: Grounding Large Language Models using 3D Scene Graphs for Scalable Task Planning},
        author={Krishan Rana and Jesse Haviland and Sourav Garg and Jad Abou-Chakra and Ian Reid and Niko Suenderhauf},
        booktitle={7th Annual Conference on Robot Learning},
        year={2023},
        url={https://openreview.net/forum?id=wMpOMO0Ss7a}
      }

## Pipeline Structure 

The SayPlan pipeline is implemented in `pipeline.py` and provides a framework for task planning using scene graphs and large language models (LLMs). The pipeline consists of several key components:

### Main Components

1. **Pipeline Class** (`pipeline.py`):
   - Loads scene graph from JSON files
   - Prunes the environment graph to focus on task-relevant elements
   - Generates task plans using LLMs
   - Handles re-planning with kinematic relations

2. **Scene Graph Database** (`utils/sg_utils.py`):
   - `SceneGraphDatabase` class manages the scene graph structure
   - `Node` class represents both instances and parts in the scene graph
   - Supports recursive construction of object-part trees
   - Handles kinematic relationships between parts

3. **LLM Integration** (`utils/llm_utils/`):
   - `GeminiVLMClient` class for interacting with Gemini AI models
   - Prompt generation functions for various planning stages
   - Support for both instance-level and part-level pruning

### Pipeline Workflow

The pipeline follows this sequence:

1. **Initialization**: Load scene graph from JSON and initialize the database
2. **Graph Pruning**: 
   - Instance-level pruning to select relevant objects
   - Recursive part-level pruning to focus on necessary components
3. **Task Planning**: Generate initial action plan using LLM
4. **Re-planning**: Refine plan with kinematic relations added

### Key Methods

- `prune_graph()`: Uses LLM to recursively prune the environment graph, keeping only elements relevant to the task
- `recursive_prune_node()`: Helper function for recursive pruning at part levels
- `plan()`: Generates the initial task plan based on pruned graph
- `replan()`: Refines the plan with kinematic relationships
- `run()`: Executes the full pipeline from pruning to re-planning

### Usage

The pipeline can be executed from the command line:

```bash
python pipeline.py --sgPath <scene_graph_json> --sgKinematicPath <kinematic_relations_json> --task "task description"
```

### Dependencies

- `networkx`: For graph operations
- `google-genai`: For Gemini AI API access
- JSON scene graph files with proper structure

### File Structure

- `pipeline.py`: Main pipeline implementation
- `utils/sg_utils.py`: Scene graph utilities and database management
- `utils/llm_utils/llm_service.py`: LLM client implementations
- `utils/llm_utils/gemini_message.py`: Prompt generation functions for LLM interactions
- `config/`: Configuration files for model settings

This implementation reconstructs the SayPlan approach for scalable task planning using 3D scene graphs grounded with large language models.
