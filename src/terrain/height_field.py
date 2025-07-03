"""
Height field generation for flowing terrain.
This module handles the mathematical generation of terrain height maps.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import math
from typing import List, Tuple
import rng


class SimpleFlowField:
    """Simple flowing terrain using pure Python height field generation"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid_width = width // 8  # Lower resolution
        self.grid_height = height // 8

        # Create height field as 2D list
        self.height_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
    def generate_base_terrain(self, complexity: float = 0.5):
        """Generate flowing terrain using sine waves and random walks"""
        # Create flowing base using multiple sine waves
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Multiple sine wave frequencies for organic look
                freq1 = 0.1 * (1 + complexity)
                freq2 = 0.05 * (1 + complexity * 0.5)
                freq3 = 0.2 * (1 + complexity * 2)
                
                height = (
                    math.sin(x * freq1) * math.cos(y * freq1 * 0.7) * 0.4 +
                    math.sin(x * freq2 * 1.3) * math.sin(y * freq2 * 0.9) * 0.3 +
                    math.cos(x * freq3 * 0.8) * math.cos(y * freq3 * 1.1) * 0.3
                )
                
                self.height_field[y][x] = height
        
        # Normalize to 0-1 range
        min_val = min(min(row) for row in self.height_field)
        max_val = max(max(row) for row in self.height_field)
        range_val = max_val - min_val
        
        if range_val > 0:
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    self.height_field[y][x] = (self.height_field[y][x] - min_val) / range_val
    
    def create_flow_channels(self, complexity: float = 0.5):
        """Create flowing channels using random walks"""
        num_channels = int(5 + complexity * 15)
        
        for _ in range(num_channels):
            # Start from top edge
            start_x = rng.randint(self.grid_width // 4, 3 * self.grid_width // 4)
            start_y = rng.randint(0, self.grid_height // 4)
            
            self._carve_channel(start_x, start_y, complexity)
    
    def _carve_channel(self, start_x: int, start_y: int, complexity: float):
        """Carve a flowing channel from start point"""
        x, y = start_x, start_y
        direction = rng.uniform(0, 2 * math.pi)
        
        channel_length = int(20 + complexity * 40)
        carve_strength = 0.1 + complexity * 0.2
        
        for step in range(channel_length):
            # Stay within bounds
            if x < 1 or x >= self.grid_width - 1 or y < 1 or y >= self.grid_height - 1:
                break
            
            # Carve out terrain (lower the height)
            carve_radius = 2
            for dy in range(-carve_radius, carve_radius + 1):
                for dx in range(-carve_radius, carve_radius + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance <= carve_radius:
                            erosion = carve_strength * (1 - distance / carve_radius)
                            self.height_field[ny][nx] -= erosion
            
            # Update direction with some randomness for organic flow
            direction += rng.uniform(-0.3, 0.3)
            
            # Move in flow direction
            x += math.cos(direction) * (1 + rng.uniform(0, 0.5))
            y += math.sin(direction) * (1 + rng.uniform(0, 0.5))
            x, y = int(x), int(y)
    
    def smooth_terrain(self):
        """Simple smoothing filter"""
        new_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                # Simple average of neighbors
                total = 0.0
                count = 0
                
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        total += self.height_field[y + dy][x + dx]
                        count += 1
                
                new_field[y][x] = total / count
        
        # Copy back (except edges)
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                self.height_field[y][x] = new_field[y][x]
    
    def smooth_terrain_advanced(self, iterations: int = 4, strength: float = 0.8):
        """Advanced smoothing with multiple iterations and configurable strength"""
        for _ in range(iterations):
            new_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
            
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    # Gaussian-like smoothing kernel
                    total = 0.0
                    weight_sum = 0.0
                    
                    # Use weighted average with higher weight for center
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                weight = 4.0  # Center weight
                            elif abs(dx) + abs(dy) == 1:
                                weight = 2.0  # Edge neighbors
                            else:
                                weight = 1.0  # Corner neighbors
                            
                            total += self.height_field[y + dy][x + dx] * weight
                            weight_sum += weight
                    
                    smoothed_value = total / weight_sum
                    # Blend original with smoothed based on strength
                    new_field[y][x] = (1 - strength) * self.height_field[y][x] + strength * smoothed_value
            
            # Copy back (except edges which stay as borders)
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    self.height_field[y][x] = new_field[y][x]
    
    def apply_erosion(self, iterations: int = 2):
        """Apply morphological erosion to remove small terrain features"""
        for _ in range(iterations):
            new_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
            
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    # Find minimum in 3x3 neighborhood
                    min_height = self.height_field[y][x]
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            min_height = min(min_height, self.height_field[y + dy][x + dx])
                    
                    new_field[y][x] = min_height
            
            # Copy back
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    self.height_field[y][x] = new_field[y][x]
    
    def apply_dilation(self, iterations: int = 1):
        """Apply morphological dilation to expand terrain features"""
        for _ in range(iterations):
            new_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
            
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    # Find maximum in 3x3 neighborhood
                    max_height = self.height_field[y][x]
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            max_height = max(max_height, self.height_field[y + dy][x + dx])
                    
                    new_field[y][x] = max_height
            
            # Copy back
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    self.height_field[y][x] = new_field[y][x]
    
    def create_flowing_channels_smooth(self, complexity: float = 0.5):
        """Create smoother flowing channels with better connectivity"""
        # Reduce number of channels but make them wider and more flowing
        num_channels = max(2, int(3 + complexity * 8))
        
        for i in range(num_channels):
            # Create main flow lines from different edges
            if i % 4 == 0:  # From top
                start_x = rng.randint(self.grid_width // 4, 3 * self.grid_width // 4)
                start_y = rng.randint(0, self.grid_height // 6)
                general_direction = math.pi / 2  # Downward
            elif i % 4 == 1:  # From left
                start_x = rng.randint(0, self.grid_width // 6)
                start_y = rng.randint(self.grid_height // 4, 3 * self.grid_height // 4)
                general_direction = 0  # Rightward
            elif i % 4 == 2:  # From bottom
                start_x = rng.randint(self.grid_width // 4, 3 * self.grid_width // 4)
                start_y = rng.randint(5 * self.grid_height // 6, self.grid_height - 1)
                general_direction = -math.pi / 2  # Upward
            else:  # From right
                start_x = rng.randint(5 * self.grid_width // 6, self.grid_width - 1)
                start_y = rng.randint(self.grid_height // 4, 3 * self.grid_height // 4)
                general_direction = math.pi  # Leftward
            
            self._carve_smooth_channel(start_x, start_y, general_direction, complexity)
    
    def _carve_smooth_channel(self, start_x: int, start_y: int, general_direction: float, complexity: float):
        """Carve a smooth flowing channel with consistent width"""
        x, y = float(start_x), float(start_y)
        direction = general_direction
        
        channel_length = int(30 + complexity * 60)
        base_width = 3 + int(complexity * 4)  # Wider channels
        carve_strength = 0.3 + complexity * 0.4  # Stronger carving
        
        for step in range(channel_length):
            # Stay within bounds with margin
            if x < 2 or x >= self.grid_width - 2 or y < 2 or y >= self.grid_height - 2:
                break
            
            # Carve with varying width for natural look
            current_width = base_width + rng.uniform(-1, 1)
            
            for dy in range(-int(current_width), int(current_width) + 1):
                for dx in range(-int(current_width), int(current_width) + 1):
                    nx, ny = int(x) + dx, int(y) + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance <= current_width:
                            # Smooth falloff from center
                            erosion = carve_strength * max(0, 1 - distance / current_width)
                            self.height_field[ny][nx] -= erosion
            
            # Update direction with gentle curves toward center
            center_x = self.grid_width / 2
            center_y = self.grid_height / 2
            
            # Slight bias toward center for better flow
            to_center_x = center_x - x
            to_center_y = center_y - y
            to_center_angle = math.atan2(to_center_y, to_center_x)
            
            # Blend general direction with center bias and some randomness
            direction = (
                0.7 * direction + 
                0.2 * to_center_angle + 
                0.1 * rng.uniform(-math.pi/3, math.pi/3)
            )
            
            # Move in flow direction with consistent step size
            step_size = 1.2 + rng.uniform(-0.2, 0.2)
            x += math.cos(direction) * step_size
            y += math.sin(direction) * step_size
            
    def add_solid_border(self, border_width_pixels: int = 20):
        """Add a solid border around the terrain"""
        # Convert pixel border width to grid units
        border_width_x = max(1, border_width_pixels // (self.width // self.grid_width))
        border_width_y = max(1, border_width_pixels // (self.height // self.grid_height))
        
        # Set top and bottom borders
        for y in range(min(border_width_y, self.grid_height)):
            for x in range(self.grid_width):
                self.height_field[y][x] = 1.0  # Solid terrain
                self.height_field[self.grid_height - 1 - y][x] = 1.0
        
        # Set left and right borders
        for x in range(min(border_width_x, self.grid_width)):
            for y in range(self.grid_height):
                self.height_field[y][x] = 1.0  # Solid terrain
                self.height_field[y][self.grid_width - 1 - x] = 1.0
    
    def remove_small_terrain_pieces(self, min_region_size: int = 50):
        """Remove small scattered terrain pieces using flood fill"""
        # Convert pixel size to grid units
        min_grid_size = max(4, min_region_size // (self.width // self.grid_width))
        
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        threshold = 0.3  # Same threshold used for terrain detection
        
        def flood_fill(start_x: int, start_y: int) -> List[Tuple[int, int]]:
            """Flood fill to find connected terrain regions"""
            region = []
            stack = [(start_x, start_y)]
            
            while stack:
                x, y = stack.pop()
                if (x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height or
                    visited[y][x] or self.height_field[y][x] <= threshold):
                    continue
                
                visited[y][x] = True
                region.append((x, y))
                
                # Add neighbors to stack
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    stack.append((x + dx, y + dy))
            
            return region
        
        # Find all terrain regions and remove small ones
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not visited[y][x] and self.height_field[y][x] > threshold:
                    region = flood_fill(x, y)
                    
                    # If region is too small, remove it
                    if len(region) < min_grid_size:
                        for rx, ry in region:
                            self.height_field[ry][rx] = 0.0  # Clear terrain
    
    def apply_border_fade(self, fade_distance: int = 10):
        """Apply a fade effect near borders for smoother transitions"""
        fade_grid = max(1, fade_distance // (self.width // self.grid_width))
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Calculate distance from edges
                dist_from_edge = min(x, y, self.grid_width - 1 - x, self.grid_height - 1 - y)
                
                if dist_from_edge < fade_grid:
                    # Gradually increase terrain height near edges
                    fade_factor = 1.0 - (dist_from_edge / fade_grid)
                    self.height_field[y][x] = max(self.height_field[y][x], fade_factor * 0.8)
