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
    1: 2, 2: 2, 3: 3, 4: 4, 5: 2, 6: 3, 7: 4, 8: 5
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
        # Use simple speed for now. 
        new_x = self.x + dx * self.speed
        
        # Check screen bounds
        if new_x < 0 or new_x > (256 - 16) * SCALE:
            self._reverse_direction()
            return
            
        # Check for floor beneath
        col = int((new_x + 8 * SCALE) // (8 * SCALE))
        row = int((self.y + 16 * SCALE - MAP_OFFSET_Y * SCALE) // (8 * SCALE))
        
        if row >= 0 and row < len(level.grid) and col >= 0 and col < len(level.grid[0]):
            tile_below = level.grid[row][col] if row < len(level.grid) else TILE_EMPTY
            
            # Check if at ladder junction
            # STRICT alignment check inside _at_ladder_junction
            if self._at_ladder_junction(level, new_x, row): # Pass new_x
                self._decide_junction(level, col, row, junction_counter)
                if self.direction in [self.DIR_UP, self.DIR_DOWN]:
                    # Snap x to center of ladder (ensure visual alignment)
                    # Ladder tile left edge is col * 8 * SCALE.
                    # Hen is 16 wide. Center is +8. Ladder center is +4.
                    # Hen Left should be col * 8 * SCALE - 4 * SCALE? 
                    # If Hen center aligns with Ladder center:
                    # HenX + 8 = TileX + 4  => HenX = TileX - 4.
                    # BUT Harry is 16px wide too. Check Harry logic.
                    # Let's align LEFT edge of Hen to LEFT edge of Tile for now as that's simpler.
                    # Wait, Hen width 16. Ladder width 8.
                    # If Hen is centered: Hen Left is -4 from Tile Left.
                    # Let's trust strict alignment logic below to dictate "close enough".
                    # And SNAP to exactly aligned position.
                    # If _at_ladder check uses strict alignment, we are close.
                    # Just snap to "col * 8 * SCALE" if that's the canonical position? 
                    # Or "col * 8 * SCALE - 4 * SCALE"?
                    # Checking original code logic or just ensure it looks good.
                    # Let's align to col * 8 * SCALE for now (Left matching Left of tile).
                    # Actually if Hen is 2 tiles wide, and Ladder is 1 tile...
                    # If Hen is at X, it covers [X, X+16].
                    # Ladder at Col covers [Col*8, Col*8+8].
                    # Center alignment: X+8 = Col*8+4 => X = Col*8 - 4.
                    # Let's try X = Col*8 - 4 * SCALE.
                    # But if I use strict alignment check `abs(center_diff) < speed`,
                    # then I should snap to the target.
                    
                    # For now, simplistic snap to nearest tile boundary might be visually off if center is needed.
                    # I will snap to `col * 8 * SCALE` (tile boundary) to be safe and consistent with grid.
                    self.x = col * 8 * SCALE 
                    return 
                return
                
            # Check for edge of platform
            if tile_below not in [TILE_FLOOR, TILE_LADDER_L, TILE_LADDER_R]:
                self._reverse_direction()
                return
                
        self.x = new_x
        
    def _climb_vertical(self, level, dy):
        """Climb up or down a ladder."""
        new_y = self.y + dy * self.speed
        
        # Check screen bounds
        if new_y < MAP_OFFSET_Y * SCALE or new_y > (168 + MAP_OFFSET_Y) * SCALE:
            # Reached top or bottom, go back to walking
            self.direction = self.DIR_RIGHT if (self.frame % 2) else self.DIR_LEFT
            return
            
        # Check for ladder tile
        col = int((self.x + 8 * SCALE) // (8 * SCALE))
        row = int((new_y + 8 * SCALE - MAP_OFFSET_Y * SCALE) // (8 * SCALE))
        
        if row >= 0 and row < len(level.grid) and col >= 0 and col < len(level.grid[0]):
            tile = level.grid[row][col]
            
            if tile not in [TILE_LADDER_L, TILE_LADDER_R]:
                # Reached end of ladder, start walking
                self.direction = self.DIR_RIGHT if (self.frame % 2) else self.DIR_LEFT
                
                # Fix Y alignment
                # User: "bottom is srovnaná s bottom dílku žebříku (resp. platformy)"
                # "vyleze těsně pod platformou" -> previous was too low.
                # Previous was `row * 8`.
                # We want `Bottom == Tile.Bottom`.
                # y + 16 = row * 8 + 8 (Tile Bottom)
                # y = row * 8 - 8.
                self.y = (row * 8 - 8) * SCALE + MAP_OFFSET_Y * SCALE
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
        # "v jednom jediném bode, když jsou přesně zarovnané na stred zebriku"
        
        # Note: 4 * SCALE might imply Hen center is aligned with Ladder center.
        # But if the graphics are drawn such that Left edge aligns...
        # Let's assume Center-Center alignment is the requirement.
        
        target_x = (col * 8 - 4) * SCALE
        # Wait, if I align to -4, does it look right?
        # If I align to 0 (col * 8), Hen is shifted right relative to ladder center.
        # Let's try Strict Grid Alignment (x % 8 == 0) which is `col * 8 * SCALE`.
        # If that looks off, I'll adjust. 
        # But user said "aligned to center of ladder".
        # Ladder is 8px. Hen is 16px.
        # If Hen Left is at Grid Line, Hen spans [0, 16]. Center 8.
        # Tile spans [0, 8]. Center 4.
        # They are OFF by 4 pixels.
        # So Hen needs to be at -4 to align centers?
        # -4 spans [-4, 12]. Center 4. YES.
        # So `target_x = col * 8 * SCALE - 4 * SCALE`.
        
        # However, looking at my `spawn_hens` data...
        # Spawn X are hex values like 0x68, 0x48...
        # 0x68 = 104. 104 / 8 = 13.
        # 0x48 = 72. 72 / 8 = 9.
        # They seem to be character grid aligned (multiples of 8).
        # So Hens spawn ALIGNED TO GRID (Left edge at tile boundary).
        # So they probably walk ALIGNED TO GRID.
        # So I should enforce `x % 8 == 0`. ie. `abs(x_pos - col * 8 * SCALE) < speed`.
        
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
            
        # 1. Accelerate towards Harry
        if self.x > harry_x:
            self.velocity_x = max(self.velocity_x - 1, -6 * SCALE // 2)  # Accelerate left
        elif self.x < harry_x:
            self.velocity_x = min(self.velocity_x + 1, 5 * SCALE // 2)   # Accelerate right
            
        if self.y > harry_y:
            self.velocity_y = max(self.velocity_y - 1, -6 * SCALE // 2)  # Accelerate up
        elif self.y < harry_y:
            self.velocity_y = min(self.velocity_y + 1, 5 * SCALE // 2)   # Accelerate down
            
        # 2. Apply velocity to position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 3. Bounce off screen edges
        right_edge = (238 + MAP_OFFSET_Y) * SCALE 
        left_edge = 0
        bottom_edge = (166 + MAP_OFFSET_Y) * SCALE
        top_edge = (20 + MAP_OFFSET_Y) * SCALE
        
        if self.x > right_edge:
            self.x -= 2 * self.velocity_x
            self.velocity_x = -5 * SCALE // 2
        elif self.x < left_edge:
            self.x -= 2 * self.velocity_x
            self.velocity_x = 5 * SCALE // 2
            
        if self.y > bottom_edge:
            self.y -= 2 * self.velocity_y
            self.velocity_y = -5 * SCALE // 2
        elif self.y < top_edge:
            self.y -= 2 * self.velocity_y
            self.velocity_y = 5 * SCALE // 2
            
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
