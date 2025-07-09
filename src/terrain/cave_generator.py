"""
Simplified height field generation for cave-like terrain.
"""


from typing import List, Tuple, Union
import numpy as np
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
    
    def generate(self) -> np.ndarray:
        """Generate organic, continuous terrain with chambers, corridors, branches, and islands (comprehensive update)."""
        if self.complexity <= 0.0:
            return self._generate_border_only()

        # --- 1. Start with solid terrain ---
        height_field = np.ones((self.grid_height, self.grid_width), dtype=np.float32)
        self.carver.create_solid_borders(height_field)

        # --- 2. Carve main winding path (smooth drunken walk) ---
        min_width = max(2, int(getattr(self.cfg, 'MIN_PATH_WIDTH', 4)))
        max_width = max(min_width, int(getattr(self.cfg, 'MAX_PATH_WIDTH', min_width + 4)))
        path = self._carve_main_path_smooth(height_field, min_width, max_width)

        # --- 3. Carve large, well-connected chambers ---
        chamber_count = max(2, int(getattr(self.cfg, 'CHAMBER_COUNT', int(self.complexity * 4))))
        chamber_radius_min = int(getattr(self.cfg, 'CHAMBER_RADIUS_MIN', min_width + 2))
        chamber_radius_max = int(getattr(self.cfg, 'CHAMBER_RADIUS_MAX', min_width + 8))
        chamber_radius_range = (chamber_radius_min, chamber_radius_max)
        chamber_centers = self._carve_chambers_connected(height_field, path, chamber_count, chamber_radius_range)

        # --- 4. Add organic branches ---
        branch_count = max(1, int(getattr(self.cfg, 'BRANCH_COUNT', int(self.complexity * 3))))
        self._carve_branches_smooth(height_field, path, branch_count, min_width)

        # --- 5. Place islands only in large open areas ---
        island_count = max(2, int(getattr(self.cfg, 'ISLAND_COUNT', int(self.complexity * 6))))
        self._place_islands_in_chambers(height_field, chamber_centers, island_count)

        # --- 6. Smoothing/dilation pass ---
        self._smooth_height_field(height_field, passes=2)

        # --- 7. Organic roughening ---
        if self.complexity > 0.3:
            self.add_organic_roughening(height_field, self.complexity * 0.5)

        # --- 8. Ensure all open space is connected ---
        height_field = self._connect_isolated_air_pockets(height_field)

        return height_field

    def _carve_main_path_smooth(self, height_field, min_width, max_width):
        import math
        import random
        path = []
        x, y = random.randint(2, self.grid_width // 6), random.randint(self.grid_height // 6, 5 * self.grid_height // 6)
        angle = rng.uniform(-math.pi, math.pi)
        visited = set()
        max_steps = int(self.grid_width * 3.5)  # Allow for more winding and looping
        for _ in range(max_steps):
            width = rng.randint(min_width, max_width)
            for dy in range(-width // 2, width // 2 + 1):
                for dx in range(-width // 3, width // 3 + 1):
                    nx, ny = x + dx, y + dy
                    if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                        height_field[ny][nx] = 0.0
                        visited.add((nx, ny))
            path.append((x, y))
            # --- Space-filling bias ---
            # Sample more directions and pick the one with the most unused space
            best_angle = angle
            best_score = -1
            for delta in [-1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2]:
                test_angle = angle + delta + rng.uniform(-0.15, 0.15)
                tx = int(x + math.cos(test_angle) * 10)
                ty = int(y + math.sin(test_angle) * 10)
                score = self._count_unvisited_space(height_field, tx, ty, radius=8)
                if score > best_score:
                    best_score = score
                    best_angle = test_angle
            # More aggressive winding and bouncing
            angle = best_angle + rng.uniform(-0.5, 0.5)
            step = rng.randint(4, 10)
            x += int(math.cos(angle) * step + rng.randint(-1, 2))
            y += int(math.sin(angle) * step + rng.randint(-2, 2))
            # Bounce off edges
            if x < 3:
                x = 3
                angle = math.pi - angle + rng.uniform(-0.5, 0.5)
            if x > self.grid_width - 4:
                x = self.grid_width - 4
                angle = math.pi - angle + rng.uniform(-0.5, 0.5)
            if y < 3:
                y = 3
                angle = -angle + rng.uniform(-0.5, 0.5)
            if y > self.grid_height - 4:
                y = self.grid_height - 4
                angle = -angle + rng.uniform(-0.5, 0.5)
            # Optionally, stop if we've covered enough area and are near the right edge
            if x >= self.grid_width - 6 and len(path) > self.grid_width:
                break
        return path

    def _count_unvisited_space(self, height_field, x, y, radius=8):
        # Count how many solid cells are in a radius (for space-filling bias)
        count = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    if height_field[ny][nx] > 0.5:
                        count += 1
        return count

    def _count_open_space(self, height_field, x, y, radius=7):
        # Count how many open cells are in a radius (for space-filling bias)
        open_count = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    if height_field[ny][nx] < 0.5:
                        open_count += 1
        return open_count

    def _carve_chambers_connected(self, height_field, path, chamber_count, radius_range):
        import random
        chamber_centers = []
        if len(path) < chamber_count:
            return chamber_centers
        chosen = random.sample(path[5:-5], chamber_count) if len(path) > 10 else path
        for (x, y) in chosen:
            radius = rng.randint(*radius_range)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        nx, ny = x + dx, y + dy
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            height_field[ny][nx] = 0.0
            chamber_centers.append((x, y, radius))
        return chamber_centers

    def _carve_branches_smooth(self, height_field, path, branch_count, min_width):
        import math
        import random
        if len(path) < 10:
            return
        for _ in range(branch_count):
            start = random.choice(path[5:-5])
            x, y = start
            angle = rng.uniform(-math.pi / 2, math.pi / 2)
            length = rng.randint(10, 22)
            for i in range(length):
                width = rng.randint(min_width, min_width + 2)
                for dy in range(-width // 2, width // 2 + 1):
                    for dx in range(-width // 3, width // 3 + 1):
                        nx, ny = int(x + dx), int(y + dy)
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            height_field[ny][nx] = 0.0
                # Smooth, gradual turns
                angle += rng.uniform(-0.18, 0.18)
                x += int(math.cos(angle) * 2)
                y += int(math.sin(angle) * 2)
                y = max(2, min(self.grid_height - 3, y))
                x = max(2, min(self.grid_width - 3, x))

    def _place_islands_in_chambers(self, height_field, chamber_centers, island_count):
        import random
        if not chamber_centers:
            return
        for _ in range(island_count):
            cx, cy, cr = random.choice(chamber_centers)
            irad = rng.randint(2, max(3, cr // 2))
            ox = rng.randint(-cr // 3, cr // 3)
            oy = rng.randint(-cr // 3, cr // 3)
            for dy in range(-irad, irad + 1):
                for dx in range(-irad, irad + 1):
                    if dx * dx + dy * dy <= irad * irad:
                        nx, ny = cx + ox + dx, cy + oy + dy
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            # Only place in open space (not in narrow corridors)
                            if self._is_large_open_area(height_field, nx, ny, irad):
                                height_field[ny][nx] = 1.0

    def _is_large_open_area(self, height_field, x, y, radius):
        # Check if a region is mostly open (for island placement)
        open_count = 0
        total = 0
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    total += 1
                    if height_field[ny][nx] < 0.5:
                        open_count += 1
        return open_count > total * 0.7

    def _smooth_height_field(self, height_field, passes=1):
        # Simple smoothing/dilation: fill small gaps and round corners
        for _ in range(passes):
            to_open = []
            for y in range(1, self.grid_height - 1):
                for x in range(1, self.grid_width - 1):
                    if height_field[y][x] > 0.5:
                        open_neighbors = 0
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if dx == 0 and dy == 0:
                                    continue
                                if height_field[y + dy][x + dx] < 0.5:
                                    open_neighbors += 1
                        if open_neighbors >= 5:
                            to_open.append((x, y))
            for (x, y) in to_open:
                height_field[y][x] = 0.0

    def _carve_main_path(self, height_field, min_width, max_width):
        """Carve a winding main path from left to right."""
        import math
        path = []
        x, y = 2, self.grid_height // 2
        angle = 0.0
        while x < self.grid_width - 2:
            width = rng.randint(min_width, max_width)
            # Carve at (x, y)
            for dy in range(-width // 2, width // 2 + 1):
                for dx in range(-width // 3, width // 3 + 1):
                    nx, ny = x + dx, y + dy
                    if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                        height_field[ny][nx] = 0.0
            path.append((x, y))
            # Randomly curve the path
            angle += rng.uniform(-0.5, 0.5)
            step = rng.randint(1, 2)
            x += int(math.cos(angle) * step + 1)
            y += int(math.sin(angle) * step)
            y = max(2, min(self.grid_height - 3, y))
        return path

    def _carve_chambers(self, height_field, path, chamber_count, radius_range):
        """Carve chambers at random points along the main path."""
        import random
        chamber_centers = []
        if len(path) < chamber_count:
            return chamber_centers
        chosen = random.sample(path[5:-5], chamber_count) if len(path) > 10 else path
        for (x, y) in chosen:
            radius = rng.randint(*radius_range)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        nx, ny = x + dx, y + dy
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            height_field[ny][nx] = 0.0
            chamber_centers.append((x, y, radius))
        return chamber_centers

    def _carve_branches(self, height_field, path, branch_count, min_width):
        """Carve branches off the main path, possibly dead-ending."""
        import math
        import random
        if len(path) < 10:
            return
        for _ in range(branch_count):
            start = random.choice(path[5:-5])
            x, y = start
            angle = rng.uniform(-math.pi / 2, math.pi / 2)
            length = rng.randint(8, 18)
            for i in range(length):
                width = rng.randint(min_width, min_width + 2)
                for dy in range(-width // 2, width // 2 + 1):
                    for dx in range(-width // 3, width // 3 + 1):
                        nx, ny = int(x + dx), int(y + dy)
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            height_field[ny][nx] = 0.0
                # Randomly curve
                angle += rng.uniform(-0.3, 0.3)
                x += int(math.cos(angle) * 1.5)
                y += int(math.sin(angle) * 1.5)
                y = max(2, min(self.grid_height - 3, y))
                x = max(2, min(self.grid_width - 3, x))

    def _place_islands(self, height_field, chamber_centers, island_count, min_width):
        """Place solid islands in chambers/corridors."""
        import random
        possible_centers = chamber_centers[:]
        # Add some random points along the main path for corridor islands
        if len(possible_centers) < island_count:
            possible_centers += [(x, y, min_width + 1) for (x, y, _) in random.sample(chamber_centers, min(len(chamber_centers), island_count - len(possible_centers)))]
        for _ in range(island_count):
            if not possible_centers:
                break
            cx, cy, cr = random.choice(possible_centers)
            # Place a small solid blob
            irad = rng.randint(2, max(3, cr // 2))
            ox = rng.randint(-cr // 3, cr // 3)
            oy = rng.randint(-cr // 3, cr // 3)
            for dy in range(-irad, irad + 1):
                for dx in range(-irad, irad + 1):
                    if dx * dx + dy * dy <= irad * irad:
                        nx, ny = cx + ox + dx, cy + oy + dy
                        if 1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1:
                            height_field[ny][nx] = 1.0
    
    def _create_base_solid_terrain(self) -> np.ndarray:
        """Create base terrain that's mostly solid with some natural variation"""
        height_field = np.ones((self.grid_height, self.grid_width), dtype=np.float32)
        
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
    
    def _ensure_basic_connectivity(self, height_field: np.ndarray) -> np.ndarray:
        """Ensure there's good connectivity with variety in patterns"""
        # Randomly choose connectivity pattern to avoid the repetitive cross
        connectivity_pattern = rng.random_float()
        
        if connectivity_pattern < 0.3:
            # No cross pattern - rely on natural caves and flow channels
            pass
        elif connectivity_pattern < 0.6:
            # Create horizontal corridor only (wider)
            self._create_horizontal_corridor(height_field)
        elif connectivity_pattern < 0.8:
            # Create vertical corridor only (wider) 
            self._create_vertical_corridor(height_field)
        else:
            # Create the cross pattern but with much wider channels
            self._create_cross_pattern(height_field)
        
        # Remove small isolated solid areas (clean up terrain)
        height_field = self._remove_small_islands(height_field)
        
        # Connect isolated air pockets to main air space
        height_field = self._connect_isolated_air_pockets(height_field)
        
        return height_field
    
    def _create_horizontal_corridor(self, height_field: np.ndarray):
        """Create a single horizontal corridor with gentle curves"""
        mid_y = self.grid_height // 2
        
        for x in range(self.grid_width):
            # Use gentler noise for subtle curves
            curve_noise = NoiseGenerator.perlin_noise_2d(x, 0, 0.06) * 4
            y = int(mid_y + curve_noise)
            y = max(4, min(self.grid_height - 5, y))
            
            # Much wider corridor (increased from 4 to 8-12)
            corridor_width = rng.randint(8, 12)
            
            # Carve clean corridor
            for dy in range(-corridor_width//2, corridor_width//2 + 1):
                corridor_y = y + dy
                if 0 <= corridor_y < self.grid_height:
                    height_field[corridor_y][x] = 0.0
    
    def _create_vertical_corridor(self, height_field: np.ndarray):
        """Create a single vertical corridor with gentle curves"""
        mid_x = self.grid_width // 2
        
        for y in range(self.grid_height):
            # Gentle horizontal variation
            curve_noise = NoiseGenerator.perlin_noise_2d(0, y, 0.08) * 3
            connector_x = int(mid_x + curve_noise)
            connector_x = max(4, min(self.grid_width - 5, connector_x))
            
            # Much wider vertical corridor (increased from 2 to 6-10)
            width = rng.randint(6, 10)
            for dx in range(-width//2, width//2 + 1):
                final_x = connector_x + dx
                if 0 <= final_x < self.grid_width:
                    height_field[y][final_x] = 0.0
    
    def _create_cross_pattern(self, height_field: np.ndarray):
        """Create the traditional cross pattern but with wider channels"""
        # Create wider horizontal corridor
        mid_y = self.grid_height // 2
        
        for x in range(self.grid_width):
            curve_noise = NoiseGenerator.perlin_noise_2d(x, 0, 0.06) * 4
            y = int(mid_y + curve_noise)
            y = max(4, min(self.grid_height - 5, y))
            
            # Much wider corridor (increased from 4 to 8-12)
            corridor_width = rng.randint(8, 12)
            
            for dy in range(-corridor_width//2, corridor_width//2 + 1):
                corridor_y = y + dy
                if 0 <= corridor_y < self.grid_height:
                    height_field[corridor_y][x] = 0.0
        
        # Create wider vertical connector
        mid_x = self.grid_width // 2
        for y in range(self.grid_height):
            curve_noise = NoiseGenerator.perlin_noise_2d(0, y, 0.08) * 3
            connector_x = int(mid_x + curve_noise)
            connector_x = max(4, min(self.grid_width - 5, connector_x))
            
            # Much wider vertical connector (increased from 2 to 6-10)
            width = rng.randint(6, 10)
            for dx in range(-width//2, width//2 + 1):
                final_x = connector_x + dx
                if 0 <= final_x < self.grid_width:
                    height_field[y][final_x] = 0.0

    def _remove_small_islands(self, height_field: np.ndarray) -> np.ndarray:
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
    
    def _generate_border_only(self) -> np.ndarray:
        """Generate terrain with only solid borders"""
        height_field = np.zeros((self.grid_height, self.grid_width), dtype=np.float32)
        self.carver.create_solid_borders(height_field)
        return height_field
    
    def add_organic_roughening(self, height_field: np.ndarray, complexity: float):
        """Add organic roughening to remove straight lines and add natural features"""
        # Add small outcroppings and inlets to terrain edges
        self._add_edge_roughening(height_field, complexity)
        
        # Add natural texture to large open areas
        self._add_area_texture(height_field, complexity)
        
        # Add small natural features
        self._add_micro_features(height_field, complexity)
    
    def _add_edge_roughening(self, height_field: np.ndarray, complexity: float):
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
    
    def _add_area_texture(self, height_field: np.ndarray, complexity: float):
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
    
    def _add_micro_features(self, height_field: np.ndarray, complexity: float):
        """Add very few small natural features"""
        num_features = int(complexity * self.grid_width * self.grid_height * 0.002)  # Much fewer
        
        for _ in range(num_features):
            x = rng.randint(5, self.grid_width - 6)
            y = rng.randint(5, self.grid_height - 6)
            
            # Only add tiny chambers, no protrusions
            feature_type = rng.random_float()
            if feature_type < 0.7:  # Mostly chambers
                self._add_tiny_chamber(height_field, x, y)
    
    def _add_tiny_chamber(self, height_field: np.ndarray, center_x: int, center_y: int):
        """Add a tiny natural chamber"""
        radius = rng.randint(1, 3)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:  # Diamond shape
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        height_field[y][x] = 0.0
    
    def _add_tiny_protrusion(self, height_field: np.ndarray, center_x: int, center_y: int):
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
    
    def _connect_isolated_air_pockets(self, height_field: np.ndarray) -> np.ndarray:
        """Connect isolated air pockets to the main air space using flood fill"""
        # Find all connected air regions using flood fill
        visited = [[False for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        air_regions = []
        
        # Find all air regions
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if height_field[y][x] < 0.5 and not visited[y][x]:  # Open space, not visited
                    region = self._flood_fill_air_region(height_field, visited, x, y)
                    if region:
                        air_regions.append(region)
        
        if len(air_regions) <= 1:
            return height_field  # No isolated pockets or no air at all
        
        # Find the largest air region (main air space)
        largest_region = max(air_regions, key=len)
        
        # Connect smaller regions to the largest one
        for region in air_regions:
            if region != largest_region and len(region) > 2:  # Don't connect tiny 1-2 cell pockets
                self._create_connection_to_main_air(height_field, region, largest_region)
        
        return height_field
    
    def _flood_fill_air_region(self, height_field: np.ndarray, visited: List[List[bool]], 
                              start_x: int, start_y: int) -> List[Tuple[int, int]]:
        """Use flood fill to find all connected air cells starting from a point"""
        if (start_x < 0 or start_x >= self.grid_width or 
            start_y < 0 or start_y >= self.grid_height or
            visited[start_y][start_x] or height_field[start_y][start_x] >= 0.5):
            return []
        
        region = []
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if (x < 0 or x >= self.grid_width or 
                y < 0 or y >= self.grid_height or
                visited[y][x] or height_field[y][x] >= 0.5):
                continue
                
            visited[y][x] = True
            region.append((x, y))
            
            # Add neighbors to stack
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))
        
        return region
    
    def _create_connection_to_main_air(self, height_field: np.ndarray, 
                                     isolated_region: List[Tuple[int, int]], 
                                     main_region: List[Tuple[int, int]]):
        """Create a connection from an isolated air pocket to the main air space"""
        if not isolated_region or not main_region:
            return
        
        # Find the closest point between the two regions
        min_distance = float('inf')
        best_isolated_point = None
        best_main_point = None
        
        # Sample a subset of points to avoid performance issues with large regions
        isolated_sample = isolated_region[::max(1, len(isolated_region) // 20)]
        main_sample = main_region[::max(1, len(main_region) // 20)]
        
        for iso_x, iso_y in isolated_sample:
            for main_x, main_y in main_sample:
                distance = ((iso_x - main_x) ** 2 + (iso_y - main_y) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    best_isolated_point = (iso_x, iso_y)
                    best_main_point = (main_x, main_y)
        
        if best_isolated_point and best_main_point:
            # Create a tunnel between the two points
            self._carve_connection_tunnel(height_field, best_isolated_point, best_main_point)
    
    def _carve_connection_tunnel(self, height_field: np.ndarray, 
                                start: Tuple[int, int], end: Tuple[int, int]):
        """Carve a narrow tunnel to connect two air regions"""
        start_x, start_y = start
        end_x, end_y = end
        
        # Use simple line interpolation to create the tunnel
        distance = max(abs(end_x - start_x), abs(end_y - start_y))
        if distance == 0:
            return
        
        tunnel_width = 2  # Narrow tunnel width
        
        for i in range(distance + 1):
            t = i / distance
            x = int(start_x + t * (end_x - start_x))
            y = int(start_y + t * (end_y - start_y))
            
            # Carve tunnel with some width
            for dx in range(-tunnel_width, tunnel_width + 1):
                for dy in range(-tunnel_width, tunnel_width + 1):
                    tunnel_x = x + dx
                    tunnel_y = y + dy
                    
                    if (0 <= tunnel_x < self.grid_width and 
                        0 <= tunnel_y < self.grid_height and
                        abs(dx) + abs(dy) <= tunnel_width):  # Diamond shape
                        height_field[tunnel_y][tunnel_x] = 0.0
