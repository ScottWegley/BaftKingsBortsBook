"""
Main terrain generator orchestrating the terrain creation process.
"""

from typing import List, Tuple
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import rng
from config import get_config
from .cave_generator import CaveTerrainGenerator
from .obstacle import FlowingTerrainObstacle


class FlowingTerrainGenerator:
    """Generates flowing, organic terrain like in the reference image"""
    
    def __init__(self, width: int, height: int, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed
        self.terrain_obstacle = None
        
        # Generate random base color for terrain using RNG system
        self.base_color = self._generate_terrain_color()
    
    def _generate_terrain_color(self) -> Tuple[int, int, int]:
        """Generate a natural terrain color (browns, tans, earth tones)"""
        # Generate earth tone colors similar to reference images
        color_type = rng.randint(0, 2)
        
        if color_type == 0:
            # Brown terrain (like reference images)
            red = rng.randint(120, 160)
            green = rng.randint(80, 120)
            blue = rng.randint(60, 100)
        elif color_type == 1:
            # Tan/beige terrain
            red = rng.randint(150, 200)
            green = rng.randint(140, 180)
            blue = rng.randint(100, 140)
        else:
            # Gray terrain
            gray_value = rng.randint(100, 140)
            red = gray_value
            green = gray_value
            blue = gray_value
        
        return (red, green, blue)
    
    def generate_terrain(self, complexity: float = 0.5) -> List:
        """Generate flowing terrain with configurable complexity."""
        cfg = get_config()
        
        # Use runtime complexity if available, otherwise use parameter
        final_complexity = cfg.simulation.TERRAIN_COMPLEXITY if hasattr(cfg.simulation, 'TERRAIN_COMPLEXITY') else complexity
        
        # Create cave terrain generator
        cave_generator = CaveTerrainGenerator(self.width, self.height, final_complexity)
        
        # Generate height field
        height_field = cave_generator.generate()
        
        # Create terrain obstacle from height field
        scale_x = cfg.terrain.TERRAIN_GRID_SCALE
        scale_y = cfg.terrain.TERRAIN_GRID_SCALE
        threshold = 0.2  # Lower threshold - more things become terrain (inverted logic)
        
        self.terrain_obstacle = FlowingTerrainObstacle(
            height_field,
            threshold,
            scale_x,
            scale_y,
            self.base_color
        )
        
        return [self.terrain_obstacle] if self.terrain_obstacle else []
    
    def get_obstacles(self) -> List:
        """Get terrain obstacles"""
        return [self.terrain_obstacle] if self.terrain_obstacle else []
    
    def render_terrain(self, screen):
        """Render the flowing terrain"""
        if self.terrain_obstacle:
            self.terrain_obstacle.render(screen, self.base_color)
