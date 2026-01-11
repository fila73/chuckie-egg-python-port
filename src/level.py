
import pygame
import json
import os
from .constants import *

class Level:
    def __init__(self, resources):
        self.resources = resources
        self.grid = []
        self.levels_data = {}
        self.current_level_name = ""
        
    def load_data(self, data_path):
        with open(data_path, 'r') as f:
            self.levels_data = json.load(f)
            
    def set_level(self, level_name):
        if level_name in self.levels_data:
            self.current_level_name = level_name
            self.grid = self.levels_data[level_name]
        else:
            print(f"Level {level_name} not found.")

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
