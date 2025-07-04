"""
Main terrain generator orchestrating the terrain creation process.
"""

from typing import List, Tuple

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
        """Generate a truly random color for the terrain (any RGB value)."""
        return (
            rng.randint(0, 255),
            rng.randint(0, 255),
            rng.randint(0, 255)
        )
    
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
