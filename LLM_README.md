You are working with a MARBLE RACE SIMULATION codebase. This is a physics-based simulation with procedurally generated flowing terrain.

PROJECT STRUCTURE:
```
src/
├── main.py                    # CLI entry point
├── config.py                  # Centralized configuration
├── rng.py                     # Random number generation
├── physics/                   # Physics engine and objects
│   ├── __init__.py
│   ├── marble.py             # Marble physics object
│   └── collision.py          # Collision detection utilities
├── terrain/                   # Terrain generation system
│   ├── __init__.py
│   ├── generator.py          # Main terrain generator
│   ├── height_field.py       # Height field generation algorithms
│   └── obstacle.py           # Terrain obstacle collision/rendering
├── rendering/                 # Graphics and visualization
│   ├── __init__.py
│   └── graphics.py           # Pygame graphics renderer
└── simulation/                # Simulation management
    ├── __init__.py
    ├── manager.py            # Main simulation orchestrator
    ├── runner.py             # Graphics/headless mode runners  
    └── marble_factory.py     # Marble creation and positioning
```

CORE CLASSES:
- `physics.Marble`: Physics object with position, velocity, elastic collisions, constant speed maintenance
- `simulation.SimulationManager`: Manages multiple marbles, terrain, physics updates through orchestration
- `terrain.FlowingTerrainGenerator`: Creates organic terrain using sine waves, flow channels, smoothing, erosion
- `rendering.GraphicsRenderer`: Pygame visualization with real-time rendering
- `physics.CollisionDetector`: Handles marble-to-marble collision detection and resolution
- `simulation.MarbleFactory`: Creates and positions marbles avoiding terrain overlap

PHYSICS BEHAVIOR:
- Marbles maintain constant speed through velocity normalization
- Elastic collisions between marbles and terrain with reflection/push-out
- Fixed timestep physics for consistency
- Gradual terrain collision response prevents clipping

TERRAIN GENERATION:
- Procedural creation using mathematical functions (sine waves, random walks)
- Advanced post-processing: smoothing, erosion, border generation, small feature removal
- Supports pure Python fallback if scientific libraries unavailable
- Configurable complexity (0.0-1.0) affects terrain density and features

EXECUTION MODES:
- Graphics mode: Real-time pygame visualization with 120 FPS
- Headless mode: Fast simulation with fixed timestep, progress reporting

CLI PARAMETERS:
- `--marbles N`: Number of marbles (1-50)
- `--terrain-complexity F`: Complexity factor (0.0-1.0)
- `--arena-width/height N`: Arena dimensions (min 200x200)
- `--headless/graphics`: Execution mode

CONFIGURATION SYSTEM:
All parameters centralized in `config.py` with classes:
- `SimulationConfig`: Physics constants, collision parameters, marble properties
- `TerrainConfig`: Generation parameters, smoothing settings, visual properties
- `RenderingConfig`: Display settings, colors, UI elements

MODULAR ARCHITECTURE:
- **Physics Module**: Contains all physics-related functionality including marble behavior and collision detection
- **Terrain Module**: Handles all terrain generation from height fields to obstacles and rendering
- **Rendering Module**: Manages all graphics and visualization using Pygame
- **Simulation Module**: Orchestrates the entire simulation, managing components without tight coupling
- **Configuration**: Centralized configuration system accessible to all modules
- **RNG Module**: Provides consistent random number generation across all modules

DEPENDENCIES:
- pygame: Required for graphics and input handling
- numpy, scipy, scikit-image: Optional for enhanced terrain generation

When working with this code, consider the physics consistency, terrain generation quality, and performance optimization between graphics/headless modes. The modular architecture allows for easy extension and testing of individual components.
