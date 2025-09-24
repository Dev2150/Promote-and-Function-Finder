from dataclasses import dataclass

@dataclass
class Node:
    id: int
    name: str
    color: str = "#000000"