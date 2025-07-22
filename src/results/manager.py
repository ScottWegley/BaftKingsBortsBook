"""
Results management for storing and retrieving simulation results.

This module handles:
- Saving simulation results to JSON files
- Organizing results into canon vs misc directories
- Finding and loading recent results
- Formatting result data consistently
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ResultsManager:
    """Manages simulation result storage and retrieval."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize results manager.
        
        Args:
            project_root: Root directory of the project. If None, infers from this file's location.
        """
        if project_root is None:
            # Infer project root from this file's location (src/results/manager.py -> project root)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        self.project_root = project_root
        self.results_dir = os.path.join(project_root, 'results')
        self.canon_dir = os.path.join(self.results_dir, 'canon')
        self.misc_dir = os.path.join(self.results_dir, 'misc')
        
        # Ensure directories exist
        os.makedirs(self.canon_dir, exist_ok=True)
        os.makedirs(self.misc_dir, exist_ok=True)
    
    def save_results(self, 
                    simulation_time: float, 
                    winner_marble_id: int, 
                    simulation_instance=None,
                    command_args: Optional[Dict[str, Any]] = None,
                    is_canon: bool = False) -> str:
        """Save simulation results to appropriate directory.
        
        Args:
            simulation_time: Duration of the simulation in seconds
            winner_marble_id: ID of the winning marble
            simulation_instance: The simulation object to extract character info from
            command_args: Command line arguments used to run the simulation
            is_canon: Whether to save to canon or misc directory
            
        Returns:
            Path to the saved results file
        """
        # Determine output directory
        output_dir = self.canon_dir if is_canon else self.misc_dir
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simulation_results_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Get winner character information
        winner_character_id = None
        winner_character_name = None
        if (simulation_instance is not None and 
            winner_marble_id is not None and 
            hasattr(simulation_instance, 'characters') and 
            winner_marble_id < len(simulation_instance.characters)):
            char = simulation_instance.characters[winner_marble_id]
            if char:
                winner_character_id = char.id
                winner_character_name = getattr(char, 'name', None)
        
        # Get RNG seed
        rng_seed = None
        try:
            from rng import get_current_seed
            rng_seed = get_current_seed()
        except ImportError:
            pass
        
        # Process command line arguments
        processed_args = {}
        if command_args:
            for arg_name, arg_value in command_args.items():
                if isinstance(arg_value, Enum):
                    processed_args[arg_name] = arg_value.value
                else:
                    processed_args[arg_name] = arg_value
        
        # Create results data
        results = {
            "timestamp": datetime.now().isoformat(),
            "command_line_arguments": processed_args,
            "rng_seed": rng_seed,
            "winning_marble": winner_marble_id,
            "winning_character_id": winner_character_id,
            "winning_character_name": winner_character_name,
            "simulation_length_seconds": round(simulation_time, 2),
            "is_canon": is_canon
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {filepath}")
        return filepath
    
    def get_latest_results(self, canon_only: bool = False) -> Optional[Dict[str, Any]]:
        """Get the most recent simulation results.
        
        Args:
            canon_only: If True, only look in canon directory
            
        Returns:
            Dictionary containing the latest results, or None if no results found
        """
        search_dirs = [self.canon_dir] if canon_only else [self.canon_dir, self.misc_dir]
        
        latest_file = None
        latest_mtime = 0
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            json_files = [f for f in os.listdir(search_dir) if f.lower().endswith('.json')]
            for json_file in json_files:
                filepath = os.path.join(search_dir, json_file)
                mtime = os.path.getmtime(filepath)
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = filepath
        
        if latest_file:
            try:
                with open(latest_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading results from {latest_file}: {e}")
                return None
        
        return None
    
    def get_latest_canon_results(self) -> Optional[Dict[str, Any]]:
        """Get the most recent canon simulation results."""
        return self.get_latest_results(canon_only=True)
    
    def list_results(self, canon_only: bool = False, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List simulation results, sorted by timestamp (newest first).
        
        Args:
            canon_only: If True, only return canon results
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        search_dirs = [self.canon_dir] if canon_only else [self.canon_dir, self.misc_dir]
        
        all_results = []
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            json_files = [f for f in os.listdir(search_dir) if f.lower().endswith('.json')]
            for json_file in json_files:
                filepath = os.path.join(search_dir, json_file)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        result['_filepath'] = filepath  # Add filepath for reference
                        all_results.append(result)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
                    continue
        
        # Sort by timestamp (newest first)
        all_results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        if limit is not None:
            all_results = all_results[:limit]
        
        return all_results
    
    def cleanup_old_results(self, keep_count: int = 10, canon_only: bool = False) -> int:
        """Clean up old result files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent results to keep
            canon_only: If True, only clean canon results
            
        Returns:
            Number of files deleted
        """
        search_dirs = [self.canon_dir] if canon_only else [self.canon_dir, self.misc_dir]
        
        deleted_count = 0
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            json_files = [f for f in os.listdir(search_dir) if f.lower().endswith('.json')]
            
            # Sort by modification time (newest first)
            json_files.sort(key=lambda f: os.path.getmtime(os.path.join(search_dir, f)), reverse=True)
            
            # Delete files beyond keep_count
            for file_to_delete in json_files[keep_count:]:
                filepath = os.path.join(search_dir, file_to_delete)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted old result: {filepath}")
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")
        
        return deleted_count
