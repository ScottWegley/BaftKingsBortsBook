"""
Global configuration for the marble race simulation.

This module contains all configurable parameters for the simulation, terrain generation,
and rendering. Different game modes can have their own specific configurations.
"""

from typing import Dict, Any, Tuple
import os
from rng import RNGMode


class RNGConfig:
    """Configuration for random number generation - Global across all game modes"""
    
    # Default RNG settings
    DEFAULT_RNG_MODE = RNGMode.DATE
    DEFAULT_RNG_VALUE = None


class SimulationConfig:
    """Base configuration for marble simulation physics and behavior"""
    
    # Simulation parameters
    DEFAULT_NUM_MARBLES = 8
    DEFAULT_GAME_MODE = "indiv_race"  # Default and only game mode for now
    FIXED_TIMESTEP = 1.0 / 60.0  # 60 FPS for headless mode
    GRAPHICS_FPS = 240  # Frames per second for graphics mode
    
    # Runtime overrides (set by command line arguments)
    _runtime_num_marbles = None
    _runtime_arena_width = None
    _runtime_arena_height = None
    _runtime_terrain_complexity = None
    
    @property
    def NUM_MARBLES(self):
        return self._runtime_num_marbles or self.DEFAULT_NUM_MARBLES
    
    @property 
    def ARENA_WIDTH(self):
        return self._runtime_arena_width or TerrainConfig.DEFAULT_ARENA_WIDTH
        
    @property
    def ARENA_HEIGHT(self):
        return self._runtime_arena_height or TerrainConfig.DEFAULT_ARENA_HEIGHT
        
    @property
    def TERRAIN_COMPLEXITY(self):
        return self._runtime_terrain_complexity or TerrainConfig.DEFAULT_TERRAIN_COMPLEXITY
    
    def set_runtime_parameters(self, num_marbles=None, arena_width=None, arena_height=None, terrain_complexity=None):
        """Set runtime configuration overrides"""
        if num_marbles is not None:
            self._runtime_num_marbles = num_marbles
        if arena_width is not None:
            self._runtime_arena_width = arena_width
        if arena_height is not None:
            self._runtime_arena_height = arena_height
        if terrain_complexity is not None:
            self._runtime_terrain_complexity = terrain_complexity

    # Marble physics
    MARBLE_RADIUS = 15
    MARBLE_SPEED = 175  # pixels per second
    COLLISION_RESTITUTION = 1.0  # Elastic collisions
    MARBLE_PLACEMENT_BUFFER = 5  # Buffer between marbles and obstacles
    
    # Collision detection and resolution
    MAX_MARBLE_PLACEMENT_ATTEMPTS = 200
    SEPARATION_BUFFER = 5  # Minimum distance between marbles
    
    # Collision system configuration
    COLLISION_POSITION_TOLERANCE = 0.1  # Minimum distance to consider objects separated (increased for stability)
    COLLISION_MAX_SEPARATION_ITERATIONS = 4  # Maximum attempts to separate overlapping objects (reduced to avoid jitter)
    COLLISION_VELOCITY_DAMPING = 0.999  # Slight velocity damping to prevent energy buildup (closer to 1.0 = less damping)
    COLLISION_SEPARATION_FACTOR = 1.0  # Factor for marble separation (1.0 = full separation)
    COLLISION_MAX_PASSES = 1  # Maximum collision resolution passes per frame (reduced to prevent oscillation)
    COLLISION_BOUNDARY_PRECISION = True  # Use precise boundary positioning
    COLLISION_TERRAIN_STEP_SIZE = 0.2  # Step size for terrain separation (increased for faster, more stable separation)
    
    # Color generation for marbles
    MARBLE_COLOR_SATURATION = 0.8
    MARBLE_COLOR_VALUE = 0.9
    
    # Progress reporting
    HEADLESS_PROGRESS_INTERVAL = 480  # frames between progress reports


class TerrainConfig:
    # Organic track generator parameters (used by the new generator)
    MIN_PATH_WIDTH = 8              # Minimum width of main path (grid cells)
    MAX_PATH_WIDTH = 12               # Maximum width of main path (grid cells)
    CHAMBER_COUNT = 4                 # Number of chambers along the main path
    CHAMBER_RADIUS_MIN = 6            # Minimum chamber radius (grid cells)
    CHAMBER_RADIUS_MAX = 12           # Maximum chamber radius (grid cells)
    BRANCH_COUNT = 3                  # Number of branches off the main path
    ISLAND_COUNT = 6                  # Number of islands to place (in chambers/corridors)
    # Arena dimensions
    DEFAULT_ARENA_WIDTH = 1280
    DEFAULT_ARENA_HEIGHT = 960
    DEFAULT_TERRAIN_COMPLEXITY = .8  # 0.0 = borders only, 1.0 = maximum complexity
    # Grid resolution for terrain generation
    TERRAIN_GRID_SCALE = 9  # World pixels per grid cell (smaller for higher resolution)
    # Border configuration
    SOLID_BORDER_WIDTH = 150  # Width of solid border in pixels



class RenderingConfig:
    """Base configuration for graphics rendering"""
    
    # Display settings
    WINDOW_TITLE = "Marble Race Simulation"
    BACKGROUND_COLOR = (0, 0, 0)  # Black background for terrain
    
    # UI elements
    SHOW_FPS = True
    FPS_COLOR = (0, 0, 0)  # Black text
    FPS_POSITION = (10, 10)
      # Marble rendering
    MARBLE_BORDER_WIDTH = 0  # No border by default
    MARBLE_BORDER_COLOR = (0, 0, 0)  # Black border if enabled
    
    # Terrain rendering
    TERRAIN_ALPHA = 255  # Fully opaque


# =============================================================================
# GAME MODE SPECIFIC CONFIGURATIONS
# =============================================================================

class IndivRaceSimulationConfig(SimulationConfig):
    """Simulation config for individual race mode - no time limit, runs forever"""
    


class IndivRaceTerrainConfig(TerrainConfig):
    """Terrain config for individual race mode"""
    
    # Zone placement parameters
    MIN_SPAWN_GOAL_DISTANCE_FACTOR = 0.25  # Minimum distance as fraction of arena diagonal
    ZONE_SEPARATION_BUFFER = 100  # Additional buffer distance in pixels
    SPAWN_ZONE_RADIUS_MULTIPLIER = 3  # Multiplier for spawn zone size (marble_radius * this value)
    GOAL_ZONE_RADIUS_MULTIPLIER = 1.5   # Multiplier for goal zone size (marble_radius * this value)
    


class IndivRaceRenderingConfig(RenderingConfig):
    """Rendering config for individual race mode"""
    


# =============================================================================
# GAME MODE CONFIGURATIONS REGISTRY
# =============================================================================

GAME_MODE_CONFIGS = {
    "indiv_race": {
        "simulation": IndivRaceSimulationConfig,
        "terrain": IndivRaceTerrainConfig,
        "rendering": IndivRaceRenderingConfig,
    }
}


class Config:
    """Main configuration class that manages game mode specific configurations"""
    
    def __init__(self, game_mode: str = "indiv_race"):
        # Global RNG config (same across all game modes)
        self.rng = RNGConfig()
        
        # Initialize with default game mode
        self.current_game_mode = game_mode
        self.activate_game_mode(game_mode)
    
    def activate_game_mode(self, game_mode: str):
        """Activate a specific game mode configuration"""
        if game_mode not in GAME_MODE_CONFIGS:
            available_modes = ", ".join(GAME_MODE_CONFIGS.keys())
            raise ValueError(f"Unknown game mode '{game_mode}'. Available modes: {available_modes}")
        
        self.current_game_mode = game_mode
        mode_configs = GAME_MODE_CONFIGS[game_mode]
        
        # Instantiate game mode specific configs
        self.simulation = mode_configs["simulation"]()
        self.terrain = mode_configs["terrain"]()
        self.rendering = mode_configs["rendering"]()
    
    def get_available_game_modes(self) -> list:
        """Get list of available game modes"""
        return list(GAME_MODE_CONFIGS.keys())


# Global configuration instance - starts with indiv_race mode
config = Config()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config


def set_game_mode(game_mode: str):
    """Set the active game mode globally"""
    global config
    config.activate_game_mode(game_mode)
