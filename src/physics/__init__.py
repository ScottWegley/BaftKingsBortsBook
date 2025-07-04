
"""
Physics module for the marble race simulation.

This module contains all physics-related classes and functionality,
including marble physics and the unified physics engine for collision detection.
"""

from .marble import Marble
from .engine import PhysicsEngine, get_physics_engine, initialize_physics_engine

__all__ = ['Marble', 'PhysicsEngine', 'get_physics_engine', 'initialize_physics_engine']
