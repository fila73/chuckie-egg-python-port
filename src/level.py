
import pygame
import json
import os
from .constants import *
from .entities import Elevator

class Level:
    def __init__(self, resources):
        self.resources = resources
        self.grid = []
        self.levels_data = {}
        self.current_level_name = ""
        self.elevators = []  # List of Elevator instances
        
    def load_data(self, data_path):
        with open(data_path, 'r') as f:
            self.levels_data = json.load(f)
            
    def set_level(self, level_name):
        if level_name in self.levels_data:
            self.current_level_name = level_name
            self.grid = self.levels_data[level_name]
            self._init_elevators(level_name)
        else:
            print(f"Level {level_name} not found.")

    def _init_elevators(self, level_name):
        """Initialize elevators based on level name."""
        self.elevators = []
        
        # Elevator configurations for levels 3-7
        # Format: (center_x, y_top, y_bottom, speed, direction, start_offset)
        # start_offset: 0 = start at bottom, 0.5 = start in middle, etc.
        # Positions are in pixels (scaled)
        elevator_configs = {
            "level_3": [
                # Two elevators in the same column, 8 tiles apart
                # Column 4 (tile), range from row 0 to row 21 (full screen)
                (9 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.0),   # A: starts at bottom
                (9 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.38),  # B: starts ~8 tiles higher
            ],
            "level_4": [
                # Two elevators in the same column, 8 tiles apart
                # Column 4 (tile), range from row 0 to row 21 (full screen)
                (19 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.0),   # A: starts at bottom
                (19* 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.38),  # B: starts ~8 tiles higher
            ],
            "level_5": [
                # Two elevators in the same column, 8 tiles apart
                # Column 4 (tile), range from row 0 to row 21 (full screen)
                (26 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.0),   # A: starts at bottom
                (26 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.38),  # B: starts ~8 tiles higher
            ],
            "level_6": [
                # Two elevators in the same column, 8 tiles apart
                # Column 4 (tile), range from row 0 to row 21 (full screen)
                (16 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.0),   # A: starts at bottom
                (16 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.38),  # B: starts ~8 tiles higher
            ],
            "level_7": [
                # Two elevators in the same column, 8 tiles apart
                # Column 4 (tile), range from row 0 to row 21 (full screen)
                (31 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.0),   # A: starts at bottom
                (31 * 8 * SCALE, 0 * 8 * SCALE, 21 * 8 * SCALE, 1, -1, 0.38),  # B: starts ~8 tiles higher
            ],
            # Add more levels as needed
        }
        
        if level_name in elevator_configs:
            for cfg in elevator_configs[level_name]:
                x, y_top, y_bottom, speed, direction, start_offset = cfg
                elevator = Elevator(x, y_top, y_bottom, speed, direction)
                # Apply start offset
                total_range = y_bottom - y_top
                elevator.rect.y = y_bottom - int(total_range * start_offset) - elevator.rect.height
                self.elevators.append(elevator)
                
    def update_elevators(self):
        """Update all elevator positions."""
        for elevator in self.elevators:
            elevator.update()

    def draw(self, surface):
        if not self.grid:
            return
            
        # Draw grid
        for row_idx, row in enumerate(self.grid):
            for col_idx, tile_id in enumerate(row):
                if tile_id == TILE_EMPTY:
                    continue
                    
                tile_img = self.resources.tiles.get(tile_id)
                if tile_img:
                    # Calculate position
                    x = col_idx * 8 * SCALE
                    y = row_idx * 8 * SCALE
                    
                    # Scale tile?
                    # The assets are 8x8. We need to scale them to SCALE (3x).
                    # Better to scale them once in ResourceManager or scale blit.
                    # Pygame scale during blit is slow?
                    # Let's scale on load in ResourceManager is better, 
                    # but for now let's scale here to see it working.
                    
                    scaled_tile = pygame.transform.scale(tile_img, (8 * SCALE, 8 * SCALE))
                    surface.blit(scaled_tile, (x, y))
        
        # Draw elevators on top
        for elevator in self.elevators:
            elevator.draw(surface)

    def get_tile(self, col, row):
        if not self.grid: return TILE_EMPTY
        if row < 0 or row >= len(self.grid): return TILE_EMPTY
        if col < 0 or col >= len(self.grid[0]): return TILE_EMPTY
        return self.grid[row][col]
        
    def set_tile(self, col, row, tile_id):
        if not self.grid: return
        if row < 0 or row >= len(self.grid): return
        if col < 0 or col >= len(self.grid[0]): return
        self.grid[row][col] = tile_id
