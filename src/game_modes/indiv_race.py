"""
Individual race game mode implementation.
"""

from typing import List, Tuple, Optional
import math
from .base import GameResult, Zone
from .simple_terrain_validator import SimpleTerrainZoneValidator
from terrain.obstacle import FlowingTerrainObstacle
import rng


class IndivRaceGameMode:
    """Individual race game mode logic with optimized zone placement"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.spawn_zone: Optional[Zone] = None
        self.goal_zone: Optional[Zone] = None
        self.winner_marble_id: Optional[int] = None
        self.validator = SimpleTerrainZoneValidator(arena_width, arena_height)
    
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
        max_attempts = 50  # Reduced for speed
        
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
