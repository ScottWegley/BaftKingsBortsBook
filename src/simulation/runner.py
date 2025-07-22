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
from integrations import DiscordIntegration
from results import ResultsManager


def _save_simulation_results(args, simulation_time: float, winner_marble_id: int, simulation=None):
    """Save simulation results using the ResultsManager."""
    results_manager = ResultsManager()
    
    # Collect command line arguments
    cmd_args = {}
    if args:
        for arg_name, arg_value in vars(args).items():
            cmd_args[arg_name] = arg_value
    
    # Determine if this is a canon run
    is_canon = hasattr(args, 'canon') and args.canon
    
    # Save results
    filepath = results_manager.save_results(
        simulation_time=simulation_time,
        winner_marble_id=winner_marble_id,
        simulation_instance=simulation,
        command_args=cmd_args,
        is_canon=is_canon
    )
    
    return filepath


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
    
    # Initialize Discord integration if output is enabled
    discord = None
    cfg = get_config()
    discord_enabled = (hasattr(args, 'output') and args.output and 
                      cfg.integration.DISCORD_ENABLED and 
                      not (hasattr(args, 'no_discord') and args.no_discord))
    
    if discord_enabled:
        discord = DiscordIntegration()
        if discord.is_configured() and cfg.integration.DISCORD_SEND_START:
            discord.send_race_start()

    simulation = SimulationManager()
    renderer = GraphicsRenderer(simulation)

    # Video recording setup
    video_recorder = None
    # If output is requested, clear any existing mp4 files in output dir first
    if hasattr(args, 'output') and args.output:
        # Always use project root/output
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
        if os.path.exists(output_dir):
            for f in os.listdir(output_dir):
                if f.lower().endswith('.mp4'):
                    try:
                        os.remove(os.path.join(output_dir, f))
                    except Exception as e:
                        print(f"Warning: Could not delete {f}: {e}")
        from rendering.video_recorder import VideoRecorder
        video_fps = getattr(cfg.simulation, 'VIDEO_FPS', 60)
        video_recorder = VideoRecorder(simulation.arena_width, simulation.arena_height, output_dir="output", fps=video_fps)

    running = True
    fixed_dt = cfg.simulation.FIXED_TIMESTEP
    accumulator = 0.0


    # --- Pre-simulation countdown: only update timer and render, no simulation processing ---
    while running and simulation.simulation_time < 0:
        frame_dt = renderer.get_dt()
        running = renderer.handle_events()
        simulation.simulation_time += frame_dt
        renderer.render()
        if video_recorder:
            video_recorder.add_frame(renderer.screen, fixed_dt)

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
        if video_recorder:
            video_recorder.add_frame(renderer.screen, fixed_dt)

    # Freeze and show victory message for 3 seconds after win
    if simulation.is_finished():
        freeze_seconds = 3.0
        freeze_time = 0.0
        while freeze_time < freeze_seconds:
            frame_dt = renderer.get_dt()
            freeze_time += frame_dt
            renderer.render()
            if video_recorder:
                video_recorder.add_frame(renderer.screen, fixed_dt)
            # Allow quit/ESC during freeze
            if not renderer.handle_events():
                break

    # Save video if needed
    if video_recorder:
        video_recorder.save()

    pygame.quit()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")

    # Save results and handle Discord notifications if needed
    if args is not None and simulation.get_winner() is not None:
        results_filepath = _save_simulation_results(args, simulation.simulation_time, simulation.get_winner(), simulation)
        
        # Handle Discord notifications if output was enabled
        if hasattr(args, 'output') and args.output and discord and discord.is_configured():
            # Load the results for Discord posting
            results_manager = ResultsManager()
            results_data = results_manager.get_latest_results()
            
            if results_data:
                # Send completion notification with video if available
                if cfg.integration.DISCORD_SEND_COMPLETE and video_recorder:
                    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
                    mp4_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')]
                    if mp4_files:
                        mp4_files.sort()
                        video_path = os.path.join(output_dir, mp4_files[0])
                        discord.send_race_complete_with_video(video_path, results_data)
                
                # Send winner announcement (with delay)
                if cfg.integration.DISCORD_SEND_WINNER:
                    discord.send_winner_announcement(results_data)
                
                # Clean up videos if configured
                if cfg.integration.DISCORD_CLEANUP_VIDEOS:
                    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
                    discord.cleanup_videos(output_dir)


def run_headless_mode(args=None):
    """Run simulation without graphics"""
    _print_simulation_info("Headless Mode")
    
    # Initialize Discord integration if output is enabled
    discord = None
    cfg = get_config()
    discord_enabled = (hasattr(args, 'output') and args.output and 
                      cfg.integration.DISCORD_ENABLED and 
                      not (hasattr(args, 'no_discord') and args.no_discord))
    
    if discord_enabled:
        discord = DiscordIntegration()
        if discord.is_configured() and cfg.integration.DISCORD_SEND_START:
            discord.send_race_start()
    
    # Setup pygame in headless mode before importing pygame
    import os
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    simulation = SimulationManager()
    dt = cfg.simulation.FIXED_TIMESTEP
    frames = 0
    start_time = time.time()

    # Video recording setup
    video_recorder = None
    # If output is requested, clear any existing mp4 files in output dir first
    if hasattr(args, 'output') and args.output:
        # Always use project root/output
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
        if os.path.exists(output_dir):
            for f in os.listdir(output_dir):
                if f.lower().endswith('.mp4'):
                    try:
                        os.remove(os.path.join(output_dir, f))
                    except Exception as e:
                        print(f"Warning: Could not delete {f}: {e}")
        from rendering.video_recorder import VideoRecorder
        video_fps = getattr(cfg.simulation, 'VIDEO_FPS', 60)
        video_recorder = VideoRecorder(simulation.arena_width, simulation.arena_height, output_dir="output", fps=video_fps)

    pygame.display.init()
    screen = pygame.display.set_mode((simulation.arena_width, simulation.arena_height))
    from rendering.graphics import GraphicsRenderer
    renderer = GraphicsRenderer(simulation)
    renderer.screen = screen

    # Pre-simulation countdown
    simulation.simulation_time = -3.0
    while simulation.simulation_time < 0:
        simulation.simulation_time += dt
        renderer.render()
        if video_recorder:
            video_recorder.add_frame(renderer.screen, dt)

    # Main simulation loop
    while not simulation.is_finished():
        simulation.update(dt)
        renderer.render()
        if video_recorder:
            video_recorder.add_frame(renderer.screen, dt)
        frames += 1
        progress_interval = cfg.simulation.HEADLESS_PROGRESS_INTERVAL
        if frames % progress_interval == 0:
            print(f"Simulation time: {simulation.simulation_time:.1f}s")

    # Freeze and show victory message for 3 seconds after win
    freeze_seconds = 3.0
    freeze_time = 0.0
    while freeze_time < freeze_seconds:
        freeze_time += dt
        renderer.render()
        if video_recorder:
            video_recorder.add_frame(renderer.screen, dt)

    end_time = time.time()
    print(f"Simulation ended after {simulation.simulation_time:.2f} seconds")
    print(f"Real time elapsed: {end_time - start_time:.2f} seconds")
    print(f"Simulated {frames} frames")

    # Save video if needed
    if video_recorder:
        video_recorder.save()

    # Save results and handle Discord notifications if needed
    if args is not None and simulation.get_winner() is not None:
        results_filepath = _save_simulation_results(args, simulation.simulation_time, simulation.get_winner(), simulation)
        
        # Handle Discord notifications if output was enabled
        if hasattr(args, 'output') and args.output and discord and discord.is_configured():
            # Load the results for Discord posting
            results_manager = ResultsManager()
            results_data = results_manager.get_latest_results()
            
            if results_data:
                # Send completion notification with video if available
                if cfg.integration.DISCORD_SEND_COMPLETE and video_recorder:
                    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
                    mp4_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')]
                    if mp4_files:
                        mp4_files.sort()
                        video_path = os.path.join(output_dir, mp4_files[0])
                        discord.send_race_complete_with_video(video_path, results_data)
                
                # Send winner announcement (with delay)
                if cfg.integration.DISCORD_SEND_WINNER:
                    discord.send_winner_announcement(results_data)
                
                # Clean up videos if configured
                if cfg.integration.DISCORD_CLEANUP_VIDEOS:
                    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
                    discord.cleanup_videos(output_dir)
