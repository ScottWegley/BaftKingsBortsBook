"""
Terrain carving operations for creating paths and chambers.
"""

import math

from typing import List, Tuple, Union
import numpy as np
import rng
from config import get_config
from .noise import NoiseGenerator


class TerrainCarver:
    """Handles carving operations on terrain height fields"""
    
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cfg = get_config().terrain
    
    def carve_flow_channels(self, height_field: np.ndarray, complexity: float):
        """Create major flow channels through the terrain"""
        if complexity < 0.2:
            return
        
        num_channels = max(1, int(self.cfg.FLOW_CHANNEL_COUNT * complexity))
        
        for _ in range(num_channels):
            start_side = rng.choice(['top', 'bottom', 'left', 'right'])
            end_side = rng.choice(['top', 'bottom', 'left', 'right'])
            
            # Avoid same-side channels
            while end_side == start_side:
                end_side = rng.choice(['top', 'bottom', 'left', 'right'])
            
            start_x, start_y = self._get_border_point(start_side)
            end_x, end_y = self._get_border_point(end_side)
            
            channel_width = rng.uniform(self.cfg.FLOW_CHANNEL_WIDTH_MIN, 
                                       self.cfg.FLOW_CHANNEL_WIDTH_MAX)
            
            self._carve_curved_path(height_field, start_x, start_y, end_x, end_y, channel_width)
    
    def carve_interior_chambers(self, height_field: np.ndarray, complexity: float):
        """Create interior chambers with better connectivity"""
        num_chambers = int(self.cfg.INTERIOR_OBSTACLE_DENSITY * complexity * 
                          self.grid_width * self.grid_height * 0.03)  # Fewer, larger chambers
        
        for _ in range(num_chambers):
            # Position away from borders
            border_margin = max(6, self.grid_width // 12)
            x = rng.randint(border_margin, self.grid_width - border_margin)
            y = rng.randint(border_margin, self.grid_height - border_margin)
            
            # Larger chamber sizes
            size = rng.randint(self.cfg.MIN_OBSTACLE_SIZE + 2, self.cfg.MAX_OBSTACLE_SIZE + 3)
            
            # Create mostly circular chambers for better flow
            if rng.random_float() < 0.9:
                self._carve_circular_area(height_field, x, y, size / 1.8)  # Slightly larger
            else:
                self._carve_elongated_area(height_field, x, y, size)
    
    def create_solid_borders(self, height_field: np.ndarray):
        """Create solid borders around the terrain"""
        border_width = max(2, self.cfg.SOLID_BORDER_WIDTH // self.cfg.TERRAIN_GRID_SCALE)
        
        # Top and bottom borders
        for y in range(min(border_width, self.grid_height)):
            for x in range(self.grid_width):
                height_field[y][x] = 1.0
                if self.grid_height - 1 - y >= 0:
                    height_field[self.grid_height - 1 - y][x] = 1.0
        
        # Left and right borders
        for x in range(min(border_width, self.grid_width)):
            for y in range(self.grid_height):
                height_field[y][x] = 1.0
                if self.grid_width - 1 - x >= 0:
                    height_field[y][self.grid_width - 1 - x] = 1.0
    
    def _get_border_point(self, side: str) -> Tuple[int, int]:
        """Get a random point on a border side"""
        margin = 5
        
        if side == 'top':
            return (rng.randint(margin, self.grid_width - margin), 0)
        elif side == 'bottom':
            return (rng.randint(margin, self.grid_width - margin), self.grid_height - 1)
        elif side == 'left':
            return (0, rng.randint(margin, self.grid_height - margin))
        else:  # right
            return (self.grid_width - 1, rng.randint(margin, self.grid_height - margin))
    
    def _carve_curved_path(self, height_field: np.ndarray, 
                          start_x: int, start_y: int, end_x: int, end_y: int, width: float):
        """Carve a gently curved path between two points"""
        # Simple curved path with one control point
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Add gentle curvature
        curve_strength = min(abs(end_x - start_x), abs(end_y - start_y)) * 0.2  # Reduced
        offset_x = rng.uniform(-curve_strength, curve_strength)
        offset_y = rng.uniform(-curve_strength, curve_strength)
        
        control_x = mid_x + offset_x
        control_y = mid_y + offset_y
        
        # Sample points along the curve
        distance = max(abs(end_x - start_x), abs(end_y - start_y))
        num_points = max(20, int(distance * 1.5))
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Quadratic Bezier curve
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
            
            # Simple circular carving without width variation
            self._carve_circular_area(height_field, x, y, width / 2)
    
    def _carve_circular_area(self, height_field: np.ndarray, 
                            center_x: float, center_y: float, radius: float):
        """Carve out a circular area with smooth edges"""
        radius_int = int(radius)
        center_x_int = int(center_x)
        center_y_int = int(center_y)
        
        for dy in range(-radius_int - 2, radius_int + 3):
            for dx in range(-radius_int - 2, radius_int + 3):
                x = center_x_int + dx
                y = center_y_int + dy
                
                if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius:
                        height_field[y][x] = 0.0  # Clear path
                    elif distance <= radius + 1:
                        # Smooth edge transition
                        height_field[y][x] = min(height_field[y][x], 0.3)
    
    def _carve_elongated_area(self, height_field: np.ndarray, 
                             center_x: int, center_y: int, size: int):
        """Carve an elongated chamber"""
        angle = rng.uniform(0, 2 * math.pi)
        length = size * 2
        
        for i in range(length):
            t = i / max(1, length - 1)
            x = int(center_x + math.cos(angle) * t * size)
            y = int(center_y + math.sin(angle) * t * size)
            
            if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                # Carve area around the line
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                            height_field[ny][nx] = 0.0
