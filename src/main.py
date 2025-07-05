import argparse
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.runner import run_graphics_mode, run_headless_mode
from config import get_config, set_game_mode, RNGMode
from rng import configure_rng, get_current_seed


def main():
    cfg = get_config()
    
    parser = argparse.ArgumentParser(description="Marble Race Simulation")
    parser.add_argument("--headless", action="store_true", 
                       help="Run simulation without graphics")
    parser.add_argument("--graphics", action="store_true", 
                       help="Run simulation with graphics (default)")
    parser.add_argument("--game-mode", type=str, choices=cfg.get_available_game_modes(), 
                       default=cfg.current_game_mode, 
                       help=f"Game mode to run (default: {cfg.current_game_mode}). Available: {', '.join(cfg.get_available_game_modes())}")
    parser.add_argument("--marbles", type=int, default=cfg.simulation.DEFAULT_NUM_MARBLES, 
                       help=f"Number of marbles in the simulation (default: {cfg.simulation.DEFAULT_NUM_MARBLES})")
    parser.add_argument("--terrain-complexity", type=float, default=cfg.terrain.DEFAULT_TERRAIN_COMPLEXITY,
                       help=f"Terrain complexity from 0.0 (simple) to 1.0 (very complex) (default: {cfg.terrain.DEFAULT_TERRAIN_COMPLEXITY})")
    parser.add_argument("--arena-width", type=int, default=cfg.terrain.DEFAULT_ARENA_WIDTH,
                       help=f"Arena width in pixels (default: {cfg.terrain.DEFAULT_ARENA_WIDTH})")
    parser.add_argument("--arena-height", type=int, default=cfg.terrain.DEFAULT_ARENA_HEIGHT,
                       help=f"Arena height in pixels (default: {cfg.terrain.DEFAULT_ARENA_HEIGHT})")    
    parser.add_argument("--rng-mode", type=str, choices=["date", "random", "set"], 
                       default=cfg.rng.DEFAULT_RNG_MODE.value, help="RNG seed mode: 'date' uses current date, 'random' uses timestamp, 'set' uses --rng-value")
    parser.add_argument("--rng-value", type=int, 
                       help="Seed value to use when --rng-mode is 'set'")
    parser.add_argument("--canon", action="store_true", 
                       help="Save results to /results/canon instead of /results/misc")
    args = parser.parse_args()
    
    # Activate the selected game mode
    if args.game_mode != cfg.current_game_mode:
        set_game_mode(args.game_mode)
        cfg = get_config()  # Get updated config
    
    # Configure RNG based on command line arguments
    rng_mode = args.rng_mode
    if rng_mode == "set" and args.rng_value is None:
        print("Error: --rng-mode set requires --rng-value to be specified")
        sys.exit(1)
    
    configure_rng(rng_mode, args.rng_value)
    print(f"Using RNG seed: {get_current_seed()}")
    
    # Default to graphics mode if neither specified
    if not args.headless and not args.graphics:
        args.graphics = True
    
    # Validate marble count
    if args.marbles < 1:
        print("Error: Number of marbles must be at least 1")
        sys.exit(1)
    
    if args.marbles > 50:
        print("Warning: Large number of marbles may impact performance")
      # Validate terrain complexity
    if args.terrain_complexity < 0.0 or args.terrain_complexity > 1.0:
        print("Error: Terrain complexity must be between 0.0 and 1.0")
        sys.exit(1)

    # Validate arena dimensions
    if args.arena_width < 200 or args.arena_height < 200:
        print("Error: Arena dimensions must be at least 200x200 pixels")
        sys.exit(1)
    
    # Set runtime configuration instead of passing parameters around
    cfg.simulation.set_runtime_parameters(
        num_marbles=args.marbles,
        arena_width=args.arena_width,
        arena_height=args.arena_height,
        terrain_complexity=args.terrain_complexity
    )
    
    try:
        if args.headless:
            run_headless_mode(args)
        else:
            run_graphics_mode(args)
    
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    except Exception as e:
        print(f"Error during simulation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()