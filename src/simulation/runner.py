"""
Simulation runner functions for graphics and headless modes.
"""

import pygame
import time
from config import get_config
from rendering import GraphicsRenderer
from .manager import SimulationManager


def _print_simulation_info(mode_name: str, extra_info: str = ""):
    """Helper function to print simulation information"""
    cfg = get_config()
    print(f"Starting marble simulation with {cfg.simulation.NUM_MARBLES} marbles ({mode_name})")
    print(f"Game Mode: {cfg.current_game_mode} (Endless)")
    print(f"Arena: {cfg.simulation.ARENA_WIDTH}x{cfg.simulation.ARENA_HEIGHT}, Terrain complexity: {cfg.simulation.TERRAIN_COMPLEXITY:.2f}")
    if extra_info:
        print(extra_info)


def run_graphics_mode():
    """Run simulation with graphics"""
    _print_simulation_info("Graphics Mode", "Press ESC or close window to exit early")
    
    simulation = SimulationManager()
    renderer = GraphicsRenderer(simulation)
    
    cfg = get_config()
    running = True
    # Use fixed timestep for simulation consistency, separate from rendering frame rate
    fixed_dt = cfg.simulation.FIXED_TIMESTEP
    accumulator = 0.0
    
    while running and not simulation.is_finished():
        frame_dt = renderer.get_dt()
        accumulator += frame_dt
        
        # Handle events
        running = renderer.handle_events()
        
        # Update simulation with fixed timestep (may run multiple times per frame)
        while accumulator >= fixed_dt:
            simulation.update(fixed_dt)
            accumulator -= fixed_dt
        
        # Render at display frame rate
        renderer.render()
    
    pygame.quit()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")


def run_headless_mode():
    """Run simulation without graphics"""
    _print_simulation_info("Headless Mode")
    
    simulation = SimulationManager()
    
    cfg = get_config()
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
