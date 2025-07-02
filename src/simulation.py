import pygame
import random
import math
from typing import List, Tuple
import time


class Marble:
    def __init__(self, x: float, y: float, radius: float, color: Tuple[int, int, int], speed: float):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
        
        # Random direction (angle in radians)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
    
    def update(self, dt: float, arena_width: int, arena_height: int):
        """Update marble position and handle boundary collisions"""
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Boundary collisions - bounce off walls while maintaining constant speed
        if self.x - self.radius <= 0 or self.x + self.radius >= arena_width:
            self.velocity_x = -self.velocity_x
            # Clamp position to stay within bounds
            self.x = max(self.radius, min(arena_width - self.radius, self.x))
        
        if self.y - self.radius <= 0 or self.y + self.radius >= arena_height:
            self.velocity_y = -self.velocity_y
            # Clamp position to stay within bounds
            self.y = max(self.radius, min(arena_height - self.radius, self.y))
    
    def check_collision(self, other: 'Marble') -> bool:
        """Check if this marble collides with another marble"""
        distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return distance <= (self.radius + other.radius)
    
    def resolve_collision(self, other: 'Marble'):
        """Resolve collision with another marble using elastic collision"""
        # Calculate distance and overlap
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:  # Prevent division by zero
            return
        
        # Normalize collision vector
        nx = dx / distance
        ny = dy / distance
        
        # Separate marbles to prevent overlap
        overlap = (self.radius + other.radius) - distance
        if overlap > 0:
            separation = overlap / 2
            self.x -= nx * separation
            self.y -= ny * separation
            other.x += nx * separation
            other.y += ny * separation
        
        # Calculate relative velocity in collision normal direction
        relative_velocity_x = other.velocity_x - self.velocity_x
        relative_velocity_y = other.velocity_y - self.velocity_y
        velocity_along_normal = relative_velocity_x * nx + relative_velocity_y * ny
        
        # Don't resolve if velocities are separating
        if velocity_along_normal > 0:
            return
        
        # Calculate impulse (assuming equal mass and perfectly elastic collision)
        impulse = velocity_along_normal
        
        # Update velocities
        self.velocity_x += impulse * nx
        self.velocity_y += impulse * ny
        other.velocity_x -= impulse * nx
        other.velocity_y -= impulse * ny
        
        # Ensure constant speed is maintained
        self._normalize_velocity()
        other._normalize_velocity()
    
    def _normalize_velocity(self):
        """Ensure velocity magnitude equals the desired speed"""
        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > 0:
            self.velocity_x = (self.velocity_x / current_speed) * self.speed
            self.velocity_y = (self.velocity_y / current_speed) * self.speed


class MarbleSimulation:
    def __init__(self, num_marbles: int = 8, arena_width: int = 800, arena_height: int = 600):
        self.num_marbles = num_marbles
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.marble_radius = 15
        self.marble_speed = 100  # pixels per second
        self.marbles: List[Marble] = []
        self.simulation_time = 0.0
        self.max_simulation_time = 10.0  # 10 seconds
        
        # Initialize marbles
        self._create_marbles()
    
    def _create_marbles(self):
        """Create marbles with random positions that don't overlap"""
        for i in range(self.num_marbles):
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                x = random.uniform(self.marble_radius, self.arena_width - self.marble_radius)
                y = random.uniform(self.marble_radius, self.arena_height - self.marble_radius)
                
                # Check if this position overlaps with existing marbles
                valid_position = True
                for existing_marble in self.marbles:
                    distance = math.sqrt((x - existing_marble.x)**2 + (y - existing_marble.y)**2)
                    if distance < (self.marble_radius + existing_marble.radius + 5):  # 5px buffer
                        valid_position = False
                        break
                
                if valid_position:
                    marble = Marble(x, y, self.marble_radius, (0,255,0), self.marble_speed)
                    self.marbles.append(marble)
                    break
                
                attempts += 1
    
    def update(self, dt: float):
        """Update simulation state"""
        self.simulation_time += dt
        
        # Update all marbles
        for marble in self.marbles:
            marble.update(dt, self.arena_width, self.arena_height)
        
        # Handle marble-to-marble collisions
        for i in range(len(self.marbles)):
            for j in range(i + 1, len(self.marbles)):
                if self.marbles[i].check_collision(self.marbles[j]):
                    self.marbles[i].resolve_collision(self.marbles[j])
    
    def is_finished(self) -> bool:
        """Check if simulation should end"""
        return self.simulation_time >= self.max_simulation_time


class GraphicsRenderer:
    def __init__(self, simulation: MarbleSimulation):
        pygame.init()
        self.simulation = simulation
        self.screen = pygame.display.set_mode((simulation.arena_width, simulation.arena_height))
        pygame.display.set_caption("Marble Race Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
    
    def render(self):
        """Render the current simulation state"""
        # Clear screen
        self.screen.fill((50, 50, 50))  # Dark gray background
        
        # Draw arena border
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (0, 0, self.simulation.arena_width, self.simulation.arena_height), 2)
        
        # Draw marbles
        for marble in self.simulation.marbles:
            pygame.draw.circle(self.screen, marble.color, 
                             (int(marble.x), int(marble.y)), marble.radius)
            # Draw a small white dot in the center for visibility
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (int(marble.x), int(marble.y)), 2)
        
        # Draw simulation info
        time_text = self.font.render(f"Time: {self.simulation.simulation_time:.1f}s", True, (255, 255, 255))
        self.screen.blit(time_text, (10, 10))
        
        pygame.display.flip()
    
    def handle_events(self) -> bool:
        """Handle pygame events, return False if should quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True
    
    def get_dt(self) -> float:
        """Get delta time in seconds"""
        return self.clock.tick(24) / 1000.0  # 24 FPS


def run_graphics_mode(num_marbles: int):
    """Run simulation with graphics"""
    print(f"Starting marble simulation with {num_marbles} marbles (Graphics Mode)")
    print("Press ESC or close window to exit early")
    
    simulation = MarbleSimulation(num_marbles)
    renderer = GraphicsRenderer(simulation)
    
    running = True
    while running and not simulation.is_finished():
        dt = renderer.get_dt()
        
        # Handle events
        running = renderer.handle_events()
        
        # Update simulation
        simulation.update(dt)
        
        # Render
        renderer.render()
    
    pygame.quit()
    print(f"Simulation completed in {simulation.simulation_time:.2f} seconds")


def run_headless_mode(num_marbles: int):
    """Run simulation without graphics"""
    print(f"Starting marble simulation with {num_marbles} marbles (Headless Mode)")
    
    simulation = MarbleSimulation(num_marbles)
    
    # Fixed timestep for consistent simulation
    dt = 1.0 / 60.0  # 60 FPS simulation rate
    frames = 0
    
    start_time = time.time()
    
    while not simulation.is_finished():
        simulation.update(dt)
        frames += 1
        
        # Print progress every second
        if frames % 60 == 0:
            print(f"Simulation time: {simulation.simulation_time:.1f}s")
    
    end_time = time.time()
    print(f"Simulation completed in {simulation.simulation_time:.2f} seconds")
    print(f"Real time elapsed: {end_time - start_time:.2f} seconds")
    print(f"Simulated {frames} frames")
