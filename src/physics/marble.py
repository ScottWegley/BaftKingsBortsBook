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
    
    def update(self, dt: float, arena_width: int, arena_height: int):
        """Update marble position and handle boundary collisions"""
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Boundary collisions with small tolerance to prevent wall sliding
        tolerance = 0.1
        
        # Left boundary
        if self.x - self.radius < tolerance:
            self.x = self.radius + tolerance
            if self.velocity_x < 0:  # Only reflect if moving toward wall
                self.velocity_x = -self.velocity_x
        
        # Right boundary
        elif self.x + self.radius > arena_width - tolerance:
            self.x = arena_width - self.radius - tolerance
            if self.velocity_x > 0:  # Only reflect if moving toward wall
                self.velocity_x = -self.velocity_x
        
        # Top boundary
        if self.y - self.radius < tolerance:
            self.y = self.radius + tolerance
            if self.velocity_y < 0:  # Only reflect if moving toward wall
                self.velocity_y = -self.velocity_y
        
        # Bottom boundary
        elif self.y + self.radius > arena_height - tolerance:
            self.y = arena_height - self.radius - tolerance
            if self.velocity_y > 0:  # Only reflect if moving toward wall
                self.velocity_y = -self.velocity_y
    
    def _normalize_velocity(self):
        """Ensure velocity magnitude equals the desired speed"""
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > 0:
            self.velocity_x = (self.velocity_x / current_speed) * self.speed
            self.velocity_y = (self.velocity_y / current_speed) * self.speed
