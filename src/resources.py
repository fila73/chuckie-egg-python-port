
import pygame
import os
from .constants import *

class ResourceManager:
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.sprites = {}
        self.tiles = {}
        
    def load_image(self, filename):
        path = os.path.join(self.assets_dir, 'sprites', filename)
        try:
            surface = pygame.image.load(path).convert_alpha()
            return surface
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            return pygame.Surface((8, 8))

    def load_all(self):
        # Load raw images
        img_ladder = self.load_image('gfx_tile_ladder.png') # 16x8
        img_floor = self.load_image('gfx_tile_floor.png') # 8x8 or 8x48? Check extract log.
        img_egg = self.load_image('gfx_item_egg.png')
        img_corn = self.load_image('gfx_item_corn.png')
        
        # Check floor dims. Extract log said (8x48) in Step 300? 
        # "Saved gfx_tile_floor.png (8x48)"
        # Wait, floor tile is usually just one 8x8 tile repeated. 
        # Why 8x48? 
        # Skool: 
        # @label=gfx_tile_floor
        # b$8518 defb $fb,$00,$bf,$00,$ef,$00,$00,$00  (8 bytes)
        # 
        # Next matches? 
        # Skool (Step 269):
        # 542: ; Unknown ad unused?
        # 543: b$8520 defb $00...
        
        # Ah, my extractor reads until the next label.
        # "Unknown and unused" at 542 does NOT have a label!
        # So "gfx_tile_floor" swallowed the unused bytes!
        # So "gfx_tile_floor.png" is a tall strip. I should just use the top 8x8.
        
        # Create Tiles Mapping
        self.tiles[TILE_EMPTY] = None
        
        # Floor (take top 8x8)
        self.tiles[TILE_FLOOR] = img_floor.subsurface((0, 0, 8, 8))
        
        # Ladder (Split 16x8 into two 8x8)
        self.tiles[TILE_LADDER_L] = img_ladder.subsurface((0, 0, 8, 8))
        self.tiles[TILE_LADDER_R] = img_ladder.subsurface((8, 0, 8, 8))
        
        self.tiles[TILE_EGG] = img_egg
        self.tiles[TILE_CORN] = img_corn
        
        # Coloring
        # Tinting: Fill a surface with color and multiply?
        self.tiles[TILE_FLOOR] = self.tint(self.tiles[TILE_FLOOR], COLOR_GREEN) 
        self.tiles[TILE_LADDER_L] = self.tint(self.tiles[TILE_LADDER_L], COLOR_MAGENTA)
        self.tiles[TILE_LADDER_R] = self.tint(self.tiles[TILE_LADDER_R], COLOR_MAGENTA)
        self.tiles[TILE_EGG] = self.tint(self.tiles[TILE_EGG], COLOR_WHITE) 
        self.tiles[TILE_CORN] = self.tint(self.tiles[TILE_CORN], COLOR_MAGENTA)
        
    def tint(self, surface, color):
        # Create a copy
        colored = surface.copy()
        # Fill with color using special flags
        # If source is white on transparent:
        # We can fill check pixels.
        # Or: create a solid color surface and blit with masking.
        # Ideally: 
        # colored.fill(color, special_flags=pygame.BLEND_RGBA_MULT) 
        # But source needs to be white.
        # Yes, extract_graphics makes white pixels.
        colored.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        return colored
