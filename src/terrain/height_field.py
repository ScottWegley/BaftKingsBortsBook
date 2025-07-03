"""
Height field generation for flowing terrain.
This module handles the mathematical generation of terrain height maps.
"""

import math
from typing import List, Tuple
import rng


import numpy as np
import scipy.ndimage
import skimage.morphology

class AdvancedFlowField:
    def remove_isolated_pockets(self, min_pocket_size: int = 50):
        """Remove isolated pockets of terrain or open space that are too small"""
        # First pass: identify connected regions of terrain (above threshold)
        threshold = 0.3
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        terrain_regions = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not visited[y][x] and self.height_field[y][x] > threshold:
                    region = self._flood_fill_region(x, y, threshold, visited, True)
                    if region:
                        terrain_regions.append(region)
        # Remove small terrain regions
        for region in terrain_regions:
            if len(region) < min_pocket_size:
                for x, y in region:
                    self.height_field[y][x] = 0.1  # Convert to open space
        # Second pass: identify connected regions of open space (below threshold)
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        open_regions = []
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not visited[y][x] and self.height_field[y][x] <= threshold:
                    region = self._flood_fill_region(x, y, threshold, visited, False)
                    if region:
                        open_regions.append(region)
        # Remove small open space regions (fill them in)
        for region in open_regions:
            if len(region) < min_pocket_size:
                for x, y in region:
                    self.height_field[y][x] = 0.6  # Convert to terrain

    def _flood_fill_region(self, start_x: int, start_y: int, threshold: float, visited, is_terrain: bool):
        """Flood fill to find connected regions"""
        if (start_x < 0 or start_x >= self.grid_width or start_y < 0 or start_y >= self.grid_height or visited[start_y][start_x]):
            return []
        cell_is_terrain = self.height_field[start_y][start_x] > threshold
        if cell_is_terrain != is_terrain:
            return []
        stack = [(start_x, start_y)]
        region = []
        while stack:
            x, y = stack.pop()
            if (x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height or visited[y][x]):
                continue
            cell_is_terrain = self.height_field[y][x] > threshold
            if cell_is_terrain != is_terrain:
                continue
            visited[y][x] = True
            region.append((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))
        return region

    def ensure_connectivity(self):
        """Ensure open spaces are well connected by widening narrow passages"""
        threshold = 0.3
        for y in range(2, self.grid_height - 2):
            for x in range(2, self.grid_width - 2):
                if self.height_field[y][x] <= threshold:  # This is open space
                    if self._is_narrow_passage(x, y, threshold):
                        self._widen_passage(x, y, threshold)

    def _is_narrow_passage(self, x: int, y: int, threshold: float) -> bool:
        """Check if a point is part of a narrow passage"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        terrain_walls = 0
        for dx, dy in directions:
            wall_found = False
            for dist in range(1, 3):
                check_x, check_y = x + dx * dist, y + dy * dist
                if (0 <= check_x < self.grid_width and 0 <= check_y < self.grid_height):
                    if self.height_field[check_y][check_x] > threshold:
                        wall_found = True
                        break
            if wall_found:
                terrain_walls += 1
        return terrain_walls >= 2

    def _widen_passage(self, x: int, y: int, threshold: float):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    if self.height_field[ny][nx] > threshold:
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance <= 1.5:
                            reduction = 0.3 * (1.5 - distance) / 1.5
                            self.height_field[ny][nx] = max(0.1, self.height_field[ny][nx] - reduction)

    def promote_continuous_spaces(self):
        """Promote formation of continuous open spaces"""
        threshold = 0.3
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                if self.height_field[y][x] > threshold:  # This is terrain
                    open_neighbors = 0
                    total_neighbors = 0
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                                total_neighbors += 1
                                if self.height_field[ny][nx] <= threshold:
                                    open_neighbors += 1
                    if total_neighbors > 0 and open_neighbors / total_neighbors > 0.6:
                        self.height_field[y][x] = 0.2  # Convert to open space
    """Simple flowing terrain using pure Python height field generation"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid_width = width // 8  # Lower resolution
        self.grid_height = height // 8        # Create height field as 2D list
        self.height_field = [[0.0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
    def generate_base_terrain(self, complexity: float = 0.5):
        """Generate flowing terrain using advanced numpy/scipy/skimage algorithms"""
        # Use Perlin/simplex noise or random fields for base
        base = np.random.rand(self.grid_height, self.grid_width)
        # Smooth with gaussian filter for organic look
        base = scipy.ndimage.gaussian_filter(base, sigma=3 + 8 * (1 - complexity))
        # Normalize
        base = (base - base.min()) / (base.max() - base.min())
        self.height_field = base.tolist()
    
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
    
    def remove_isolated_pockets(self, min_pocket_size: int = 50):
        """Remove isolated pockets of terrain or open space that are too small"""
        # First pass: identify connected regions of terrain (above threshold)
        threshold = 0.3
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        terrain_regions = []
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not visited[y][x] and self.height_field[y][x] > threshold:
                    region = self._flood_fill_region(x, y, threshold, visited, True)
                    if region:
                        terrain_regions.append(region)
        
        # Remove small terrain regions
        for region in terrain_regions:
            if len(region) < min_pocket_size:
                for x, y in region:
                    self.height_field[y][x] = 0.1  # Convert to open space
        
        # Second pass: identify connected regions of open space (below threshold)
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        open_regions = []
        
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if not visited[y][x] and self.height_field[y][x] <= threshold:
                    region = self._flood_fill_region(x, y, threshold, visited, False)
                    if region:
                        open_regions.append(region)
        
        # Remove small open space regions (fill them in)
        for region in open_regions:
            if len(region) < min_pocket_size:
                for x, y in region:
                    self.height_field[y][x] = 0.6  # Convert to terrain
    
    def _flood_fill_region(self, start_x: int, start_y: int, threshold: float, 
                          visited: List[List[bool]], is_terrain: bool) -> List[Tuple[int, int]]:
        """Flood fill to find connected regions"""
        if (start_x < 0 or start_x >= self.grid_width or 
            start_y < 0 or start_y >= self.grid_height or 
            visited[start_y][start_x]):
            return []
        
        # Check if this cell matches the type we're looking for
        cell_is_terrain = self.height_field[start_y][start_x] > threshold
        if cell_is_terrain != is_terrain:
            return []
        
        # Use iterative flood fill to avoid stack overflow
        stack = [(start_x, start_y)]
        region = []
        
        while stack:
            x, y = stack.pop()
            
            if (x < 0 or x >= self.grid_width or 
                y < 0 or y >= self.grid_height or 
                visited[y][x]):
                continue
            
            cell_is_terrain = self.height_field[y][x] > threshold
            if cell_is_terrain != is_terrain:
                continue
            
            visited[y][x] = True
            region.append((x, y))
            
            # Add neighbors to stack
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))
        
        return region
    
    def ensure_connectivity(self):
        """Ensure open spaces are well connected by widening narrow passages"""
        threshold = 0.3
        
        # Find narrow passages and widen them
        for y in range(2, self.grid_height - 2):
            for x in range(2, self.grid_width - 2):
                if self.height_field[y][x] <= threshold:  # This is open space
                    # Check if this is a narrow passage
                    if self._is_narrow_passage(x, y, threshold):
                        # Widen the passage
                        self._widen_passage(x, y, threshold)
    
    def _is_narrow_passage(self, x: int, y: int, threshold: float) -> bool:
        """Check if a point is part of a narrow passage"""
        # Check in 4 directions to see if there are terrain walls close by
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        terrain_walls = 0
        
        for dx, dy in directions:
            # Check if there's terrain within 2 cells in this direction
            wall_found = False
            for dist in range(1, 3):
                check_x, check_y = x + dx * dist, y + dy * dist
                if (0 <= check_x < self.grid_width and 0 <= check_y < self.grid_height):
                    if self.height_field[check_y][check_x] > threshold:
                        wall_found = True
                        break
            if wall_found:
                terrain_walls += 1
        
        # If we have terrain walls in at least 2 opposite directions, it's narrow
        return terrain_walls >= 2
    
    def _widen_passage(self, x: int, y: int, threshold: float):
        """Widen a narrow passage by lowering nearby terrain"""
        # Widen in a small radius around the passage
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                    if self.height_field[ny][nx] > threshold:
                        # Gradually lower terrain to create wider passage
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance <= 1.5:
                            reduction = 0.3 * (1.5 - distance) / 1.5
                            self.height_field[ny][nx] = max(0.1, self.height_field[ny][nx] - reduction)
    
    def promote_continuous_spaces(self):
        """Promote formation of continuous open spaces"""
        threshold = 0.3
        
        # Find areas where open space could be expanded
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                if self.height_field[y][x] > threshold:  # This is terrain
                    # Count nearby open spaces
                    open_neighbors = 0
                    total_neighbors = 0
                    
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                                total_neighbors += 1
                                if self.height_field[ny][nx] <= threshold:
                                    open_neighbors += 1
                    
                    # If most neighbors are open space, convert this terrain to open space
                    if total_neighbors > 0 and open_neighbors / total_neighbors > 0.6:
                        self.height_field[y][x] = 0.2  # Convert to open space
    
    def add_scattered_terrain_islands(self, num_islands: int = 3):
        """Add scattered terrain islands in large open areas"""
        threshold = 0.3
        border_buffer = 20  # Stay away from borders
        
        # Find large open areas that could use some terrain islands
        potential_centers = []
        
        for y in range(border_buffer, self.grid_height - border_buffer, 15):
            for x in range(border_buffer, self.grid_width - border_buffer, 15):
                if self._is_good_island_location(x, y, threshold):
                    potential_centers.append((x, y))
        
        # Randomly select locations for islands
        if potential_centers:
            num_to_place = min(num_islands, len(potential_centers))
            selected_centers = []
            
            # Manually select random centers
            for _ in range(num_to_place):
                if potential_centers:
                    index = rng.randint(0, len(potential_centers) - 1)
                    selected_centers.append(potential_centers.pop(index))
            
            for center_x, center_y in selected_centers:
                self._create_terrain_island(center_x, center_y)
    
    def _is_good_island_location(self, x: int, y: int, threshold: float) -> bool:
        """Check if a location is good for placing a terrain island"""
        # Must be in open space
        if self.height_field[y][x] > threshold:
            return False
        
        # Check for sufficient open space around this point
        min_radius = 12
        for dy in range(-min_radius, min_radius + 1):
            for dx in range(-min_radius, min_radius + 1):
                check_x, check_y = x + dx, y + dy
                if (0 <= check_x < self.grid_width and 0 <= check_y < self.grid_height):
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance <= min_radius:
                        if self.height_field[check_y][check_x] > threshold:
                            return False
        
        return True
    
    def _create_terrain_island(self, center_x: int, center_y: int):
        """Create a terrain island at the specified location"""
        # Create irregular island shape
        island_radius = rng.randint(4, 8)
        
        for dy in range(-island_radius, island_radius + 1):
            for dx in range(-island_radius, island_radius + 1):
                island_x, island_y = center_x + dx, center_y + dy
                
                if (0 <= island_x < self.grid_width and 0 <= island_y < self.grid_height):
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    # Create irregular shape with some randomness
                    noise = rng.uniform(-0.3, 0.3)
                    effective_radius = island_radius + noise
                    
                    if distance <= effective_radius:
                        # Smooth falloff from center
                        height_factor = 1.0 - (distance / effective_radius)
                        height_factor = max(0, height_factor)
                        
                        # Add some randomness to height
                        height_variation = rng.uniform(0.8, 1.2)
                        new_height = 0.5 + (height_factor * 0.3 * height_variation)
                        
                        self.height_field[island_y][island_x] = max(
                            self.height_field[island_y][island_x], 
                            new_height
                        )
