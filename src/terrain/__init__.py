"""
Terrain generation module for the marble race simulation.

This module contains all terrain-related classes and functionality,
including procedural generation, height fields, and terrain obstacles.
"""

from .generator import FlowingTerrainGenerator
from .height_field import SimpleFlowField
from .obstacle import FlowingTerrainObstacle

__all__ = ['FlowingTerrainGenerator', 'SimpleFlowField', 'FlowingTerrainObstacle']
