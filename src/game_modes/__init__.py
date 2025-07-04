"""
Game modes module for the marble race simulation.

This module contains game mode specific logic for handling different race types 
and win conditions.
"""

from .base import GameResult, Zone
from .indiv_race import IndivRaceGameMode
from .optimal_terrain_validator import OptimalTerrainValidator

__all__ = ['GameResult', 'Zone', 'IndivRaceGameMode', 'OptimalTerrainValidator']
