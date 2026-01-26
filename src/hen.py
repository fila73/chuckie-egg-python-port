"""Enemy entities: Hens (ostriches) and Mother Duck."""
import pygame
from .constants import *

# Hen spawn data per level (X, Y, direction, reserved) - all 5 positions
# Direction: 1=left, 2=right, 3=up, 4=down
HEN_SPAWN_DATA = {
    1: [(0x68, 0x88, 2, 0), (0x48, 0x68, 1, 0), (0x40, 0x48, 1, 0), (0x98, 0x08, 2, 0), (0x48, 0x28, 1, 0)],
    2: [(0x10, 0x08, 2, 0), (0x48, 0x88, 2, 0), (0xE0, 0x48, 2, 0), (0x90, 0x48, 1, 0), (0xA8, 0x88, 1, 0)],
    3: [(0x10, 0x68, 1, 0), (0xE8, 0x20, 1, 0), (0x70, 0x80, 2, 0), (0x64, 0x50, 3, 0), (0x28, 0x04, 1, 0)],
    4: [(0x10, 0x28, 1, 0), (0xD8, 0x08, 2, 0), (0xD8, 0x88, 2, 0), (0x78, 0x88, 2, 0), (0x58, 0x08, 1, 0)],
    5: [(0x10, 0x28, 1, 0), (0x28, 0x48, 2, 0), (0x28, 0x68, 1, 0), (0xA8, 0x48, 2, 0), (0xE0, 0x08, 2, 0)],
    6: [(0x18, 0x08, 1, 0), (0x18, 0x68, 1, 0), (0xC0, 0x28, 2, 0), (0xE8, 0x68, 2, 0), (0xA0, 0x48, 2, 0)],
    7: [(0xC8, 0x88, 1, 0), (0x58, 0x08, 1, 0), (0xBC, 0x40, 3, 0), (0x28, 0x68, 2, 0), (0x18, 0x08, 1, 0)],
    8: [(0x7C, 0x70, 4, 0), (0x7C, 0x30, 4, 0), (0xA0, 0x08, 1, 0), (0x38, 0x48, 1, 0), (0xC0, 0x48, 2, 0)],
}

# Number of active hens per level in first playthrough
HEN_ACTIVE_COUNT = {
    1: 2, 2: 2, 3: 3, 4: 4, 5: 2, 6: 3, 7: 4, 8: 0
}

class Hen:
    """A hen/ostrich enemy that walks on platforms and climbs ladders."""
    
    DIR_LEFT = 1
    DIR_RIGHT = 2
    DIR_UP = 3
    DIR_DOWN = 4
    
    def __init__(self, x, y, direction, resources):
        self.x = x * SCALE
        # Invert Y logic: 192 (Height) - 16 (Sprite) - Y = 176 - Y
        self.y = (176 - y) * SCALE
        self.direction = direction
        self.resources = resources
        self.frame = 0
        self.frame_counter = 0
        self.speed = 1
        self.accumulator = 0.0
        self.active = True
        
        # Create rect for collision
        self.rect = pygame.Rect(self.x, self.y, 16 * SCALE, 16 * SCALE)

    # Note: _move_horizontal and _climb_vertical logic remains relative.
    # But coordinate checks might need adjustment if bounding box changed.
    # Bounding box is same size (16x16).

    # ... [Keep update methods same, just updating draw] ...


    def pixel_to_row(self, y_pixel):
        """Convert pixel Y coordinate to grid row."""
        return int((y_pixel - MAP_OFFSET_Y * SCALE) // (8 * SCALE))

    def pixel_to_col(self, x_pixel):
        """Convert pixel X coordinate to grid column."""
        return int(x_pixel // (8 * SCALE))

    def update(self, level, junction_counter):
        """Update hen position and AI."""
        if not self.active:
            return
            
        # Animation
        self.frame_counter += 1
        if self.frame_counter >= 8:
            self.frame_counter = 0
            self.frame = (self.frame + 1) % 4
            
        # Movement based on direction
        if self.direction == self.DIR_RIGHT:
            self._move_horizontal(level, 1, junction_counter)
        elif self.direction == self.DIR_LEFT:
            self._move_horizontal(level, -1, junction_counter)
        elif self.direction == self.DIR_UP:
            self._climb_vertical(level, -1)
        elif self.direction == self.DIR_DOWN:
            self._climb_vertical(level, 1)
            
        # Update rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def _move_horizontal(self, level, dx, junction_counter):
        """Move horizontally on platforms."""
        # Calculate next X
        new_x = self.x + dx * self.speed
        
        # Check screen bounds
        if new_x < 0 or new_x > (256 - 16) * SCALE:
            self._reverse_direction()
            return
            
        # Calculate current grid position (using center for column)
        cx = new_x + 8 * SCALE
        c = self.pixel_to_col(cx)
        
        # Row is determined by feet/bottom-ish
        # Hen is 16px high. If standing on row R, feet are at (R+1)*8?
        # Player check: r_bottom = pixel_to_row(rect.bottom - 1 - offset)
        # Here we use top-left y. 
        # y represents top-left. +16 is bottom.
        # If standing on floor, bottom aligns with grid.
        # so r = pixel_to_row(y + 16 - small_offset)
        r = self.pixel_to_row(self.y + 16 * SCALE - 1)
        
        # Bound checks
        if r < 0 or r >= len(level.grid) or c < 0 or c >= len(level.grid[0]):
             self._reverse_direction()
             return

        # 1. Check if we ran off the platform
        tile_below = level.grid[r][c]
        if tile_below not in [TILE_FLOOR, TILE_LADDER_L, TILE_LADDER_R]:
             # Only reverse if we are predominantly over the empty tile
             # i.e. our center has crossed into empty space? 
             # OR if the leading edge has?
             # Simple check: Flip if center is over void.
             self._reverse_direction()
             return

        # 2. Check for Ladder Junctions (mimic Player Step 3)
        # Check if we are passing a ladder.
        # Check tile at feet level (should be standing ON it or AT it?)
        # If we are walking, we are AT row 'r-1' effectively? No, standing on 'r'.
        # Tile 'r' is floor/ladder-top.
        # Ladder Up: Tile at 'r-1' (Head level) is Ladder.
        # Ladder Down: Tile at 'r+1' (Below feet) is Ladder.
        
        # Determine current column center X
        target_center_x = c * 8 * SCALE + 4 * SCALE # Wait, Hen is 16px. 
        # Hen Center = x + 8. 
        # Tile Center = c * 8 + 4.
        # Player logic: rect.centerx == target_center_x
        # But for Hen (width 16) vs Player (width 16).
        # Ladder is 8px wide.
        # My previous alignment fixes assumed Left Alignment.
        # User wants "copy from harry". Harry uses `pixel_to_col(self.rect.centerx)`.
        # And `target_center_x` depends on LADDER_L or R. 
        # But hens treat TILE_LADDER_L/R similarly in my code context.
        # Assuming we just align with the grid column `c`.
        
        # Check alignment narrowly
        # If we are close to being centered on column 'c'?
        # Or aligned with grid boundary? `new_x % (8*SCALE) == 0`.
        
        if int(new_x) % (8 * SCALE) == 0:
             # Aligned grid-wise.
             # Check for ladder possibilities
             can_go_up = (r > 0) and level.grid[r-1][c] in [TILE_LADDER_L, TILE_LADDER_R]
             can_go_down = (r < len(level.grid) - 1) and level.grid[r+1][c] in [TILE_LADDER_L, TILE_LADDER_R]
             
             if (can_go_up or can_go_down) and (junction_counter & 0x04): # Chance to take it
                  # Decide
                  want_up = False
                  want_down = False
                  
                  if (junction_counter & 0x02): # Prefer Up
                      if can_go_up: want_up = True
                      elif can_go_down: want_down = True
                  else: # Prefer Down
                      if can_go_down: want_down = True
                      elif can_go_up: want_up = True
                      
                  if want_up:
                       self.direction = self.DIR_UP
                       self.x = new_x # Snap X
                       return
                  elif want_down:
                       self.direction = self.DIR_DOWN
                       self.x = new_x # Snap X
                       return

        self.x = new_x
        
    def _climb_vertical(self, level, dy):
        """Climb up or down a ladder."""
        new_y = self.y + dy * self.speed
        
        # Bound checks
        if new_y < MAP_OFFSET_Y * SCALE or new_y > (168 + MAP_OFFSET_Y) * SCALE:
            # Reached screen bounds, force off
            self.direction = self.DIR_RIGHT if (self.frame % 2) else self.DIR_LEFT
            return

        # Check for grid alignment (Sideways Exit Opportunity)
        # Mimic Player Step 5: "Sideways Exit"
        # Must be aligned vertically with a "floor row".
        # rect.bottom % 8 == 0.
        # Here `self.y` is top. `self.y + 16` is bottom.
        
        check_y = new_y + 16 * SCALE # Bottom
        
        if int(check_y - MAP_OFFSET_Y * SCALE) % (8 * SCALE) == 0:
             # Using int() to avoid float precision issues, though speed is 1.0.
             
             r = self.pixel_to_row(check_y - 1) # row above the line (the row we are in)
             c = self.pixel_to_col(self.x + 8 * SCALE) # Center column
             
             # Check Left Exit
             # Player checks `c - 2`. Why 2? 
             # Player width 16 (2 tiles). Center is at `c`. Left is `c-1`.
             # Tile to the left of the player is `c-2`?
             # Let's check `c-1`.
             # If Tile(r, c-1) is Floor, we can go left.
             can_left = c > 0 and level.grid[r][c-1] == TILE_FLOOR
             can_right = c < len(level.grid[0]) - 1 and level.grid[r][c+1] == TILE_FLOOR
             
             # Also check if we ran out of ladder (Topping out / Bottoming out)
             # If going UP and tile at Head (r-1?) isn't ladder -> Forced exit
             # Head is `new_y`. Row is `pixel_to_row(new_y)`.
             # `r` calculated above is feet row? No, `check_y - 1` is bottom-1.
             # So `r` is the tile the body occupies (bottom half).
             
             # Check "End of Ladder" condition
             tile_here = level.grid[r][c]
             if tile_here not in [TILE_LADDER_L, TILE_LADDER_R]:
                  # We are NOT on a ladder anymore? 
                  # Or we just climbed past it.
                  # If we are not on a ladder, we MUST exit.
                  pass # Logic below handles direction choice

             # AI Decision:
             # Randomly decide or forced?
             # If end of ladder, forced.
             # If junction, random.
             
             should_exit = False
             
             # Check if we ARE on local ladder tile
             on_ladder = tile_here in [TILE_LADDER_L, TILE_LADDER_R]
             
             if not on_ladder:
                  should_exit = True
             elif can_left or can_right:
                  # Chance to exit sideways?
                  if (self.frame_counter & 0x04): # Reuse random-ish counter
                       should_exit = True
                       
             if should_exit:
                  # Pick direction
                  if can_left and can_right:
                       self.direction = self.DIR_LEFT if (self.frame_counter % 2) else self.DIR_RIGHT
                  elif can_left:
                       self.direction = self.DIR_LEFT
                  elif can_right:
                       self.direction = self.DIR_RIGHT
                  else:
                       # Stuck? Or end of ladder with no floor?
                       # Falling? Hens don't fall usually?
                       # If no floor, maybe turn around (reverse vert)?
                       # Or just force Right (default fall-back).
                       self.direction = self.DIR_RIGHT 
                       
                  # Snap Y
                  # We want bottom to be on grid line.
                  # check_y is exactly on grid line (from if condition).
                  # so new_y is correct.
                  self.y = new_y
                  return
                  
        self.y = new_y

    def _at_ladder_junction(self, level, x_pos, row):
        """Check if hen is at a ladder junction with strict alignment."""
        # Calculate column based on center? No, based on loose position first.
        col = int((x_pos + 8 * SCALE) // (8 * SCALE))
        
        if col < 0 or col >= len(level.grid[0]) or row < 0 or row >= len(level.grid):
            return False
            
        tile = level.grid[row][col] if row < len(level.grid) else TILE_EMPTY
        if tile not in [TILE_LADDER_L, TILE_LADDER_R]:
            return False
            
        # STRICT ALIGNMENT CHECK
        target_x = col * 8 * SCALE
        
        diff = abs(x_pos - target_x)
        return diff < self.speed + 0.1 # Tolerance
        
    def _decide_junction(self, level, col, row, counter):
        """Decide which direction to take at a junction."""
        # User: "po dílku se žebříkem se dá chodit jako po podlaze"
        # Hens shouldn't ALWAYS turn.
        # Add a chance to just keep walking (ignore junction).
        # Using counter bit 2 (0x04) allows turning only periodically.
        if (counter & 0x04) == 0: 
            return # Keep walking
            
        can_go_up = row > 0 and level.grid[row - 1][col] in [TILE_LADDER_L, TILE_LADDER_R]
        can_go_down = row < len(level.grid) - 1 and level.grid[row + 1][col] in [TILE_LADDER_L, TILE_LADDER_R]
        
        if counter & 0x02:  # bit 1 set - prefer UP
            if can_go_up:
                self.direction = self.DIR_UP
            elif can_go_down:
                self.direction = self.DIR_DOWN
        else:  # prefer DOWN
            if can_go_down:
                self.direction = self.DIR_DOWN
            elif can_go_up:
                self.direction = self.DIR_UP
                
    def _reverse_direction(self):
        """Reverse horizontal direction."""
        if self.direction == self.DIR_RIGHT:
            self.direction = self.DIR_LEFT
        elif self.direction == self.DIR_LEFT:
            self.direction = self.DIR_RIGHT

    def check_collision(self, player):
        """Check if hen collides with player."""
        return self.active and self.rect.colliderect(player.rect)

    def draw(self, screen):
        """Draw the hen sprite."""
        if not self.active:
            return
            
        # Get sprite based on direction and frame
        # Frames 0-3 for walk
        # Frames 0-1 for climb (reused)
        if self.direction in [self.DIR_UP, self.DIR_DOWN]:
            sprite_key = f'hen_climb_{self.frame % 2}'
        elif self.direction == self.DIR_LEFT:
            sprite_key = f'hen_left_{self.frame % 4}'
        else:
            sprite_key = f'hen_right_{self.frame % 4}'
            
        # Get sprite
        sprite = self.resources.sprites.get(sprite_key)
        if not sprite:
            # Fallback
            pygame.draw.rect(screen, COLOR_CYAN, self.rect)
            return
            
        # Calculate draw position with offset for walk frames
        draw_x = int(self.x)
        if self.direction in [self.DIR_LEFT, self.DIR_RIGHT]:
            # Walk frames are 1 and 3 (0=stand, 1=walk, 2=stand, 3=walk)
            if self.frame in [1, 3]:
                # User: walk sprity jsou o 4 pixely posunuty doprava -> Shift Left by 4
                draw_x -= 4 * SCALE
                
        screen.blit(pygame.transform.scale(sprite, (16 * SCALE, 16 * SCALE)), (draw_x, int(self.y)))


class MotherDuck:
    """The Mother Duck (big hen) that chases Harry with inertia."""
    
    CAGE_X = 0 # User requested move left 1 tile (was 8)
    CAGE_Y = 152 
    # Inverted Y logic applied in init/reset: 176 - 152 = 24 (Top)
    
    def __init__(self, resources):
        self.resources = resources
        self.active = False
        self.reset() # This sets x, y 
        
        # Create rect for collision
        self.rect = pygame.Rect(self.x, self.y, 16 * SCALE, 16 * SCALE)
        
        self.velocity_x = 0
        self.velocity_y = 0
        self.frame = 0
        self.frame_counter = 0
        self.move_timer = 0
        
    def activate(self, cleared_levels):
        """Activate duck based on cleared levels."""
        self.active = cleared_levels >= 8
        if not self.active:
            self.reset()
            
    def reset(self):
        """Reset duck to cage position."""
        self.x = (self.CAGE_X + 8) * SCALE
        # User: kachna pak má být o 2 dlaždice níž než je teď (kde je klec)
        # Cage is at CAGE_Y. Duck spawns at CAGE_Y + 16 (2 tiles).
        # Inverted Y: 152 - (CAGE_Y + 16)? Or just shift relative to screen?
        # If CAGE_Y is the top of the cage (handle).
        # Cage Handle (8px) + Cage Body (16px?).
        # Let's assume Cage is visual background. Duck spawns "in" or "below" it?
        # "kachna pak má být o 2 dlaždice níž" -> 16 pixels lower.
        
        # Original logic: y = (152 - CAGE_Y) ...
        # If CAGE_Y=152, y=0.
        # If we want it lower (visually down on screen), Y increases.
        # In inverted coords (if Y is increasing UP?), then Y decreases?
        # User said "Y pozici ... máš opět obráceně". I fixed that with (152 - y).
        # So (152 - y) puts 152 at 0 (Top). 0 at 152 (Bottom).
        # If I want it 16px LOWER on SCREEN:
        # Screen Y increases downwards.
        # My `self.y` is screen coordinate.
        # So I just add 16 * SCALE to the final result.
        
        cage_screen_y = (152 - self.CAGE_Y) * SCALE + MAP_OFFSET_Y * SCALE
        self.y = (cage_screen_y - 32) * SCALE
        
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self, harry_x, harry_y, cleared_levels):
        """Update duck position with inertia physics."""
        # Animation
        self.frame_counter += 1
        if self.frame_counter >= 6:
            self.frame_counter = 0
            self.frame = (self.frame + 1) % 2
            
        # For levels < 8, stay in cage area (but hidden or just floating?)
        # "Levels 8-15: Duck only". Levels < 8: Hens only.
        # If inactive, we should probably hide it or keep it at spawn.
        if cleared_levels < 8:
            self.reset() # Keep resetting to spawn
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
            return
            
        # Movement timer (original game updates duck every 12 frames)
        if self.move_timer > 0:
            self.move_timer -= 1
            return

        self.move_timer = 12

        # 1. Accelerate towards Harry
        # Original speed: Max speed is 6. Acceleration is 1.
        limit = 6 * SCALE 
        
        if self.x > harry_x:
            self.velocity_x = max(self.velocity_x - 1 * SCALE, -limit) 
        elif self.x < harry_x:
            self.velocity_x = min(self.velocity_x + 1 * SCALE, limit) 
            
        if self.y > harry_y:
            self.velocity_y = max(self.velocity_y - 1 * SCALE, -limit) 
        elif self.y < harry_y:
            self.velocity_y = min(self.velocity_y + 1 * SCALE, limit)
            
        # 2. Apply velocity to position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 3. Bounce off screen edges
        # Define edges in screen coordinates
        right_edge = (SCREEN_WIDTH - 16) * SCALE
        left_edge = 0
        bottom_edge = (192 - 16) * SCALE
        top_edge = 0
        
        if self.x > right_edge:
            self.x = right_edge
            if self.velocity_x > 0:
                self.velocity_x = -self.velocity_x
        elif self.x < left_edge:
            self.x = left_edge
            if self.velocity_x < 0:
                self.velocity_x = -self.velocity_x
            
        if self.y > bottom_edge:
            self.y = bottom_edge
            if self.velocity_y > 0:
                self.velocity_y = -self.velocity_y
        elif self.y < top_edge:
            self.y = top_edge
            if self.velocity_y < 0:
                self.velocity_y = -self.velocity_y
            
        # Update rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def check_collision(self, player):
        """Check if duck collides with player."""
        return self.active and self.rect.colliderect(player.rect)
        
    def draw_cage(self, screen):
        """Draw the cage background."""
        # Cage Handle at CAGE_Y (Screen Y)
        # Cage Body below it.
        # Use CAGE_X, CAGE_Y.
        screen_x = self.CAGE_X * SCALE
        screen_y = (152 - self.CAGE_Y) * SCALE + MAP_OFFSET_Y * SCALE
        
        # Draw Handle
        handle = self.resources.sprites.get('cage_handle')
        if handle:
            # Handle is likely 16x8 or similar? 
            # gfx_tile_birdcage_handle.png (107 bytes)
            # Assuming 16x8 based on typical tiles.
            screen.blit(pygame.transform.scale(handle, (16 * SCALE, 8 * SCALE)), (screen_x + 8 * SCALE, screen_y))
            
        # Draw Cage Body
        # gfx_tile_birdcage.png (247 bytes)
        # Assuming 16x16?
        cage = self.resources.sprites.get('cage')
        if cage:
            screen.blit(pygame.transform.scale(cage, (32 * SCALE, 32 * SCALE)), (screen_x, screen_y + 8 * SCALE))

    def draw(self, screen):
        """Draw the mother duck sprite."""
        # Get sprite based on direction (velocity_x)
        if self.velocity_x < 0:
            sprite_key = f'duck_left_{self.frame % 2}'
        else:
            sprite_key = f'duck_right_{self.frame % 2}'
            
        sprite = self.resources.sprites.get(sprite_key)
        
        if not sprite:
            # Fallback
            color = COLOR_YELLOW
            pygame.draw.rect(screen, color, self.rect)
            return
            
        screen.blit(pygame.transform.scale(sprite, (16 * SCALE, 16 * SCALE)), (int(self.x), int(self.y)))


def get_active_hen_count(level_num, cleared_levels):
    """Get number of active hens based on level and progression."""
    level_index = ((level_num - 1) % 8) + 1
    
    if cleared_levels < 8:
        # First playthrough - use per-level count
        return HEN_ACTIVE_COUNT.get(level_index, 2)
    elif cleared_levels < 16:
        # Second playthrough - no hens (only duck)
        return 0
    elif cleared_levels < 24:
        # Third playthrough - normal hen count + duck
        return HEN_ACTIVE_COUNT.get(level_index, 2)
    else:
        # Fourth+ playthrough - all 5 hens + duck
        return 5


def spawn_hens(level_num, cleared_levels, resources):
    """Spawn hens for the current level."""
    level_index = ((level_num - 1) % 8) + 1
    spawn_data = HEN_SPAWN_DATA.get(level_index, [])
    active_count = get_active_hen_count(level_num, cleared_levels)
    
    hens = []
    for i, (x, y, direction, _) in enumerate(spawn_data):
        if i < active_count:
            hens.append(Hen(x, y, direction, resources))
            
    return hens
