"""
Random Number Generator Module

This module centralizes all random number generation for the marble race simulation.
It provides configurable seeding based on different modes: date, random, or user-set value.
"""

import random
import time
from datetime import date
from typing import Optional, Literal


# Import RNGMode from config to avoid circular imports, we'll handle this differently
class RNGConfig:
    """Configuration for random number generation"""
    
    def __init__(self, mode: str = "random", seed_value: Optional[int] = None):
        self.mode = mode
        self.seed_value = seed_value
        self._current_seed = None
        self._initialize_seed()
    
    def _initialize_seed(self):
        """Initialize the random seed based on the configured mode"""
        if self.mode == "date":
            # Use current date as seed (YYYYMMDD format)
            today = date.today()
            self._current_seed = int(today.strftime("%Y%m%d"))
        elif self.mode == "random":
            # Use current unix timestamp
            self._current_seed = int(time.time())
        elif self.mode == "set":
            # Use user-provided seed value
            if self.seed_value is None:
                raise ValueError("RNG mode 'set' requires a seed_value to be provided")
            self._current_seed = self.seed_value
        else:
            raise ValueError(f"Unknown RNG mode: {self.mode}")
        
        # Apply the seed to Python's random module
        random.seed(self._current_seed)
    
    def get_seed(self) -> int:
        """Get the current seed value"""
        return self._current_seed
    
    def reseed(self):
        """Re-initialize the seed (useful for random mode to get a new timestamp)"""
        self._initialize_seed()


# Global RNG configuration instance
_rng_config = RNGConfig()


def configure_rng(mode: str, seed_value: Optional[int] = None):
    """Configure the global RNG settings"""
    global _rng_config
    _rng_config = RNGConfig(mode, seed_value)


def get_rng_config() -> RNGConfig:
    """Get the global RNG configuration"""
    return _rng_config


def get_current_seed() -> int:
    """Get the current seed value"""
    return _rng_config.get_seed()


# Convenience functions that wrap the standard random module
# These ensure all random generation uses the configured seed

def uniform(a: float, b: float) -> float:
    """Generate a random float between a and b"""
    return random.uniform(a, b)


def randint(a: int, b: int) -> int:
    """Generate a random integer between a and b (inclusive)"""
    return random.randint(a, b)


def choice(seq):
    """Choose a random element from a sequence"""
    return random.choice(seq)


def random_float() -> float:
    """Generate a random float between 0.0 and 1.0"""
    return random.random()
