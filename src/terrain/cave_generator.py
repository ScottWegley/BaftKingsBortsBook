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
        """Ensure there's good connectivity and remove small isolated pockets"""
        # Create main horizontal corridor with more width
        mid_y = self.grid_height // 2
        
        for x in range(self.grid_width):
            # Add vertical variation for organic path
            noise_offset = int(NoiseGenerator.perlin_noise_2d(x, 0, 0.08) * 6)
            y = mid_y + noise_offset
            y = max(3, min(self.grid_height - 4, y))
            
            # Carve wider corridor (3-5 cells high)
            corridor_width = 3 + int(abs(NoiseGenerator.perlin_noise_2d(x, 0, 0.05)) * 2)
            for dy in range(-corridor_width//2, corridor_width//2 + 1):
                if 0 <= y + dy < self.grid_height:
                    height_field[y + dy][x] = 0.0
        
        # Add vertical connector in middle
        mid_x = self.grid_width // 2
        for y in range(self.grid_height):
            # Carve vertical path with some width
            for dx in range(-2, 3):
                if 0 <= mid_x + dx < self.grid_width:
                    height_field[y][mid_x + dx] = 0.0
        
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
