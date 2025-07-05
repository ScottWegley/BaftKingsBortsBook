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
            spawn_surface = pygame.Surface((spawn_zone.radius * 2, spawn_zone.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(spawn_surface, (0, 255, 0, 80), 
                             (spawn_zone.radius, spawn_zone.radius), spawn_zone.radius)
            self.screen.blit(spawn_surface, 
                           (spawn_zone.center_x - spawn_zone.radius, spawn_zone.center_y - spawn_zone.radius))
            pygame.draw.circle(self.screen, (0, 255, 0), 
                             (int(spawn_zone.center_x), int(spawn_zone.center_y)), 
                             int(spawn_zone.radius), 2)

        if goal_zone:
            goal_surface = pygame.Surface((goal_zone.radius * 2, goal_zone.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(goal_surface, (255, 0, 0, 80), 
                             (goal_zone.radius, goal_zone.radius), goal_zone.radius)
            self.screen.blit(goal_surface, 
                           (goal_zone.center_x - goal_zone.radius, goal_zone.center_y - goal_zone.radius))
            pygame.draw.circle(self.screen, (255, 0, 0), 
                             (int(goal_zone.center_x), int(goal_zone.center_y)), 
                             int(goal_zone.radius), 2)

        # Draw marbles as characters if available
        import os
        from pygame import image, Surface
        char_list = getattr(self.simulation, 'characters', None)
        for i, marble in enumerate(self.simulation.marbles):
            char = char_list[i] if char_list and i < len(char_list) else None
            if char:
                costume = 'default'
                asset_path = os.path.join('assets', 'characters', char.id, f'{costume}.png')
                if os.path.exists(asset_path):
                    char_img = image.load(asset_path).convert_alpha()
                    char_img = pygame.transform.smoothscale(char_img, (marble.radius*2, marble.radius*2))
                    self.screen.blit(char_img, (int(marble.x-marble.radius), int(marble.y-marble.radius)))
                else:
                    pygame.draw.circle(self.screen, marble.color, (int(marble.x), int(marble.y)), marble.radius)
            else:
                pygame.draw.circle(self.screen, marble.color, (int(marble.x), int(marble.y)), marble.radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(marble.x), int(marble.y)), 2)
            if self.simulation.get_winner() == i:
                pygame.draw.circle(self.screen, (255, 255, 0), (int(marble.x), int(marble.y)), marble.radius + 5, 3)

        # Draw simulation info
        time_text = self.font.render(f"Time: {self.simulation.simulation_time:.1f}s", True, (255, 255, 255))
        self.screen.blit(time_text, (10, 10))

        # Draw winner info if game is finished
        if self.simulation.is_finished():
            winner_id = self.simulation.get_winner()
            winner_name = None
            if hasattr(self.simulation, 'get_winner_character_name'):
                winner_name = self.simulation.get_winner_character_name()
            if winner_id is not None:
                if winner_name:
                    winner_text = self.font.render(f"{winner_name} WINS!", True, (255, 255, 0))
                else:
                    winner_text = self.font.render(f"Marble {winner_id} WINS!", True, (255, 255, 0))
                text_rect = winner_text.get_rect(center=(self.simulation.arena_width // 2, 50))
                # Draw black rectangle background behind the text
                padding = 16
                bg_rect = text_rect.inflate(padding, padding)
                pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
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
