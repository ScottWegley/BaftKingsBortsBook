"""
Simple terrain zone validator - clean slate approach.
Focus on basic requirements: two zones far apart with clear path.
"""

from typing import List, Optional, Tuple
import math
import rng
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
from .base import Zone


class SimpleTerrainZoneValidator:
    """Simple, reliable terrain validator with minimal complexity"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
    
    def validate_indiv_race_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Simplified validation: find any two valid positions for zones.
        """
        if not terrain_obstacles:
            return None
            
        terrain = terrain_obstacles[0]        
        cfg = get_config()
        marble_radius = cfg.simulation.MARBLE_RADIUS
        
        # Zone sizes
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        
        # Just try to find any two valid positions
        zones = self._find_any_valid_zones(terrain, spawn_zone_radius, goal_zone_radius, marble_radius)
        return zones


    def _find_any_valid_zones(self, terrain: FlowingTerrainObstacle, spawn_radius: float, goal_radius: float, marble_radius: float) -> Optional[Tuple[Zone, Zone]]:
        """Find any two valid positions for zones - simplified approach"""
        buffer = max(spawn_radius, goal_radius) + 20
        max_attempts = 500
        
        # Find first valid spawn position
        spawn_zone = None
        for _ in range(max_attempts):
            spawn_x = rng.uniform(buffer, self.arena_width - buffer)
            spawn_y = rng.uniform(buffer, self.arena_height - buffer)
            
            if self._is_position_clear(terrain, spawn_x, spawn_y, spawn_radius, marble_radius):
                spawn_zone = Zone(spawn_x, spawn_y, spawn_radius, "spawn")
                break
        
        if not spawn_zone:
            return None
        
        # Find any valid goal position 
        for _ in range(max_attempts):
            goal_x = rng.uniform(buffer, self.arena_width - buffer)
            goal_y = rng.uniform(buffer, self.arena_height - buffer)
            
            # Simple distance check to avoid placing them too close
            distance = math.sqrt((goal_x - spawn_zone.center_x)**2 + (goal_y - spawn_zone.center_y)**2)
            min_distance = min(self.arena_width, self.arena_height) * 0.2  # At least 20% of smaller dimension
            
            if distance >= min_distance and self._is_position_clear(terrain, goal_x, goal_y, goal_radius, marble_radius):
                goal_zone = Zone(goal_x, goal_y, goal_radius, "goal")
                return (spawn_zone, goal_zone)
        
        return None

    def _is_position_clear(self, terrain: FlowingTerrainObstacle, x: float, y: float, zone_radius: float, marble_radius: float) -> bool:
        """Check if a position is clear for a zone"""
        # Check bounds
        if (x - zone_radius < 0 or x + zone_radius >= self.arena_width or 
            y - zone_radius < 0 or y + zone_radius >= self.arena_height):
            return False
        
        # Check center and a few points around the zone
        test_points = [
            (x, y),  # Center
            (x - zone_radius * 0.7, y),  # Left
            (x + zone_radius * 0.7, y),  # Right
            (x, y - zone_radius * 0.7),  # Top
            (x, y + zone_radius * 0.7),  # Bottom
        ]
        
        for test_x, test_y in test_points:
            if terrain.check_collision(test_x, test_y, marble_radius):
                return False
        
        return True