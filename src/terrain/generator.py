"""
Main terrain generator orchestrating the terrain creation process.
"""

from typing import List, Tuple
import rng
from config import get_config
from .height_field import AdvancedFlowField
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
        """Generate a random base color for terrain using the RNG system"""
        # Generate random hue (0-360 degrees)
        hue = rng.uniform(0, 360)
        
        # Use moderate saturation and value for natural terrain colors
        saturation = rng.uniform(0.4, 0.8)  # Not too gray, not too vibrant
        value = rng.uniform(0.3, 0.7)       # Not too dark, not too bright
        
        # Convert HSV to RGB
        c = value * saturation
        x = c * (1 - abs((hue / 60) % 2 - 1))
        m = value - c
        
        if 0 <= hue < 60:
            r, g, b = c, x, 0
        elif 60 <= hue < 120:
            r, g, b = x, c, 0
        elif 120 <= hue < 180:
            r, g, b = 0, c, x
        elif 180 <= hue < 240:
            r, g, b = 0, x, c
        elif 240 <= hue < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        # Convert to 0-255 range
        red = max(0, min(255, int((r + m) * 255)))
        green = max(0, min(255, int((g + m) * 255)))
        blue = max(0, min(255, int((b + m) * 255)))
        
        return (red, green, blue)
    
    def generate_terrain(self, complexity: float = 0.5) -> List:
        """Generate only background and solid borders (no terrain obstacles)."""
        cfg = get_config()
        # Create a height field with all open space (0.0), only borders are solid (1.0)
        grid_width = self.width // 8
        grid_height = self.height // 8
        height_field = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
        border_width_x = max(1, cfg.terrain.SOLID_BORDER_WIDTH // (self.width // grid_width))
        border_width_y = max(1, cfg.terrain.SOLID_BORDER_WIDTH // (self.height // grid_height))
        # Top and bottom borders
        for y in range(min(border_width_y, grid_height)):
            for x in range(grid_width):
                height_field[y][x] = 1.0
                height_field[grid_height - 1 - y][x] = 1.0
        # Left and right borders
        for x in range(min(border_width_x, grid_width)):
            for y in range(grid_height):
                height_field[y][x] = 1.0
                height_field[y][grid_width - 1 - x] = 1.0
        scale_x = self.width / grid_width
        scale_y = self.height / grid_height
        threshold = 0.5  # Only borders are solid
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
