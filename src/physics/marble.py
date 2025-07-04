"""
Marble physics object for the marble race simulation.
"""

import math
from typing import List, Tuple
import rng
from config import get_config


class Marble:
    """Physics object representing a marble with position, velocity, and collision behavior"""
    
    def __init__(self, x: float, y: float, radius: float, color: Tuple[int, int, int], speed: float, initial_angle: float = None):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
        
        # Use provided angle or generate random direction
        if initial_angle is not None:
            angle = initial_angle
        else:
            angle = rng.uniform(0, 2 * math.pi)
            
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
    
    def update(self, dt: float):
        """Update marble position - collision handling is done separately"""
        # Update position based on current velocity
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
