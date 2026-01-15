
import pygame
import os
from .constants import *

class ResourceManager:
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.sprites = {}
        self.tiles = {}
        self.sounds = {}
        self.hud_assets = {}
        self.fonts = {}
        self.loading_screen = None
        
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
        
        # Load loading screen
        try:
            ls_path = os.path.join(self.assets_dir, 'graphics', 'loading_screen.png')
            self.loading_screen = pygame.image.load(ls_path).convert()
            # Scale to current screen scale
            orig_w, orig_h = self.loading_screen.get_size()
            self.loading_screen = pygame.transform.scale(self.loading_screen, (orig_w * SCALE, orig_h * SCALE))
        except Exception as e:
            print(f"Failed to load loading screen: {e}")

        # Load sounds
        sound_files = {
            'death': 'death_tune.wav',
            'walk': 'sfx_walk.wav',
            'climb': 'sfx_climb.wav',
            'collect': 'sfx_collect.wav',
            'jump': 'sfx_jump.wav',
            'bonus': 'sfx_bonus.wav'
        }
        for key, filename in sound_files.items():
            path = os.path.join(self.assets_dir, 'sounds', filename)
            try:
                self.sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Failed to load sound {filename}: {e}")
        
        # Load HUD Labels
        hud_labels = {
            'score': 'gfx_label_score.png',
            'player': 'gfx_label_player.png',
            'level': 'gfx_label_level.png',
            'bonus': 'gfx_label_bonus.png',
            'time': 'gfx_label_time.png',
            'lives': 'gfx_icon_lives.png'
        }
        for key, filename in hud_labels.items():
            img = self.load_image(filename)
            # Tint labels to White, lives to Yellow
            color = COLOR_YELLOW if key == 'lives' else COLOR_WHITE
            self.hud_assets[key] = self.tint(img, color)

        # Load Fonts
        img_font_all = self.load_image('font_all.png')
        img_font_nums = self.load_image('font_numbers_bold.png')
        
        # Slice font_all (Assume digits 0-9 are at index 16 if it's standard ASCII shift)
        self.fonts['score'] = []
        for i in range(10):
            # 8x472 -> 59 chars. Digit '0' is usually at index 16 (shift 32 from ' ')
            digit = img_font_all.subsurface((0, (16 + i) * 8, 8, 8))
            self.fonts['score'].append(self.tint(digit, COLOR_WHITE))
            
        # Slice font_numbers_bold (digits 0-9)
        self.fonts['data'] = []
        for i in range(10):
            digit = img_font_nums.subsurface((0, i * 8, 8, 8))
            self.fonts['data'].append(self.tint(digit, COLOR_WHITE))
        
        # Load Enemy Sprites (Ostrich / Hen) - Cyan
        # Walk Left
        self.sprites['hen_left_0'] = self.tint(self.load_image('sprites_ostrich_left.png'), COLOR_CYAN)
        self.sprites['hen_left_1'] = self.tint(self.load_image('sprites_ostrich_left_walk.png'), COLOR_CYAN)
        self.sprites['hen_left_2'] = self.sprites['hen_left_0'] # Cycle
        self.sprites['hen_left_3'] = self.sprites['hen_left_1'] # Cycle
        
        # Walk Right
        self.sprites['hen_right_0'] = self.tint(self.load_image('sprites_ostrich_right.png'), COLOR_CYAN)
        self.sprites['hen_right_1'] = self.tint(self.load_image('sprites_ostrich_right_walk.png'), COLOR_CYAN)
        self.sprites['hen_right_2'] = self.sprites['hen_right_0']
        self.sprites['hen_right_3'] = self.sprites['hen_right_1']
        
        # Climb (One sprite for now?)
        # User Correction: "sprites_ostrich_climbing.png jsou 2 pozice spritu nad sebou"
        img_climb_strip = self.load_image('sprites_ostrich_climbing.png')
        # Assume 16x16 frames, strip is 16x32
        self.sprites['hen_climb_0'] = self.tint(img_climb_strip.subsurface((0, 0, 16, 16)), COLOR_CYAN)
        self.sprites['hen_climb_1'] = self.tint(img_climb_strip.subsurface((0, 16, 16, 16)), COLOR_CYAN)

        # Mother Duck - Yellow
        # User Correction: "sprites_duck_left a sprites_duck_right jsou taky 2 sprity nad sebou"
        # Walk Left Strip
        duck_l_strip = self.load_image('sprites_duck_left.png')
        self.sprites['duck_left_0'] = self.tint(duck_l_strip.subsurface((0, 0, 16, 16)), COLOR_YELLOW)
        self.sprites['duck_left_1'] = self.tint(duck_l_strip.subsurface((0, 16, 16, 16)), COLOR_YELLOW)
        
        # Walk Right Strip
        duck_r_strip = self.load_image('sprites_duck_right.png')
        self.sprites['duck_right_0'] = self.tint(duck_r_strip.subsurface((0, 0, 16, 16)), COLOR_YELLOW)
        self.sprites['duck_right_1'] = self.tint(duck_r_strip.subsurface((0, 16, 16, 16)), COLOR_YELLOW)
        
        # Birdcage - Yellow
        self.sprites['cage'] = self.tint(self.load_image('gfx_tile_birdcage.png'), COLOR_YELLOW)
        self.sprites['cage_handle'] = self.tint(self.load_image('gfx_tile_birdcage_handle.png'), COLOR_YELLOW)
        
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

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self, name, loops=-1):
        if name == 'theme':
            path = os.path.join(self.assets_dir, 'sounds', 'theme_tune.wav')
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=loops)
        elif name in self.sounds:
            self.sounds[name].play(loops=loops)

    def stop_music(self, name):
        if name == 'theme':
            pygame.mixer.music.stop()
        elif name in self.sounds:
            self.sounds[name].stop()
