"""
Simulation runner functions for graphics and headless modes.
"""

import pygame
import time
import os
import json
from datetime import datetime
from config import get_config
from rendering import GraphicsRenderer
from .manager import SimulationManager
from rng import get_current_seed
from enum import Enum


def _save_simulation_results(args, simulation_time: float, winner_marble_id: int):
    """Save simulation results to file"""
    # Determine output directory
    if hasattr(args, 'canon') and args.canon:
        output_dir = "results/canon"
    else:
        output_dir = "results/misc"
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simulation_results_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Collect command line arguments
    cmd_args = {}
    for arg_name, arg_value in vars(args).items():
        if isinstance(arg_value, Enum):
            cmd_args[arg_name] = arg_value.value
        else:
            cmd_args[arg_name] = arg_value
    
    # Create results data
    results = {
        "timestamp": datetime.now().isoformat(),
        "command_line_arguments": cmd_args,
        "rng_seed": get_current_seed(),
        "winning_marble": winner_marble_id,
        "simulation_length_seconds": round(simulation_time, 2)
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {filepath}")


def _print_simulation_info(mode_name: str, extra_info: str = ""):
    """Helper function to print simulation information"""
    cfg = get_config()
    print(f"Starting marble simulation with {cfg.simulation.NUM_MARBLES} marbles ({mode_name})")
    print(f"Game Mode: {cfg.current_game_mode} (Endless)")
    print(f"Arena: {cfg.simulation.ARENA_WIDTH}x{cfg.simulation.ARENA_HEIGHT}, Terrain complexity: {cfg.simulation.TERRAIN_COMPLEXITY:.2f}")
    if extra_info:
        print(extra_info)


def run_graphics_mode(args=None):
    """Run simulation with graphics"""
    _print_simulation_info("Graphics Mode", "Press ESC or close window to exit early")
    
    simulation = SimulationManager()
    renderer = GraphicsRenderer(simulation)

    cfg = get_config()
    running = True
    fixed_dt = cfg.simulation.FIXED_TIMESTEP
    accumulator = 0.0


    # --- Pre-simulation countdown: only update timer and render, no simulation processing ---
    while running and simulation.simulation_time < 0:
        frame_dt = renderer.get_dt()
        running = renderer.handle_events()
        simulation.simulation_time += frame_dt
        renderer.render()

    # --- Main simulation loop ---
    # --- Main simulation loop ---


    while running and not simulation.is_finished():
        frame_dt = renderer.get_dt()
        accumulator += frame_dt

        # Handle events
        running = renderer.handle_events()

        # Standard simulation update
        while accumulator >= fixed_dt:
            simulation.update(fixed_dt)
            accumulator -= fixed_dt

        # Render at display frame rate
        renderer.render()

    pygame.quit()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")

    # Save results if args provided
    if args is not None and simulation.get_winner() is not None:
        _save_simulation_results(args, simulation.simulation_time, simulation.get_winner())


def run_headless_mode(args=None):
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
    
    # Save results if args provided
    if args is not None and simulation.get_winner() is not None:
        _save_simulation_results(args, simulation.simulation_time, simulation.get_winner())
