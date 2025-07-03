"""
Game mode specific logic for handling different race types and win conditions.

This module contains zone detection, path validation, and game state management
for different game modes like individual races, team races, etc.
"""

from typing import List, Tuple, Optional, Set
from enum import Enum
import math
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
import rng


class GameResult(Enum):
    """Possible game results"""
    ONGOING = "ongoing"
    WINNER = "winner"
    DRAW = "draw"
    ERROR = "error"


class Zone:
    """Represents a zone on the terrain (spawn, goal, etc.)"""
    
    def __init__(self, center_x: float, center_y: float, radius: float, zone_type: str):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.zone_type = zone_type  # "spawn", "goal", etc.
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this zone"""
        distance = math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
        return distance <= self.radius
    
    def get_random_position_in_zone(self) -> Tuple[float, float]:
        """Get a random position within this zone"""
        # Generate random point in circle
        angle = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(0, self.radius * 0.9)  # Stay slightly inside the zone
        
        x = self.center_x + radius * math.cos(angle)
        y = self.center_y + radius * math.sin(angle)
        
        return x, y


class TerrainZoneValidator:
    """Validates terrain for game mode requirements"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
    
    def validate_indiv_race_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Validate terrain for individual race mode and return spawn/goal zones if valid.
        
        Returns:
            Tuple of (spawn_zone, goal_zone) if valid, None if invalid
        """
        if not terrain_obstacles:
            return None
            
        terrain = terrain_obstacles[0]  # Assuming single terrain obstacle
        cfg = get_config()
        marble_radius = cfg.simulation.MARBLE_RADIUS
        min_path_width = marble_radius * 2  # Minimum path width requirement
        
        # Find potential spawn and goal zones
        spawn_zone = self._find_best_spawn_zone(terrain, marble_radius)
        if not spawn_zone:
            return None
            
        goal_zone = self._find_best_goal_zone(terrain, spawn_zone, marble_radius)
        if not goal_zone:
            return None
            
        # Validate path exists between zones
        if self._validate_path_exists(terrain, spawn_zone, goal_zone, min_path_width):
            return spawn_zone, goal_zone
            
        return None
    
    def _find_best_spawn_zone(self, terrain: FlowingTerrainObstacle, marble_radius: float) -> Optional[Zone]:
        """Find the best spawn zone in the terrain"""
        # Try corners and edges first for spawn zones
        candidates = [
            (self.arena_width * 0.1, self.arena_height * 0.1),  # Top-left
            (self.arena_width * 0.9, self.arena_height * 0.1),  # Top-right
            (self.arena_width * 0.1, self.arena_height * 0.9),  # Bottom-left
            (self.arena_width * 0.9, self.arena_height * 0.9),  # Bottom-right
            (self.arena_width * 0.5, self.arena_height * 0.1),  # Top-center
            (self.arena_width * 0.5, self.arena_height * 0.9),  # Bottom-center
            (self.arena_width * 0.1, self.arena_height * 0.5),  # Left-center
            (self.arena_width * 0.9, self.arena_height * 0.5),  # Right-center
        ]
        
        zone_radius = marble_radius * 4  # Zone should fit multiple marbles
        
        for x, y in candidates:
            if self._is_valid_zone_location(terrain, x, y, zone_radius, marble_radius):
                return Zone(x, y, zone_radius, "spawn")
        
        return None
    
    def _find_best_goal_zone(self, terrain: FlowingTerrainObstacle, spawn_zone: Zone, marble_radius: float) -> Optional[Zone]:
        """Find the best goal zone, prioritizing distance from spawn"""
        candidates = [
            (self.arena_width * 0.1, self.arena_height * 0.1),  # Top-left
            (self.arena_width * 0.9, self.arena_height * 0.1),  # Top-right
            (self.arena_width * 0.1, self.arena_height * 0.9),  # Bottom-left
            (self.arena_width * 0.9, self.arena_height * 0.9),  # Bottom-right
            (self.arena_width * 0.5, self.arena_height * 0.1),  # Top-center
            (self.arena_width * 0.5, self.arena_height * 0.9),  # Bottom-center
            (self.arena_width * 0.1, self.arena_height * 0.5),  # Left-center
            (self.arena_width * 0.9, self.arena_height * 0.5),  # Right-center
        ]
        
        zone_radius = marble_radius * 3  # Goal zone can be smaller
        best_candidate = None
        max_distance = 0
        
        for x, y in candidates:
            # Skip if too close to spawn zone
            distance_to_spawn = math.sqrt((x - spawn_zone.center_x) ** 2 + (y - spawn_zone.center_y) ** 2)
            if distance_to_spawn < self.arena_width * 0.3:  # Must be at least 30% of arena width away
                continue
                
            if self._is_valid_zone_location(terrain, x, y, zone_radius, marble_radius):
                if distance_to_spawn > max_distance:
                    max_distance = distance_to_spawn
                    best_candidate = (x, y)
        
        if best_candidate:
            return Zone(best_candidate[0], best_candidate[1], zone_radius, "goal")
        
        return None
    
    def _is_valid_zone_location(self, terrain: FlowingTerrainObstacle, x: float, y: float, zone_radius: float, marble_radius: float) -> bool:
        """Check if a location is valid for placing a zone"""
        # Check several points within the zone to ensure it's clear
        test_points = 8
        for i in range(test_points):
            angle = (2 * math.pi * i) / test_points
            test_x = x + (zone_radius * 0.7) * math.cos(angle)  # Check points within zone
            test_y = y + (zone_radius * 0.7) * math.sin(angle)
            
            # Check bounds
            if test_x < marble_radius or test_x >= self.arena_width - marble_radius:
                return False
            if test_y < marble_radius or test_y >= self.arena_height - marble_radius:
                return False
                
            # Check collision with terrain
            if terrain.check_collision(test_x, test_y, marble_radius):
                return False
        
        return True
    
    def _validate_path_exists(self, terrain: FlowingTerrainObstacle, spawn_zone: Zone, goal_zone: Zone, min_width: float) -> bool:
        """Use A* pathfinding to validate a path exists between zones"""
        # Simple flood fill approach - more sophisticated pathfinding could be added
        # This is a basic implementation that checks if zones are connected
        
        # Start from spawn zone center
        start_x, start_y = int(spawn_zone.center_x), int(spawn_zone.center_y)
        goal_x, goal_y = int(goal_zone.center_x), int(goal_zone.center_y)
        
        # Use a simple grid-based flood fill
        grid_resolution = int(min_width / 2)  # Grid size based on required path width
        grid_width = self.arena_width // grid_resolution
        grid_height = self.arena_height // grid_resolution
        
        visited = set()
        queue = [(start_x // grid_resolution, start_y // grid_resolution)]
        
        while queue:
            gx, gy = queue.pop(0)
            
            if (gx, gy) in visited:
                continue
                
            visited.add((gx, gy))
            
            # Check if we reached the goal zone
            world_x = gx * grid_resolution
            world_y = gy * grid_resolution
            if goal_zone.contains_point(world_x, world_y):
                return True
            
            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = gx + dx, gy + dy
                
                if 0 <= nx < grid_width and 0 <= ny < grid_height and (nx, ny) not in visited:
                    # Check if this grid cell is passable
                    world_nx = nx * grid_resolution
                    world_ny = ny * grid_resolution
                    
                    if self._is_grid_cell_passable(terrain, world_nx, world_ny, grid_resolution, min_width):
                        queue.append((nx, ny))
        
        return False
    
    def _is_grid_cell_passable(self, terrain: FlowingTerrainObstacle, x: float, y: float, cell_size: float, min_width: float) -> bool:
        """Check if a grid cell is passable (no terrain collision)"""
        # Check center and corners of grid cell
        test_points = [
            (x, y),
            (x + cell_size, y),
            (x, y + cell_size),
            (x + cell_size, y + cell_size),
            (x + cell_size/2, y + cell_size/2)  # Center
        ]
        
        for test_x, test_y in test_points:
            if test_x >= self.arena_width or test_y >= self.arena_height:
                return False
            if terrain.check_collision(test_x, test_y, min_width / 4):  # Small radius for pathfinding
                return False
        
        return True


class IndivRaceGameMode:
    """Individual race game mode logic"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.spawn_zone: Optional[Zone] = None
        self.goal_zone: Optional[Zone] = None
        self.winner_marble_id: Optional[int] = None
        self.validator = TerrainZoneValidator(arena_width, arena_height)
    
    def validate_and_setup_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> bool:
        """
        Validate terrain and set up zones for individual race mode.
        
        Returns:
            True if terrain is valid and zones are set up, False otherwise
        """
        zones = self.validator.validate_indiv_race_terrain(terrain_obstacles)
        if zones:
            self.spawn_zone, self.goal_zone = zones
            return True
        return False
    
    def get_spawn_positions(self, num_marbles: int, marble_radius: float) -> List[Tuple[float, float]]:
        """Get spawn positions for marbles in the spawn zone"""
        if not self.spawn_zone:
            raise ValueError("Spawn zone not set up. Call validate_and_setup_terrain first.")
        
        positions = []
        max_attempts = 100
        
        for i in range(num_marbles):
            for attempt in range(max_attempts):
                x, y = self.spawn_zone.get_random_position_in_zone()
                
                # Check if position is valid (not overlapping with other marbles)
                valid = True
                for prev_x, prev_y in positions:
                    distance = math.sqrt((x - prev_x) ** 2 + (y - prev_y) ** 2)
                    if distance < marble_radius * 2.5:  # Minimum separation
                        valid = False
                        break
                
                if valid:
                    positions.append((x, y))
                    break
            else:
                # If we couldn't find a valid position, place it at zone center with offset
                angle = (2 * math.pi * i) / num_marbles
                offset = marble_radius * 2
                x = self.spawn_zone.center_x + offset * math.cos(angle)
                y = self.spawn_zone.center_y + offset * math.sin(angle)
                positions.append((x, y))
        
        return positions
    
    def check_win_condition(self, marbles) -> Tuple[GameResult, Optional[int]]:
        """
        Check if any marble has reached the goal zone.
        
        Returns:
            Tuple of (result, winner_id) where winner_id is the marble index if there's a winner
        """
        if not self.goal_zone:
            return GameResult.ERROR, None
        
        for i, marble in enumerate(marbles):
            if self.goal_zone.contains_point(marble.x, marble.y):
                self.winner_marble_id = i
                return GameResult.WINNER, i
        
        return GameResult.ONGOING, None
    
    def get_zones(self) -> Tuple[Optional[Zone], Optional[Zone]]:
        """Get the spawn and goal zones"""
        return self.spawn_zone, self.goal_zone
