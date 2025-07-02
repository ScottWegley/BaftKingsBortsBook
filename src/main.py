import argparse
import sys
from simulation import run_graphics_mode, run_headless_mode


def main():
    parser = argparse.ArgumentParser(description="Marble Race Simulation")
    parser.add_argument("--headless", action="store_true", 
                       help="Run simulation without graphics")
    parser.add_argument("--graphics", action="store_true", 
                       help="Run simulation with graphics (default)")
    parser.add_argument("--marbles", type=int, default=8, 
                       help="Number of marbles in the simulation (default: 8)")
    
    args = parser.parse_args()
    
    # Default to graphics mode if neither specified
    if not args.headless and not args.graphics:
        args.graphics = True
    
    # Validate marble count
    if args.marbles < 1:
        print("Error: Number of marbles must be at least 1")
        sys.exit(1)
    
    if args.marbles > 50:
        print("Warning: Large number of marbles may impact performance")
    
    try:
        if args.headless:
            run_headless_mode(args.marbles)
        else:
            run_graphics_mode(args.marbles)
    
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    except Exception as e:
        print(f"Error during simulation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()