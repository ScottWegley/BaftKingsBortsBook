"""
Fast terrain zone validator with optimized algorithms.
"""

from typing import List, Optional, Tuple
import math
import rng
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
from .base import Zone


class TerrainZoneValidator:
    """Validates terrain for game mode requirements with fast algorithms"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
    
    def validate_indiv_race_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Fast validation for individual race mode with optimized zone placement.
        """
        if not terrain_obstacles:
            return None
            
        terrain = terrain_obstacles[0]        
        cfg = get_config()
        marble_radius = cfg.simulation.MARBLE_RADIUS
        min_path_width = marble_radius * 1.5  # 1.5x marble diameter clearance
        
        # Fast zone placement - try strategic positions first, then refine
        zones = self._find_zones_fast(terrain, marble_radius, min_path_width)
        if zones:
            spawn_zone, goal_zone = zones
            # Quick path validation
            if self._validate_path_fast(terrain, spawn_zone, goal_zone, min_path_width):
                return spawn_zone, goal_zone
            
        return None

    def _find_zones_fast(self, terrain: FlowingTerrainObstacle, marble_radius: float, min_path_width: float) -> Optional[Tuple[Zone, Zone]]:
        """
        Fast zone placement using strategic positions and minimal search.
        Places zones as far apart as possible for optimal racing.
        """
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        min_edge_distance = max(spawn_zone_radius, goal_zone_radius) + 20
        
        # Strategic corner positions for maximum distance
        corner_positions = [
            (min_edge_distance, min_edge_distance),  # Top-left
            (self.arena_width - min_edge_distance, min_edge_distance),  # Top-right
            (min_edge_distance, self.arena_height - min_edge_distance),  # Bottom-left
            (self.arena_width - min_edge_distance, self.arena_height - min_edge_distance),  # Bottom-right
        ]
        
        # Try all corner combinations and pick the pair with maximum distance
        best_distance = 0
        best_zones = None
        
        for i, spawn_pos in enumerate(corner_positions):
            if not self._is_position_valid(terrain, spawn_pos[0], spawn_pos[1], spawn_zone_radius, marble_radius):
                continue
                
            spawn_zone = Zone(spawn_pos[0], spawn_pos[1], spawn_zone_radius, "spawn")
            
            # Try all other corners as goal positions
            for j, goal_pos in enumerate(corner_positions):
                if i == j:  # Skip same position
                    continue
                    
                distance = math.sqrt((goal_pos[0] - spawn_pos[0])**2 + (goal_pos[1] - spawn_pos[1])**2)
                
                # Only consider positions that are farther than current best
                if distance <= best_distance:
                    continue
                    
                if not self._is_position_valid(terrain, goal_pos[0], goal_pos[1], goal_zone_radius, marble_radius):
                    continue
                    
                goal_zone = Zone(goal_pos[0], goal_pos[1], goal_zone_radius, "goal")
                
                # Quick path check
                if self._validate_path_fast(terrain, spawn_zone, goal_zone, min_path_width):
                    best_distance = distance
                    best_zones = (spawn_zone, goal_zone)
        
        # If corners don't work, try edge positions
        if not best_zones:
            best_zones = self._try_edge_positions(terrain, marble_radius, min_path_width)
        
        return best_zones

    def _try_edge_positions(self, terrain: FlowingTerrainObstacle, marble_radius: float, min_path_width: float) -> Optional[Tuple[Zone, Zone]]:
        """Try positions along edges if corners don't work, prioritizing maximum distance"""
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        edge_buffer = max(spawn_zone_radius, goal_zone_radius) + 20
        
        # Top edge positions
        top_positions = [
            (self.arena_width * 0.25, edge_buffer),
            (self.arena_width * 0.5, edge_buffer),
            (self.arena_width * 0.75, edge_buffer)
        ]
        
        # Bottom edge positions
        bottom_positions = [
            (self.arena_width * 0.25, self.arena_height - edge_buffer),
            (self.arena_width * 0.5, self.arena_height - edge_buffer),
            (self.arena_width * 0.75, self.arena_height - edge_buffer)
        ]
        
        # Left edge positions
        left_positions = [
            (edge_buffer, self.arena_height * 0.25),
            (edge_buffer, self.arena_height * 0.5),
            (edge_buffer, self.arena_height * 0.75)
        ]
        
        # Right edge positions
        right_positions = [
            (self.arena_width - edge_buffer, self.arena_height * 0.25),
            (self.arena_width - edge_buffer, self.arena_height * 0.5),
            (self.arena_width - edge_buffer, self.arena_height * 0.75)
        ]
        
        # Try opposite sides for maximum distance
        opposite_pairs = [
            (top_positions, bottom_positions),     # Top vs Bottom
            (left_positions, right_positions),     # Left vs Right
        ]
        
        best_distance = 0
        best_zones = None
        
        for spawn_positions, goal_positions in opposite_pairs:
            for spawn_pos in spawn_positions:
                if not self._is_position_valid(terrain, spawn_pos[0], spawn_pos[1], spawn_zone_radius, marble_radius):
                    continue
                    
                for goal_pos in goal_positions:
                    if not self._is_position_valid(terrain, goal_pos[0], goal_pos[1], goal_zone_radius, marble_radius):
                        continue
                    
                    distance = math.sqrt((goal_pos[0] - spawn_pos[0])**2 + (goal_pos[1] - spawn_pos[1])**2)
                    
                    if distance <= best_distance:
                        continue
                        
                    spawn_zone = Zone(spawn_pos[0], spawn_pos[1], spawn_zone_radius, "spawn")
                    goal_zone = Zone(goal_pos[0], goal_pos[1], goal_zone_radius, "goal")
                    
                    if self._validate_path_fast(terrain, spawn_zone, goal_zone, min_path_width):
                        best_distance = distance
                        best_zones = (spawn_zone, goal_zone)
        
        return best_zones
    
    def _is_position_valid(self, terrain: FlowingTerrainObstacle, x: float, y: float, zone_radius: float, marble_radius: float) -> bool:
        """Fast position validation with minimal checks"""
        # Bounds check
        if (x - zone_radius < 0 or x + zone_radius >= self.arena_width or 
            y - zone_radius < 0 or y + zone_radius >= self.arena_height):
            return False
        
        # Quick terrain collision check - only check center and a few key points
        test_points = [
            (x, y),  # Center
            (x - zone_radius * 0.5, y),  # Left
            (x + zone_radius * 0.5, y),  # Right
            (x, y - zone_radius * 0.5),  # Top
            (x, y + zone_radius * 0.5),  # Bottom
        ]
        
        for test_x, test_y in test_points:
            if terrain.check_collision(test_x, test_y, marble_radius):
                return False
        
        return True
    
    def _validate_path_fast(self, terrain: FlowingTerrainObstacle, spawn_zone: Zone, goal_zone: Zone, min_width: float) -> bool:
        """
        Very fast path validation using straight-line check with sampling.
        """
        # Simple straight-line path check with sampling
        start_x, start_y = spawn_zone.center_x, spawn_zone.center_y
        end_x, end_y = goal_zone.center_x, goal_zone.center_y
        
        # Calculate path vector
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return False
        
        # Normalize direction
        dx /= distance
        dy /= distance
        
        # Sample points along the path
        step_size = min_width  # Use path width as step size
        num_steps = int(distance / step_size)
        
        for i in range(1, num_steps):  # Skip start and end points
            sample_x = start_x + dx * i * step_size
            sample_y = start_y + dy * i * step_size
            
            # Check if path is clear at this point
            if terrain.check_collision(sample_x, sample_y, min_width / 2):
                return False
        
        return True
