"""
Simplified height field generation for cave-like terrain.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List
import rng
from config import get_config
from .noise import NoiseGenerator
from .carver import TerrainCarver


class CaveTerrainGenerator:
    """Generates cave-like terrain similar to reference images"""
    
    def __init__(self, width: int, height: int, complexity: float = 0.5):
        self.width = width
        self.height = height
        self.complexity = max(0.0, min(1.0, complexity))
        self.cfg = get_config().terrain
        
        self.grid_scale = self.cfg.TERRAIN_GRID_SCALE
        self.grid_width = width // self.grid_scale
        self.grid_height = height // self.grid_scale
        
        self.carver = TerrainCarver(self.grid_width, self.grid_height)
    
    def generate(self) -> List[List[float]]:
        """Generate cave-like terrain height field"""
        if self.complexity <= 0.0:
            return self._generate_border_only()
        
        # Start with mostly solid terrain
        height_field = self._create_base_solid_terrain()
        
        # Create solid borders
        self.carver.create_solid_borders(height_field)
        
        # Carve major flow channels
        self.carver.carve_flow_channels(height_field, self.complexity)
        
        # Carve interior chambers
        self.carver.carve_interior_chambers(height_field, self.complexity)
        
        # Ensure connectivity
        height_field = self._ensure_basic_connectivity(height_field)
        
        # Add organic roughening to remove straight lines (but keep it subtle)
        if self.complexity > 0.3:  # Only add roughening for higher complexity
            self.add_organic_roughening(height_field, self.complexity * 0.5)  # Reduce intensity
        
        return height_field
    
    def _create_base_solid_terrain(self) -> List[List[float]]:
        """Create base terrain that's mostly solid with some natural variation"""
        height_field = [[1.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Use noise to create larger, more connected natural chambers
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Create noise-based variation with larger scale
                large_noise = NoiseGenerator.octave_noise(
                    x, y, octaves=2, scale=0.015, persistence=0.7
                )
                medium_noise = NoiseGenerator.octave_noise(
                    x, y, octaves=3, scale=0.03, persistence=0.5
                )
                
                # Combine for more organic chambers
                combined_noise = large_noise * 0.7 + medium_noise * 0.3
                
                # Only carve where noise is quite negative (creates fewer, larger chambers)
                if combined_noise < -0.3:
                    height_field[y][x] = 0.0
        
        return height_field
    
    def _ensure_basic_connectivity(self, height_field: List[List[float]]) -> List[List[float]]:
        """Ensure there's good connectivity with gentle curves"""
        # Create main horizontal corridor with gentle curves
        mid_y = self.grid_height // 2
        
        for x in range(self.grid_width):
            # Use gentler noise for subtle curves
            curve_noise = NoiseGenerator.perlin_noise_2d(x, 0, 0.06) * 4  # Reduced from 8
            y = int(mid_y + curve_noise)
            y = max(3, min(self.grid_height - 4, y))
            
            # Consistent corridor width
            corridor_width = 4  # Fixed width for cleaner look
            
            # Carve clean corridor
            for dy in range(-corridor_width//2, corridor_width//2 + 1):
                corridor_y = y + dy
                if 0 <= corridor_y < self.grid_height:
                    height_field[corridor_y][x] = 0.0
        
        # Add simpler vertical connector
        mid_x = self.grid_width // 2
        for y in range(self.grid_height):
            # Gentle horizontal variation
            curve_noise = NoiseGenerator.perlin_noise_2d(0, y, 0.08) * 2  # Reduced from 4
            connector_x = int(mid_x + curve_noise)
            connector_x = max(2, min(self.grid_width - 3, connector_x))
            
            # Fixed width vertical connector
            width = 2
            for dx in range(-width, width + 1):
                final_x = connector_x + dx
                if 0 <= final_x < self.grid_width:
                    height_field[y][final_x] = 0.0
        
        # Remove small isolated solid areas (clean up terrain)
        height_field = self._remove_small_islands(height_field)
        
        return height_field
    
    def _remove_small_islands(self, height_field: List[List[float]]) -> List[List[float]]:
        """Remove small isolated solid terrain pieces"""
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                if height_field[y][x] > 0.5:  # Solid terrain
                    # Count solid neighbors
                    solid_neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if height_field[y + dy][x + dx] > 0.5:
                                solid_neighbors += 1
                    
                    # If this solid cell has very few solid neighbors, remove it
                    if solid_neighbors <= 2:
                        height_field[y][x] = 0.0
        
        return height_field
    
    def _generate_border_only(self) -> List[List[float]]:
        """Generate terrain with only solid borders"""
        height_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.carver.create_solid_borders(height_field)
        return height_field
    
    def add_organic_roughening(self, height_field: List[List[float]], complexity: float):
        """Add organic roughening to remove straight lines and add natural features"""
        # Add small outcroppings and inlets to terrain edges
        self._add_edge_roughening(height_field, complexity)
        
        # Add natural texture to large open areas
        self._add_area_texture(height_field, complexity)
        
        # Add small natural features
        self._add_micro_features(height_field, complexity)
    
    def _add_edge_roughening(self, height_field: List[List[float]], complexity: float):
        """Add subtle outcroppings and inlets along terrain edges"""
        roughening_strength = complexity * 0.3  # Much more subtle
        
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                current_val = height_field[y][x]
                
                # Check if this is an edge cell (solid next to open or vice versa)
                neighbors = [
                    height_field[y-1][x], height_field[y+1][x],
                    height_field[y][x-1], height_field[y][x+1]
                ]
                
                solid_neighbors = sum(1 for n in neighbors if n > 0.5)
                
                # Only modify clear edge cases and with lower probability
                if solid_neighbors == 2 or solid_neighbors == 3:
                    noise_val = NoiseGenerator.perlin_noise_2d(x, y, 0.1)
                    
                    if noise_val > 0.7 * roughening_strength:  # Higher threshold
                        # Create small outcroppings (less aggressive)
                        if current_val < 0.5:  # Open space
                            height_field[y][x] = 0.6  # Partial solid outcrop
                    elif noise_val < -0.7 * roughening_strength:  # Higher threshold
                        # Create small inlets (less aggressive)
                        if current_val > 0.5:  # Solid terrain
                            height_field[y][x] = 0.3  # Partial inlet
    
    def _add_area_texture(self, height_field: List[List[float]], complexity: float):
        """Add very subtle texture to break up large flat areas"""
        for y in range(3, self.grid_height - 3):
            for x in range(3, self.grid_width - 3):
                if height_field[y][x] < 0.5:  # Open space
                    # Check if this is in a very large open area
                    open_neighbors = 0
                    for dy in range(-3, 4):
                        for dx in range(-3, 4):
                            if height_field[y + dy][x + dx] < 0.5:
                                open_neighbors += 1
                    
                    # Only add texture in very large open areas and rarely
                    if open_neighbors > 35:  # Very large open area
                        texture_noise = NoiseGenerator.octave_noise(
                            x, y, octaves=2, scale=0.15, persistence=0.5
                        )
                        
                        if texture_noise > 0.8:  # Very high threshold
                            height_field[y][x] = 0.2  # Very subtle texture element
    
    def _add_micro_features(self, height_field: List[List[float]], complexity: float):
        """Add very few small natural features"""
        num_features = int(complexity * self.grid_width * self.grid_height * 0.002)  # Much fewer
        
        for _ in range(num_features):
            x = rng.randint(5, self.grid_width - 6)
            y = rng.randint(5, self.grid_height - 6)
            
            # Only add tiny chambers, no protrusions
            feature_type = rng.random_float()
            if feature_type < 0.7:  # Mostly chambers
                self._add_tiny_chamber(height_field, x, y)
    
    def _add_tiny_chamber(self, height_field: List[List[float]], center_x: int, center_y: int):
        """Add a tiny natural chamber"""
        radius = rng.randint(1, 3)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:  # Diamond shape
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        height_field[y][x] = 0.0
    
    def _add_tiny_protrusion(self, height_field: List[List[float]], center_x: int, center_y: int):
        """Add a tiny natural protrusion"""
        if height_field[center_y][center_x] < 0.5:  # Only in open areas
            # Random small shape
            shape_size = rng.randint(1, 2)
            for dy in range(-shape_size, shape_size + 1):
                for dx in range(-shape_size, shape_size + 1):
                    if abs(dx) + abs(dy) <= shape_size:
                        x, y = center_x + dx, center_y + dy
                        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                            height_field[y][x] = 0.8
