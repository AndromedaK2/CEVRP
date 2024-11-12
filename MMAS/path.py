from dataclasses import dataclass, field
from typing import List

@dataclass
class Path:
    nodes: List[str] = field(default_factory=list)
    path_cost: float = 0.0
