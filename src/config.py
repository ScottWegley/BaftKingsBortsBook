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
    GRAPHICS_FPS = 30  # Frames per second for graphics mode
    
    # Marble physics
    MARBLE_RADIUS = 15
    MARBLE_SPEED = 250  # pixels per second
    COLLISION_RESTITUTION = 1.0  # Elastic collisions
    TERRAIN_PUSH_BUFFER = 2  # Extra push distance for terrain collisions (legacy)
    MARBLE_PLACEMENT_BUFFER = 5  # Buffer between marbles and obstacles
    
    # Smooth terrain collision parameters
    TERRAIN_REFLECTION_STRENGTH = 2.0  # How strong the velocity reflection is (2.0 = perfect reflection)
    TERRAIN_PUSH_STRENGTH = 2.0  # How aggressively to push marbles out of terrain
    MAX_TERRAIN_PUSH = 8.0  # Maximum distance to push in one frame for stability
    
    # Collision detection
    MAX_MARBLE_PLACEMENT_ATTEMPTS = 200
    SEPARATION_BUFFER = 5  # Minimum distance between marbles
    
    # Color generation for marbles
    MARBLE_COLOR_SATURATION = 0.8
    MARBLE_COLOR_VALUE = 0.9
    
    # Progress reporting
    HEADLESS_PROGRESS_INTERVAL = 480  # frames between progress reports


class TerrainConfig:
    """Base configuration for terrain generation"""
    
    # Arena dimensions
    DEFAULT_ARENA_WIDTH = 1280
    DEFAULT_ARENA_HEIGHT = 960
    DEFAULT_TERRAIN_COMPLEXITY = .375
    
    # Flowing terrain parameters
    FLOW_GRID_SCALE = 8  # Divide arena dimensions by this for grid resolution
    FLOW_HEIGHT_THRESHOLD = 0.3  # Height threshold for solid terrain
    FLOW_SMOOTHING_ITERATIONS = 2
    FLOW_GAUSSIAN_SIGMA = 1.0
    
    # Sine wave parameters for flowing terrain
    FLOW_FREQ1_BASE = 0.1
    FLOW_FREQ2_BASE = 0.05
    FLOW_FREQ3_BASE = 0.2
    FLOW_AMPLITUDE1 = 0.4
    FLOW_AMPLITUDE2 = 0.3
    FLOW_AMPLITUDE3 = 0.3
    
    # Channel generation parameters
    CHANNEL_WIDTH_MIN = 40
    CHANNEL_WIDTH_MAX = 100
    CHANNEL_DEPTH = 0.5
    CHANNEL_SMOOTHNESS = 20
    NUM_CHANNELS_BASE = 2
    
    # Border and cleanup parameters
    SOLID_BORDER_WIDTH = 30  # Width of solid border in pixels
    MIN_TERRAIN_REGION_SIZE = 200  # Minimum size of terrain regions to keep (increased)
    NOISE_REDUCTION_THRESHOLD = 0.05  # Remove terrain features below this size (more aggressive)
    BORDER_FADE_DISTANCE = 15  # Distance over which border fades in
    
    # Smoothing parameters for flowing terrain
    SMOOTHING_ITERATIONS = 4  # Number of smoothing passes (increased)
    SMOOTHING_STRENGTH = 0.8  # How much smoothing to apply (0.0-1.0)
    EROSION_ITERATIONS = 4  # Number of erosion passes to remove small features


class RenderingConfig:
    """Base configuration for graphics rendering"""
    
    # Display settings
    WINDOW_TITLE = "Marble Race Simulation"
    BACKGROUND_COLOR = (0, 0, 0) 
    
    # UI elements
    SHOW_FPS = True
    FPS_COLOR = (0, 0, 0)  # Black text
    FPS_POSITION = (10, 10)
    
    # Marble rendering
    MARBLE_BORDER_WIDTH = 0  # No border by default
    MARBLE_BORDER_COLOR = (0, 0, 0)  # Black border if enabled
    
    # Terrain rendering
    TERRAIN_ALPHA = 255  # Fully opaque
    FLOWING_TERRAIN_WIREFRAME = False  # Whether to show flowing terrain as wireframe


# =============================================================================
# GAME MODE SPECIFIC CONFIGURATIONS
# =============================================================================

class IndivRaceSimulationConfig(SimulationConfig):
    """Simulation config for individual race mode - no time limit, runs forever"""
    


class IndivRaceTerrainConfig(TerrainConfig):
    """Terrain config for individual race mode"""
    


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
