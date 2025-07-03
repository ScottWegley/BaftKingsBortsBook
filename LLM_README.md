
# Marble Race Simulation

A modular, physics-based simulation of marbles racing on procedurally generated flowing terrain.

## Structure

- `src/`
  - `main.py`: CLI entry point
  - `config.py`: Centralized configuration (physics, terrain, rendering)
  - `rng.py`: Random number generation (seeded, deterministic)
  - `physics/`: Marble physics and collision
  - `terrain/`: Terrain generation (height fields, obstacles)
  - `rendering/`: Pygame-based graphics
  - `simulation/`: Simulation orchestration, marble management
  - `game_modes/`: Game logic, zone validation

## Core Concepts

- **Marble Physics**: Constant speed, elastic collisions, boundary handling.
- **Terrain**: Procedurally generated using mathematical functions, with post-processing for realism.
- **Zones**: Spawn/goal zones validated for clear paths and placement.
- **Simulation**: Supports both real-time graphics and fast headless execution.
- **Configuration**: All parameters (marble size, speed, terrain complexity, etc.) are centralized and overridable via CLI.

## Usage

- CLI options: number of marbles, terrain complexity, arena size, execution mode, RNG seed/mode.
- Results can be saved for analysis.

## Dependencies

- Required: `pygame`
- Optional (for advanced terrain): `numpy`, `scipy`, `scikit-image`

## Extensibility

- Modular design: Physics, terrain, rendering, and simulation are decoupled for easy extension/testing.
