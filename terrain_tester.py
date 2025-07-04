"""
Terrain Generator Testing Script

This script generates terrain maps with different RNG seeds and saves them as images
to test the terrain generator and zone placement for the indiv_race game mode.
"""

import os
import sys
import pygame
from typing import List, Tuple
import json
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import get_config, set_game_mode
from rng import configure_rng, RNGMode
from terrain.generator import FlowingTerrainGenerator
from game_modes.indiv_race import IndivRaceGameMode


class TerrainTester:
    """Class to generate and test terrain with different seeds"""
    
    def __init__(self, arena_width: int = 1280, arena_height: int = 960):
        self.arena_width = arena_width
        self.arena_height = arena_height
        pygame.init()
        
        # Create a surface for rendering terrain
        self.surface = pygame.Surface((arena_width, arena_height))
        
        # Track statistics
        self.stats = {
            "total_tested": 0,
            "valid_terrains": 0,
            "invalid_terrains": 0,
            "terrain_generation_failures": 0,
            "zone_placement_failures": 0,
            "failed_seeds": [],
            "successful_seeds": [],
            "no_zones_seeds": []
        }
    
    def generate_terrain_image(self, seed: int, save_path: str) -> Tuple[bool, str]:
        """
        Generate terrain with given seed and save as image.
        Returns (is_valid, failure_reason).
        """
        try:
            # Configure RNG with the given seed
            configure_rng(RNGMode.SET, seed)
            
            # Configure game mode to indiv_race
            set_game_mode("indiv_race")
            
            # Create terrain generator
            terrain_gen = FlowingTerrainGenerator(self.arena_width, self.arena_height, seed)
            
            # Generate terrain
            try:
                terrain_gen.generate_terrain()
            except Exception as e:
                self.stats["terrain_generation_failures"] += 1
                self.stats["invalid_terrains"] += 1
                self.stats["failed_seeds"].append(seed)
                self.stats["total_tested"] += 1
                return False, f"terrain_generation_failed: {str(e)}"
            
            # Create game mode instance to test zone placement
            game_mode = IndivRaceGameMode(self.arena_width, self.arena_height)
            
            # Test if terrain is valid for indiv_race
            obstacles = terrain_gen.get_obstacles()
            is_valid = game_mode.validate_and_setup_terrain(obstacles)
            
            # Clear surface and render terrain
            self.surface.fill((0, 0, 0))  # Black background
            
            # Render terrain
            terrain_gen.render_terrain(self.surface)
            
            # Track zone placement status
            has_zones = is_valid and game_mode.spawn_zone and game_mode.goal_zone
            
            # If valid, draw zones
            if has_zones:
                # Draw spawn zone in green
                spawn_zone = game_mode.spawn_zone
                pygame.draw.circle(self.surface, (0, 255, 0), 
                                 (int(spawn_zone.center_x), int(spawn_zone.center_y)), 
                                 int(spawn_zone.radius), 3)
                
                # Draw goal zone in red
                goal_zone = game_mode.goal_zone
                pygame.draw.circle(self.surface, (255, 0, 0), 
                                 (int(goal_zone.center_x), int(goal_zone.center_y)), 
                                 int(goal_zone.radius), 3)
            else:
                # If terrain generated but no zones, draw a warning indicator
                warning_text = "NO ZONES"
                # Simple text rendering - draw rectangles to simulate text
                for i, char in enumerate(warning_text):
                    x = 10 + i * 15
                    y = 10
                    pygame.draw.rect(self.surface, (255, 255, 0), (x, y, 12, 20))
            
            # Add border to show arena bounds
            pygame.draw.rect(self.surface, (255, 255, 255), 
                           (0, 0, self.arena_width, self.arena_height), 2)
            
            # Save the image
            pygame.image.save(self.surface, save_path)
            
            # Update statistics
            if is_valid and has_zones:
                self.stats["valid_terrains"] += 1
                self.stats["successful_seeds"].append(seed)
                failure_reason = "success"
            else:
                self.stats["invalid_terrains"] += 1
                if not has_zones:
                    self.stats["zone_placement_failures"] += 1
                    self.stats["no_zones_seeds"].append(seed)
                    failure_reason = "zone_placement_failed"
                else:
                    self.stats["failed_seeds"].append(seed)
                    failure_reason = "validation_failed"
            
            self.stats["total_tested"] += 1
            
            return is_valid and has_zones, failure_reason
            
        except Exception as e:
            print(f"Error generating terrain for seed {seed}: {e}")
            self.stats["invalid_terrains"] += 1
            self.stats["failed_seeds"].append(seed)
            self.stats["total_tested"] += 1
            return False, f"exception: {str(e)}"
    
    def run_test_batch(self, num_seeds: int = 1000, output_dir: str = "assets/terrain_tests", start_seed: int = None):
        """
        Generate terrain images for a batch of seeds.
        """
        print(f"Starting terrain testing with {num_seeds} seeds...")
        print(f"Output directory: {output_dir}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate seeds (using provided start_seed or current timestamp as base)
        if start_seed is not None:
            base_seed = start_seed
            print(f"Using starting seed: {base_seed}")
        else:
            base_seed = int(datetime.now().timestamp())
            print(f"Using timestamp-based starting seed: {base_seed}")
        
        for i in range(num_seeds):
            seed = base_seed + i
            
            # Create filename
            status_prefix = ""
            filename = f"terrain_seed_{seed}.png"
            filepath = os.path.join(output_dir, filename)
            
            # Generate terrain
            is_valid, failure_reason = self.generate_terrain_image(seed, filepath)
            
            # Print progress
            if (i + 1) % 50 == 0 or i == 0:
                valid_percent = (self.stats["valid_terrains"] / self.stats["total_tested"]) * 100
                print(f"Progress: {i + 1}/{num_seeds} | Valid: {self.stats['valid_terrains']} ({valid_percent:.1f}%)")
        
        # Print final statistics
        self.print_final_stats()
        
        # Save statistics to JSON
        stats_file = os.path.join(output_dir, "terrain_test_stats.json")
        self.save_stats(stats_file)
    
    def print_final_stats(self):
        """Print final testing statistics"""
        total = self.stats["total_tested"]
        valid = self.stats["valid_terrains"]
        invalid = self.stats["invalid_terrains"]
        zone_failures = self.stats["zone_placement_failures"]
        terrain_failures = self.stats["terrain_generation_failures"]
        
        print("\n" + "="*50)
        print("TERRAIN TESTING RESULTS")
        print("="*50)
        print(f"Total terrains tested: {total}")
        print(f"Valid terrains (with zones): {valid} ({(valid/total)*100:.1f}%)")
        print(f"Invalid terrains: {invalid} ({(invalid/total)*100:.1f}%)")
        print(f"  - Zone placement failures: {zone_failures} ({(zone_failures/total)*100:.1f}%)")
        print(f"  - Terrain generation failures: {terrain_failures} ({(terrain_failures/total)*100:.1f}%)")
        print(f"  - Other validation failures: {invalid - zone_failures - terrain_failures}")
        
        if len(self.stats["no_zones_seeds"]) > 0:
            print(f"\nFirst 10 seeds with zone placement issues: {self.stats['no_zones_seeds'][:10]}")
        if len(self.stats["failed_seeds"]) > 0:
            print(f"First 10 completely failed seeds: {self.stats['failed_seeds'][:10]}")
    
    def save_stats(self, filepath: str):
        """Save statistics to JSON file"""
        stats_data = {
            "timestamp": datetime.now().isoformat(),
            "arena_dimensions": {
                "width": self.arena_width,
                "height": self.arena_height
            },
            "statistics": self.stats
        }
        
        with open(filepath, 'w') as f:
            json.dump(stats_data, f, indent=2)
        
        print(f"Statistics saved to: {filepath}")


def main():
    """Main function to run terrain testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test terrain generation with different RNG seeds")
    parser.add_argument("--num-seeds", type=int, default=5, 
                       help="Number of seeds to test (default: 1000)")
    parser.add_argument("--start-seed", type=int, default=None,
                       help="Starting seed value (default: use current timestamp)")
    parser.add_argument("--output-dir", type=str, default="assets/terrain_tests/testX",
                       help="Output directory for terrain images (default: assets/terrain_tests/testX)")
    parser.add_argument("--arena-width", type=int, default=1280,
                       help="Arena width (default: 1280)")
    parser.add_argument("--arena-height", type=int, default=960,
                       help="Arena height (default: 960)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = TerrainTester(args.arena_width, args.arena_height)
    
    # Run the test batch
    tester.run_test_batch(args.num_seeds, args.output_dir, args.start_seed)
    
    # Cleanup pygame
    pygame.quit()


if __name__ == "__main__":
    main()
