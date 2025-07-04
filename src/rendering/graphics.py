"""
Graphics rendering for the marble race simulation.
"""

import pygame
from typing import TYPE_CHECKING
from config import get_config

if TYPE_CHECKING:
    from simulation.manager import SimulationManager


class GraphicsRenderer:
    """Handles all pygame-based graphics rendering"""
    
    def __init__(self, simulation: 'SimulationManager'):
        pygame.init()
        self.simulation = simulation
        self.screen = pygame.display.set_mode((simulation.arena_width, simulation.arena_height))
        pygame.display.set_caption("Marble Race Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
    
    def render(self):
        """Render the current simulation state"""
        # Always use black background
        self.screen.fill((0, 0, 0))
        # Draw arena border
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (0, 0, self.simulation.arena_width, self.simulation.arena_height), 2)
        # Draw terrain with its color scheme
        self.simulation.terrain_generator.render_terrain(self.screen)
        
        # Draw zones if available
        spawn_zone, goal_zone = self.simulation.get_zones()
        if spawn_zone:
            # Draw spawn zone in green with transparency
            spawn_surface = pygame.Surface((spawn_zone.radius * 2, spawn_zone.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(spawn_surface, (0, 255, 0, 80), 
                             (spawn_zone.radius, spawn_zone.radius), spawn_zone.radius)
            self.screen.blit(spawn_surface, 
                           (spawn_zone.center_x - spawn_zone.radius, spawn_zone.center_y - spawn_zone.radius))
            # Draw spawn zone border
            pygame.draw.circle(self.screen, (0, 255, 0), 
                             (int(spawn_zone.center_x), int(spawn_zone.center_y)), 
                             int(spawn_zone.radius), 2)
        
        if goal_zone:
            # Draw goal zone in red with transparency
            goal_surface = pygame.Surface((goal_zone.radius * 2, goal_zone.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(goal_surface, (255, 0, 0, 80), 
                             (goal_zone.radius, goal_zone.radius), goal_zone.radius)
            self.screen.blit(goal_surface, 
                           (goal_zone.center_x - goal_zone.radius, goal_zone.center_y - goal_zone.radius))
            # Draw goal zone border
            pygame.draw.circle(self.screen, (255, 0, 0), 
                             (int(goal_zone.center_x), int(goal_zone.center_y)), 
                             int(goal_zone.radius), 2)
        
        # Draw marbles
        for i, marble in enumerate(self.simulation.marbles):
            pygame.draw.circle(self.screen, marble.color, 
                             (int(marble.x), int(marble.y)), marble.radius)
            # Draw a small white dot in the center for visibility
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (int(marble.x), int(marble.y)), 2)
            
            # Highlight winner marble
            if self.simulation.get_winner() == i:
                pygame.draw.circle(self.screen, (255, 255, 0), 
                                 (int(marble.x), int(marble.y)), marble.radius + 5, 3)
        
        # Draw simulation info
        time_text = self.font.render(f"Time: {self.simulation.simulation_time:.1f}s", True, (255, 255, 255))
        self.screen.blit(time_text, (10, 10))
        
        # Draw winner info if game is finished
        if self.simulation.is_finished():
            winner_id = self.simulation.get_winner()
            if winner_id is not None:
                winner_text = self.font.render(f"Marble {winner_id} WINS!", True, (255, 255, 0))
                text_rect = winner_text.get_rect(center=(self.simulation.arena_width // 2, 50))
                self.screen.blit(winner_text, text_rect)
        
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
        cfg = get_config()
        return self.clock.tick(cfg.simulation.GRAPHICS_FPS) / 1000.0
