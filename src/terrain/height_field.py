"""
Height field generation for flowing terrain.
This module handles the mathematical generation of terrain height maps.
"""

import math
from typing import List, Tuple, Set
import rng
from config import get_config


class NoiseGenerator:
    """Simple noise generation for terrain features"""
    
    @staticmethod
    def perlin_noise_2d(x: float, y: float, scale: float = 1.0) -> float:
        """Generate Perlin-like noise at given coordinates"""
        # Use deterministic pseudo-random values based on coordinates
        x_scaled = x * scale
        y_scaled = y * scale
        
        # Get integer grid points
        x0 = int(x_scaled)
        y0 = int(y_scaled)
        x1 = x0 + 1
        y1 = y0 + 1
        
        # Get fractional parts
        fx = x_scaled - x0
        fy = y_scaled - y0
        
        # Generate corner values using hash-like function
        def noise_at(xi: int, yi: int) -> float:
            # Simple hash function for consistent pseudo-random values
            # Use a deterministic approach that doesn't require state management
            seed = ((xi * 374761393) ^ (yi * 668265263)) & 0x7FFFFFFF
            # Use a simple linear congruential generator for deterministic values
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            return (seed / 0x7FFFFFFF) * 2.0 - 1.0
        
        # Get corner values
        n00 = noise_at(x0, y0)
        n10 = noise_at(x1, y0)
        n01 = noise_at(x0, y1)
        n11 = noise_at(x1, y1)
        
        # Smooth interpolation
        def smoothstep(t: float) -> float:
            return t * t * (3 - 2 * t)
        
        sx = smoothstep(fx)
        sy = smoothstep(fy)
        
        # Bilinear interpolation
        nx0 = n00 + sx * (n10 - n00)
        nx1 = n01 + sx * (n11 - n01)
        
        return nx0 + sy * (nx1 - nx0)
    
    @staticmethod
    def octave_noise(x: float, y: float, octaves: int = 4, persistence: float = 0.5, 
                    scale: float = 1.0) -> float:
        """Generate noise with multiple octaves for more complex patterns"""
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        
        for _ in range(octaves):
            value += NoiseGenerator.perlin_noise_2d(x, y, frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        
        return value / max_value


class FlowField:
    """Generates flowing terrain patterns using noise and flow algorithms"""
    
    def __init__(self, width: int, height: int, grid_scale: int):
        self.width = width
        self.height = height
        self.grid_scale = grid_scale
        self.grid_width = width // grid_scale
        self.grid_height = height // grid_scale
        self.cfg = get_config().terrain
    
    def generate_base_flow_field(self, complexity: float) -> List[List[float]]:
        """Generate base terrain using multiple noise layers - start mostly solid"""
        height_field = [[1.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]  # Start solid
        
        # Adjust noise parameters based on complexity
        base_threshold = self.cfg.BASE_TERRAIN_THRESHOLD * (0.8 + complexity * 0.4)
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Combine multiple noise scales for organic terrain
                large_noise = NoiseGenerator.octave_noise(
                    x, y, octaves=4, scale=self.cfg.NOISE_SCALE_LARGE
                )
                medium_noise = NoiseGenerator.octave_noise(
                    x, y, octaves=3, scale=self.cfg.NOISE_SCALE_MEDIUM
                )
                small_noise = NoiseGenerator.octave_noise(
                    x, y, octaves=2, scale=self.cfg.NOISE_SCALE_SMALL
                )
                
                # Combine noise layers with different weights for more solid terrain
                combined_noise = (
                    large_noise * 0.5 + 
                    medium_noise * 0.3 + 
                    small_noise * 0.2
                )
                
                # Apply complexity scaling - carve out paths where noise is low
                if combined_noise < -0.3:  # Only carve where noise is quite negative
                    height_field[y][x] = 0.0  # Open space
                # Keep most areas as solid terrain
        
        return height_field
    
    def apply_edge_variations(self, height_field: List[List[float]], complexity: float):
        """Create organic edge variations but keep them solid"""
        border_width_cells = max(2, self.cfg.SOLID_BORDER_WIDTH // self.grid_scale)  # Thicker borders
        variation_strength = self.cfg.EDGE_VARIATION_STRENGTH * complexity * 0.5  # Less variation
        
        # Apply variations to each border - keep them solid
        for side in ['top', 'bottom', 'left', 'right']:
            self._make_solid_border(height_field, side, border_width_cells)
    
    def _vary_border_edge(self, height_field: List[List[float]], side: str, 
                         border_width: int, strength: float):
        """Apply organic variations to a specific border edge"""
        if side in ['top', 'bottom']:
            length = self.grid_width
            for i in range(length):
                # Generate edge variation using noise with multiple octaves for more organic shape
                variation = NoiseGenerator.octave_noise(
                    i, 0, octaves=4, persistence=0.6, scale=self.cfg.EDGE_COMPLEXITY_SCALE
                ) * strength
                
                # Calculate varied border depth
                varied_depth = int(border_width + variation * border_width * 1.5)
                varied_depth = max(1, min(self.grid_height // 2, varied_depth))
                
                # Apply to border with soft falloff
                if side == 'top':
                    for j in range(varied_depth + 2):
                        if j < self.grid_height:
                            if j < varied_depth:
                                height_field[j][i] = 1.0
                            else:
                                # Soft edge
                                falloff = 1.0 - (j - varied_depth) / 2.0
                                height_field[j][i] = max(height_field[j][i], falloff)
                else:  # bottom
                    for j in range(varied_depth + 2):
                        row_idx = self.grid_height - 1 - j
                        if row_idx >= 0:
                            if j < varied_depth:
                                height_field[row_idx][i] = 1.0
                            else:
                                # Soft edge
                                falloff = 1.0 - (j - varied_depth) / 2.0
                                height_field[row_idx][i] = max(height_field[row_idx][i], falloff)
        
        else:  # left or right
            length = self.grid_height
            for i in range(length):
                variation = NoiseGenerator.octave_noise(
                    0, i, octaves=4, persistence=0.6, scale=self.cfg.EDGE_COMPLEXITY_SCALE
                ) * strength
                
                varied_depth = int(border_width + variation * border_width * 1.5)
                varied_depth = max(1, min(self.grid_width // 2, varied_depth))
                
                if side == 'left':
                    for j in range(varied_depth + 2):
                        if j < self.grid_width:
                            if j < varied_depth:
                                height_field[i][j] = 1.0
                            else:
                                # Soft edge
                                falloff = 1.0 - (j - varied_depth) / 2.0
                                height_field[i][j] = max(height_field[i][j], falloff)
                else:  # right
                    for j in range(varied_depth + 2):
                        col_idx = self.grid_width - 1 - j
                        if col_idx >= 0:
                            if j < varied_depth:
                                height_field[i][col_idx] = 1.0
                            else:
                                # Soft edge
                                falloff = 1.0 - (j - varied_depth) / 2.0
                                height_field[i][col_idx] = max(height_field[i][col_idx], falloff)
    
    def add_interior_features(self, height_field: List[List[float]], complexity: float):
        """Add interior carved areas and features"""
        # Create interior carved spaces for complexity
        num_features = int(self.cfg.INTERIOR_OBSTACLE_DENSITY * complexity * 
                          self.grid_width * self.grid_height * 0.08)  # More carved areas
        
        for _ in range(num_features):
            # Random position away from borders
            border_margin = max(4, self.grid_width // 15)
            x = rng.randint(border_margin, self.grid_width - border_margin)
            y = rng.randint(border_margin, self.grid_height - border_margin)
            
            # Random size
            size = rng.randint(self.cfg.MIN_OBSTACLE_SIZE, self.cfg.MAX_OBSTACLE_SIZE)
            
            # Create carved out areas (chambers)
            if rng.random_float() < 0.7:  # More circular chambers
                self._carve_circular_area(height_field, x, y, size / 2)
            else:  # Some elongated chambers
                self._carve_elongated_area(height_field, x, y, size)

    def _carve_elongated_area(self, height_field: List[List[float]], 
                               center_x: int, center_y: int, size: int):
        """Carve an elongated area (chamber or corridor)"""
        # Random orientation
        angle = rng.uniform(0, 2 * math.pi)
        length = size * 2
        
        for i in range(length):
            t = i / max(1, length - 1)
            x = int(center_x + math.cos(angle) * t * size)
            y = int(center_y + math.sin(angle) * t * size)
            
            if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                # Carve out area around the line
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                            height_field[ny][nx] = 0.0  # Clear carved area

    def _add_circular_obstacle(self, height_field: List[List[float]], 
                              center_x: int, center_y: int, radius: int):
        """Add a circular obstacle"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                
                if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= radius:
                        # Smooth falloff at edges
                        if distance <= radius - 1:
                            height_field[y][x] = 1.0
                        else:
                            # Soft edge
                            falloff = 1.0 - (distance - (radius - 1))
                            height_field[y][x] = max(height_field[y][x], falloff)

    def _add_elongated_obstacle(self, height_field: List[List[float]], 
                               center_x: int, center_y: int, size: int):
        """Add an elongated obstacle (small branching channel or ridge)"""
        # Random orientation
        angle = rng.uniform(0, 2 * math.pi)
        length = size * 2
        
        for i in range(length):
            t = i / max(1, length - 1)
            x = int(center_x + math.cos(angle) * t * size)
            y = int(center_y + math.sin(angle) * t * size)
            
            if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                # Add some width to the line
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                            height_field[ny][nx] = max(height_field[ny][nx], 0.8)
    
    def create_flow_channels(self, height_field: List[List[float]], complexity: float):
        """Create sweeping flow channels through the terrain"""
        if complexity < 0.2:
            return  # Don't create channels for very low complexity
        
        num_channels = max(1, int(self.cfg.FLOW_CHANNEL_COUNT * complexity))
        
        for _ in range(num_channels):
            self._carve_flow_channel(height_field, complexity)
    
    def _carve_flow_channel(self, height_field: List[List[float]], complexity: float):
        """Carve a single flowing channel through the terrain"""
        # Choose random start and end points
        start_side = rng.choice(['top', 'bottom', 'left', 'right'])
        end_side = rng.choice(['top', 'bottom', 'left', 'right'])
        
        # Avoid channels that go from one side to the same side
        while end_side == start_side:
            end_side = rng.choice(['top', 'bottom', 'left', 'right'])
        
        start_x, start_y = self._get_border_point(start_side)
        end_x, end_y = self._get_border_point(end_side)
        
        # Create curved path between start and end
        channel_width = rng.uniform(self.cfg.FLOW_CHANNEL_WIDTH_MIN, 
                                   self.cfg.FLOW_CHANNEL_WIDTH_MAX)
        
        # Use Bezier-like curve for organic flow
        self._carve_curved_path(height_field, start_x, start_y, end_x, end_y, channel_width)
    
    def _get_border_point(self, side: str) -> Tuple[int, int]:
        """Get a random point on a border side"""
        border_margin = 5  # Stay away from corners
        
        if side == 'top':
            return (rng.randint(border_margin, self.grid_width - border_margin), 0)
        elif side == 'bottom':
            return (rng.randint(border_margin, self.grid_width - border_margin), self.grid_height - 1)
        elif side == 'left':
            return (0, rng.randint(border_margin, self.grid_height - border_margin))
        else:  # right
            return (self.grid_width - 1, rng.randint(border_margin, self.grid_height - border_margin))
    
    def _carve_curved_path(self, height_field: List[List[float]], 
                          start_x: int, start_y: int, end_x: int, end_y: int, width: float):
        """Carve a curved path between two points"""
        # Create control points for organic curves
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Add curvature by offsetting the midpoint
        curvature = self.cfg.FLOW_CHANNEL_CURVATURE
        offset_x = rng.uniform(-curvature, curvature) * abs(end_x - start_x)
        offset_y = rng.uniform(-curvature, curvature) * abs(end_y - start_y)
        
        control_x = mid_x + offset_x
        control_y = mid_y + offset_y
        
        # Sample points along the curve
        num_points = max(50, int(math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2) * 2))
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Quadratic Bezier curve
            x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
            y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
            
            # Carve channel at this point
            self._carve_circular_area(height_field, x, y, width / 2)
    
    def _carve_circular_area(self, height_field: List[List[float]], 
                            center_x: float, center_y: float, radius: float):
        """Carve out a circular area (set to open space)"""
        radius_int = int(radius)
        center_x_int = int(center_x)
        center_y_int = int(center_y)
        
        for dy in range(-radius_int - 1, radius_int + 2):
            for dx in range(-radius_int - 1, radius_int + 2):
                x = center_x_int + dx
                y = center_y_int + dy
                
                if (0 <= x < self.grid_width and 0 <= y < self.grid_height):
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius:
                        # Aggressive carving to create clear paths
                        if distance <= radius * 0.8:
                            height_field[y][x] = 0.0  # Completely clear path
                        else:
                            # Gradual falloff at edges
                            falloff = (radius - distance) / (radius * 0.2)
                            height_field[y][x] = min(height_field[y][x], 1.0 - falloff)
    
    def create_dead_ends(self, height_field: List[List[float]], complexity: float):
        """Create dead-end corridors by carving into border areas"""
        num_dead_ends = int(self.cfg.DEAD_END_PROBABILITY * complexity * 8)
        """Create dead-end corridors by carving into border areas"""
        num_dead_ends = int(self.cfg.DEAD_END_PROBABILITY * complexity * 8)
        
        for _ in range(num_dead_ends):
            # Choose a random border to carve from
            side = rng.choice(['top', 'bottom', 'left', 'right'])
            self._carve_dead_end(height_field, side)
    
    def _carve_dead_end(self, height_field: List[List[float]], side: str):
        """Carve a dead end from a specific border"""
        depth = rng.randint(self.cfg.DEAD_END_DEPTH_MIN, self.cfg.DEAD_END_DEPTH_MAX)
        width = rng.randint(2, 4)  # Dead end width
        
        if side == 'top':
            x = rng.randint(width, self.grid_width - width)
            for d in range(depth):
                for w in range(-width//2, width//2 + 1):
                    if (0 <= x + w < self.grid_width and d < self.grid_height):
                        height_field[d][x + w] = 0.0
        elif side == 'bottom':
            x = rng.randint(width, self.grid_width - width)
            for d in range(depth):
                for w in range(-width//2, width//2 + 1):
                    if (0 <= x + w < self.grid_width and 
                        self.grid_height - 1 - d >= 0):
                        height_field[self.grid_height - 1 - d][x + w] = 0.0
        elif side == 'left':
            y = rng.randint(width, self.grid_height - width)
            for d in range(depth):
                for w in range(-width//2, width//2 + 1):
                    if (0 <= y + w < self.grid_height and d < self.grid_width):
                        height_field[y + w][d] = 0.0
        else:  # right
            y = rng.randint(width, self.grid_height - width)
            for d in range(depth):
                for w in range(-width//2, width//2 + 1):
                    if (0 <= y + w < self.grid_height and 
                        self.grid_width - 1 - d >= 0):
                        height_field[y + w][self.grid_width - 1 - d] = 0.0
    
    def ensure_connectivity(self, height_field: List[List[float]]) -> List[List[float]]:
        """Ensure all open areas are connected using flood fill"""
        # Create a copy to modify
        connected_field = [row[:] for row in height_field]
        threshold = 0.5
        
        # Find largest connected component
        visited = set()
        largest_component = set()
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if ((x, y) not in visited and 
                    connected_field[y][x] < threshold):
                    
                    component = self._flood_fill(connected_field, x, y, threshold, visited)
                    if len(component) > len(largest_component):
                        largest_component = component
        
        # Fill all areas not connected to the largest component
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if ((x, y) not in largest_component and 
                    connected_field[y][x] < threshold):
                    connected_field[y][x] = 1.0
        
        return connected_field
    
    def _flood_fill(self, height_field: List[List[float]], start_x: int, start_y: int,
                   threshold: float, global_visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Flood fill to find connected components"""
        component = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if ((x, y) in global_visited or 
                x < 0 or x >= self.grid_width or 
                y < 0 or y >= self.grid_height or
                height_field[y][x] >= threshold):
                continue
            
            global_visited.add((x, y))
            component.add((x, y))
            
            # Add neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                stack.append((x + dx, y + dy))
        
        return component


class AdvancedFlowField:
    """Main class for generating advanced flowing terrain"""
    
    def __init__(self, width: int, height: int, complexity: float = 0.5):
        self.width = width
        self.height = height
        self.complexity = max(0.0, min(1.0, complexity))
        self.cfg = get_config().terrain
        
        self.flow_field = FlowField(width, height, self.cfg.TERRAIN_GRID_SCALE)
    
    def generate(self) -> List[List[float]]:
        """Generate complete flowing terrain height field"""
        if self.complexity <= 0.0:
            # Generate only borders for zero complexity
            return self._generate_border_only()
        
        # Generate base terrain using noise
        height_field = self.flow_field.generate_base_flow_field(self.complexity)
        
        # Create flow channels for sweeping corridors
        self.flow_field.create_flow_channels(height_field, self.complexity)
        
        # Apply edge variations for organic borders
        self.flow_field.apply_edge_variations(height_field, self.complexity)
        
        # Add interior features
        self.flow_field.add_interior_features(height_field, self.complexity)
        
        # Create dead ends
        self.flow_field.create_dead_ends(height_field, self.complexity)
        
        # Ensure all open areas are connected
        height_field = self.flow_field.ensure_connectivity(height_field)
        
        return height_field
    
    def _generate_border_only(self) -> List[List[float]]:
        """Generate terrain with only solid borders"""
        grid_width = self.width // self.cfg.TERRAIN_GRID_SCALE
        grid_height = self.height // self.cfg.TERRAIN_GRID_SCALE
        height_field = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
        
        border_width_x = max(1, self.cfg.SOLID_BORDER_WIDTH // self.cfg.TERRAIN_GRID_SCALE)
        border_width_y = max(1, self.cfg.SOLID_BORDER_WIDTH // self.cfg.TERRAIN_GRID_SCALE)
        
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
        
        return height_field
