"""
Base classes and enums for game modes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Tuple
from enum import Enum
import math
import rng


class GameResult(Enum):
    """Possible game results"""
    ONGOING = "ongoing"
    WINNER = "winner"
    DRAW = "draw"
    ERROR = "error"


class Zone:
    """Represents a zone on the terrain (spawn, goal, etc.)"""
    
    def __init__(self, center_x: float, center_y: float, radius: float, zone_type: str):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.zone_type = zone_type  # "spawn", "goal", etc.
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this zone"""
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance <= self.radius
    
    def get_random_position_in_zone(self) -> Tuple[float, float]:
        """Get a random position within this zone"""
        # Generate random point in circle
        angle = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(0, self.radius * 0.9)  # Stay slightly inside the zone
        
        x = self.center_x + radius * math.cos(angle)
        y = self.center_y + radius * math.sin(angle)
        
        return x, y
