"""
Main simulation manager that orchestrates all simulation components.
"""

from typing import List, Optional, Tuple
import math
from config import get_config
from terrain import FlowingTerrainGenerator
from physics import Marble
from physics.pymunk_collision import CollisionDetector
from game_modes import IndivRaceGameMode, GameResult
from .marble_factory import MarbleFactory


class SimulationManager:
    """Manages the entire marble simulation including marbles, terrain, and physics"""
    
    def __init__(self, game_mode: str = None):
        cfg = get_config()
        
        # Read all parameters from config (including runtime overrides)
        self.num_marbles = cfg.simulation.NUM_MARBLES
        self.arena_width = cfg.simulation.ARENA_WIDTH
        self.arena_height = cfg.simulation.ARENA_HEIGHT
        self.marble_radius = cfg.simulation.MARBLE_RADIUS
        self.marble_speed = cfg.simulation.MARBLE_SPEED
        
        # Terrain settings
        self.terrain_complexity = cfg.simulation.TERRAIN_COMPLEXITY
        self.game_mode = game_mode or cfg.simulation.DEFAULT_GAME_MODE
        
        self.simulation_time = 0.0
        self.game_finished = False
        self.winner_marble_id = None
        
        # Initialize game mode handler
        if self.game_mode == "indiv_race":
            self.game_mode_handler = IndivRaceGameMode(self.arena_width, self.arena_height)
        else:
            raise ValueError(f"Unsupported game mode: {self.game_mode}")
        
        # Generate terrain with validation
        self._generate_valid_terrain(self.terrain_complexity)
        
        # Generate distinct colors for each marble
        self.colors = MarbleFactory.generate_colors(self.num_marbles)        
        # Initialize marbles using game mode specific spawn positions
        self._initialize_marbles()
    
    def _generate_valid_terrain(self, terrain_complexity: float, max_attempts: int = 50):
        """Generate terrain that meets game mode requirements"""
        self.terrain_generator = FlowingTerrainGenerator(self.arena_width, self.arena_height)
        
        # To ensure determinism, we need to consume the same amount of RNG regardless of terrain validation
        # So we generate all terrains first, then validate them
        terrain_candidates = []
        
        # Generate all terrain candidates first (fixed RNG consumption)
        for attempt in range(max_attempts):
            # Create a new generator for each attempt to ensure consistent state
            temp_generator = FlowingTerrainGenerator(self.arena_width, self.arena_height)
            terrain_obstacles = temp_generator.generate_terrain(terrain_complexity)
            terrain_candidates.append((temp_generator, terrain_obstacles))
        
        # Now validate candidates in order (deterministic)
        for attempt, (generator, obstacles) in enumerate(terrain_candidates):
            if self.game_mode_handler.validate_and_setup_terrain(obstacles):
                print(f"Valid terrain generated on attempt {attempt + 1}")
                self.terrain_generator = generator
                self.terrain_obstacles = obstacles
                return
        
        # If we get here, we couldn't generate valid terrain
        raise RuntimeError(f"Could not generate valid terrain for {self.game_mode} mode after {max_attempts} attempts")
    
    def _initialize_marbles(self):
        """Initialize marbles using game mode specific positioning"""
        if self.game_mode == "indiv_race":
            # Get spawn positions from game mode handler
            spawn_positions = self.game_mode_handler.get_spawn_positions(self.num_marbles, self.marble_radius)            # Create marbles at spawn positions with deterministic initial directions
            self.marbles: List[Marble] = []
            for i, (x, y) in enumerate(spawn_positions):
                # Use a deterministic angle based on marble index
                initial_angle = (2 * math.pi * i) / self.num_marbles
                marble = Marble(x, y, self.marble_radius, self.colors[i], self.marble_speed, initial_angle)
                self.marbles.append(marble)
        else:
            # Fallback to old method for other modes
            self.marbles: List[Marble] = MarbleFactory.create_marbles(
                self.num_marbles, self.marble_radius, self.marble_speed,
                self.arena_width, self.arena_height, self.terrain_obstacles, self.colors
            )
    
    def update(self, dt: float):
        """Update simulation state"""
        if self.game_finished:
            return
            
        self.simulation_time += dt
        
        # Update all marble positions
        for marble in self.marbles:
            marble.update(dt)
        
        # Handle all collisions centrally for better control and accuracy
        # First handle terrain and boundary collisions
        CollisionDetector.detect_and_resolve_terrain_collisions(
            self.marbles, self.terrain_obstacles, self.arena_width, self.arena_height
        )
        
        # Then handle marble-to-marble collisions
        CollisionDetector.detect_and_resolve_marble_collisions(self.marbles)
          # Check win condition
        result, winner_id = self.game_mode_handler.check_win_condition(self.marbles)
        if result == GameResult.WINNER:
            self.game_finished = True
            self.winner_marble_id = winner_id
            print(f"Marble {winner_id} wins the race!")
    
    def is_finished(self) -> bool:
        """Check if simulation should end"""
        return self.game_finished
    
    def get_winner(self) -> Optional[int]:
        """Get the winner marble ID if game is finished"""
        return self.winner_marble_id
    
    def get_zones(self) -> Tuple:
        """Get game mode zones for rendering"""
        if hasattr(self.game_mode_handler, 'get_zones'):
            return self.game_mode_handler.get_zones()
        return None, None
