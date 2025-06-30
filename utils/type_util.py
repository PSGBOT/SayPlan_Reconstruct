from typing import List, Optional

class PLSGNode:
    def __init__(self, nodeType: str, parts: Optional[List['PLSGNode']] = None):
        self.nodeType = nodeType
        self.parts = parts or []

    @staticmethod
    def from_dict(data: dict) -> 'PLSGNode':
        nodeType = data.get("nodeType", "")
        partsData = data.get("node", [])
        parts = [PLSGNode.from_dict(part) for part in partsData]
        return PLSGNode(nodeType, parts)

class PLSGTree:
    def __init__(self, node: PLSGNode):
        self.node = node

    @staticmethod
    def from_dict(data: dict) -> 'PLSGTree':
        root_node = PLSGNode.from_dict(data.get("node", {}))
        return PLSGTree(root_node)
