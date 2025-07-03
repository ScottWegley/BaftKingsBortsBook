"""
Simulation runner functions for graphics and headless modes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pygame
import time
from config import get_config
from rendering import GraphicsRenderer
from .manager import SimulationManager


def run_graphics_mode(num_marbles: int = None, terrain_complexity: float = None, 
                     arena_width: int = None, arena_height: int = None):
    """Run simulation with graphics"""
    cfg = get_config()    # Use config defaults if not specified
    num_marbles = num_marbles if num_marbles is not None else cfg.simulation.DEFAULT_NUM_MARBLES
    terrain_complexity = terrain_complexity if terrain_complexity is not None else cfg.terrain.DEFAULT_TERRAIN_COMPLEXITY
    arena_width = arena_width if arena_width is not None else cfg.terrain.DEFAULT_ARENA_WIDTH
    arena_height = arena_height if arena_height is not None else cfg.terrain.DEFAULT_ARENA_HEIGHT
    
    print(f"Starting marble simulation with {num_marbles} marbles (Graphics Mode)")
    print(f"Game Mode: {cfg.current_game_mode} (Endless)")
    print(f"Arena: {arena_width}x{arena_height}, Terrain complexity: {terrain_complexity:.2f}")
    print("Press ESC or close window to exit early")
    
    simulation = SimulationManager(
        num_marbles=num_marbles, 
        terrain_complexity=terrain_complexity,
        arena_width=arena_width,
        arena_height=arena_height
    )
    renderer = GraphicsRenderer(simulation)
    
    running = True
    while running and not simulation.is_finished():
        dt = renderer.get_dt()
        
        # Handle events
        running = renderer.handle_events()
        
        # Update simulation
        simulation.update(dt)
          # Render
        renderer.render()
    
    pygame.quit()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")


def run_headless_mode(num_marbles: int = None, terrain_complexity: float = None,
                     arena_width: int = None, arena_height: int = None):
    """Run simulation without graphics"""
    cfg = get_config()
    
    # Use config defaults if not specified
    num_marbles = num_marbles if num_marbles is not None else cfg.simulation.DEFAULT_NUM_MARBLES
    terrain_complexity = terrain_complexity if terrain_complexity is not None else cfg.terrain.DEFAULT_TERRAIN_COMPLEXITY
    arena_width = arena_width if arena_width is not None else cfg.terrain.DEFAULT_ARENA_WIDTH
    arena_height = arena_height if arena_height is not None else cfg.terrain.DEFAULT_ARENA_HEIGHT
    
    print(f"Starting marble simulation with {num_marbles} marbles (Headless Mode)")
    print(f"Game Mode: {cfg.current_game_mode} (Endless)")
    print(f"Arena: {arena_width}x{arena_height}, Terrain complexity: {terrain_complexity:.2f}")
    
    simulation = SimulationManager(
        num_marbles=num_marbles, 
        terrain_complexity=terrain_complexity,
        arena_width=arena_width,
        arena_height=arena_height
    )
    
    # Fixed timestep for consistent simulation  
    dt = cfg.simulation.FIXED_TIMESTEP
    frames = 0
    start_time = time.time()
    
    while not simulation.is_finished():
        simulation.update(dt)
        frames += 1
        
        progress_interval = cfg.simulation.HEADLESS_PROGRESS_INTERVAL
        if frames % progress_interval == 0:
            print(f"Simulation time: {simulation.simulation_time:.1f}s")
    
    end_time = time.time()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")
    print(f"Real time elapsed: {end_time - start_time:.2f} seconds")
    print(f"Simulated {frames} frames")
