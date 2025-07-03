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
        """Generate flowing terrain with solid border and advanced cleanup, favoring continuous open space"""
        cfg = get_config()
        flow_field = AdvancedFlowField(self.width, self.height)
        flow_field.generate_base_terrain(complexity * 0.7)
        flow_field.create_flowing_channels_smooth(complexity)
        flow_field.apply_border_fade(cfg.terrain.BORDER_FADE_DISTANCE)
        flow_field.add_solid_border(cfg.terrain.SOLID_BORDER_WIDTH)
        flow_field.apply_erosion(cfg.terrain.EROSION_ITERATIONS)
        flow_field.smooth_terrain_advanced(cfg.terrain.SMOOTHING_ITERATIONS, cfg.terrain.SMOOTHING_STRENGTH)
        flow_field.apply_dilation(1)
        flow_field.remove_small_terrain_pieces(cfg.terrain.MIN_TERRAIN_REGION_SIZE)
        flow_field.smooth_terrain_advanced(2, 0.3)
        # --- New: Promote continuous open space and remove isolated pockets ---
        flow_field.promote_continuous_spaces()
        flow_field.ensure_connectivity()
        flow_field.remove_isolated_pockets(min_pocket_size=cfg.terrain.MIN_TERRAIN_REGION_SIZE)
        # Add scattered terrain islands in large open areas
        flow_field.add_scattered_terrain_islands(num_islands=rng.randint(2, 5))
        # --- End new ---
        scale_x = self.width / flow_field.grid_width
        scale_y = self.height / flow_field.grid_height
        threshold = 0.25 + complexity * 0.35
        self.terrain_obstacle = FlowingTerrainObstacle(
            flow_field.height_field,
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
