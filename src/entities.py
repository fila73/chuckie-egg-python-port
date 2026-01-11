
import pygame
from .constants import *

class Entity:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.dx = 0
        self.dy = 0
        self.on_ground = False
        
    def update(self, level):
        pass
        
    def draw(self, surface):
        pass

class Player(Entity):
    def __init__(self, x, y, resource_manager):
        super().__init__(x, y, 16 * SCALE, 16 * SCALE)
        self.resources = resource_manager
        self.speed = 2 * SCALE
        self.gravity = 0.5 * SCALE
        self.jump_force = -3.2 * SCALE
        self.jump_vx = 0
        self.facing = 'right'
        self.state = 'idle'
        self.frame_timer = 0
        self.current_frame = 0
        
        # Load sprites (store in list)
        self.sprites = {
            'right': [],
            'left': [],
            'climb': []
        }
        # Placeholder loading
        sheet_r = self.resources.load_image('sprites_farmer_right.png')
        sheet_l = self.resources.load_image('sprites_farmer_left.png')
        sheet_c = self.resources.load_image('sprites_farmer_climbing.png')
        
        def rip_frames(sheet):
            frames = []
            if not sheet: return frames
            if sheet.get_width() < 16: return frames
            h = sheet.get_height()
            # How many frames?
            num_frames = h // 16
            for i in range(num_frames):
                # crop
                frame = sheet.subsurface((0, i*16, 16, 16))
                # scale
                frame = pygame.transform.scale(frame, (16*SCALE, 16*SCALE))
                
                # Tint Yellow
                frame.fill(COLOR_YELLOW, special_flags=pygame.BLEND_RGBA_MULT)
                
                frames.append(frame)
            return frames

        self.sprites['right'] = rip_frames(sheet_r)
        self.sprites['left'] = rip_frames(sheet_l)
        self.sprites['climb'] = rip_frames(sheet_c)
        
        # Ensure we have frames
        if not self.sprites['right']:
             # Fallback
             s = pygame.Surface((16*SCALE, 16*SCALE))
             s.fill(COLOR_CYAN)
             self.sprites['right'] = [s]
             self.sprites['left'] = [s]


    def update(self, level, keys):
        self.dx = 0
        
        # Determine current status from state check
        was_climbing = (self.state == 'climb')
        climbing = was_climbing 
        
        # Check center of player
        cx = self.rect.centerx
        cy = self.rect.centery
        col = cx // (8 * SCALE)
        row = cy // (8 * SCALE)
        
        tile_center = level.get_tile(col, row)
        on_ladder = (tile_center == TILE_LADDER_L or tile_center == TILE_LADDER_R)
        
        # Calculate precise ladder center X
        ladder_center_x = None
        if tile_center == TILE_LADDER_L:
             # Center is right edge of this tile (between L and R)
             ladder_center_x = (col + 1) * 8 * SCALE
        elif tile_center == TILE_LADDER_R:
             # Center is left edge of this tile (between L and R)
             ladder_center_x = col * 8 * SCALE
             
        # Check support for exiting ladder sideways
        is_supported = self.check_support(level)
        
        # --- LOGIC: Change Direction > Continue ---
        
        # Logic 1: Transition Walk -> Climb
        # If we are NOT climbing, but we have vertical input and are positioned for it.
        # This takes priority over continuing to walk.
        if not was_climbing:
             if on_ladder:
                 want_climb = keys[pygame.K_UP] or keys[pygame.K_DOWN]
                 if want_climb and ladder_center_x is not None:
                      diff = abs(self.rect.centerx - ladder_center_x)
                      # Strict alignment
                      if diff <= 1 * SCALE:
                           climbing = True
                           self.state = 'climb'
                           self.rect.centerx = ladder_center_x # Snap immediately

        # Logic 2: Transition Climb -> Walk
        # If we ARE climbing, but we have Valid Lateral Input (and support).
        # This takes priority over continuing to climb.
        if was_climbing:
            want_walk = (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT])
            if want_walk and is_supported:
                 climbing = False
                 self.state = 'walk' 
                 # Direction will be set in Movement block below

        # --- MOVEMENT ---
        
        if climbing:
             # Force zero X movement (Mutual Exclusion)
             self.dx = 0
             self.state = 'climb'
             
             # Only move if keys pressed
             self.dy = 0
             if keys[pygame.K_UP]: 
                  # Check if we can climb higher
                  # User Rule: "Check ladder above head"
                  # Look at the row above our HEAD
                  next_top = self.rect.top - self.speed
                  row_above_head = next_top // (8 * SCALE)
                  
                  t_above = level.get_tile(col, row_above_head)
                  is_ladder_above = (t_above == TILE_LADDER_L or t_above == TILE_LADDER_R)
                  
                  if is_ladder_above:
                       self.dy = -self.speed
                  else:
                       # Constraint: Head cannot enter non-ladder tile
                       # Snap head to bottom of that tile
                       target_top = (row_above_head + 1) * 8 * SCALE
                       
                       # Current top
                       if self.rect.top > target_top:
                            self.dy = -self.speed
                            if self.rect.top + self.dy < target_top:
                                 self.rect.top = target_top
                                 self.dy = 0
                       else:
                            self.rect.top = target_top
                            self.dy = 0
                            
             elif keys[pygame.K_DOWN]: self.dy = self.speed
                            
             elif keys[pygame.K_DOWN]: self.dy = self.speed
             
             # Re-enforce Center X (in case of drift or float errors)
             if ladder_center_x is not None:
                  self.rect.centerx = ladder_center_x
             
             # Check if we moved off ladder (top/bottom)
             # If not on ladder tile, we should probably stop climbing unless transitioning?
             # But we handled "Climb -> Walk" above.
             # If we simply run out of ladder (e.g. top of ladder), we might need to stop.
             if not on_ladder and self.dy > 0:
                  # Climbing down off a ladder?
                  pass
                  
             # Jump off Ladder
             if keys[pygame.K_SPACE]:
                  climbing = False
                  self.state = 'jump' # distinct state? or just idle/walk defaults in draw?
                  # Entities.draw uses 'climb' or 'facing'. 'jump' isn't a key. 
                  # Maybe set state to 'walk' or keep 'climb' animation for a moment?
                  # Usually jumping uses Jump Sprite.
                  self.on_ground = False
                  self.dy = self.jump_force
                  
                  # Lateral Momentum
                  if keys[pygame.K_LEFT]:
                       self.jump_vx = int(-self.speed * 1.3)
                       self.facing = 'left'
                  elif keys[pygame.K_RIGHT]:
                       self.jump_vx = int(self.speed * 1.3)
                       self.facing = 'right'
                  else:
                       self.jump_vx = 0
                       
                  self.dx = self.jump_vx

        else:
             # Walking / In Air
             if is_supported:
                 # Ground Movement
                 self.jump_vx = 0 # Reset momentum on ground
                 
                 if keys[pygame.K_LEFT]:
                    self.dx = -self.speed
                    self.facing = 'left'
                    self.state = 'walk'
                 elif keys[pygame.K_RIGHT]:
                    self.dx = self.speed
                    self.facing = 'right'
                    self.state = 'walk'
                 else:
                    if self.state == 'walk': self.state = 'idle'
                 
                 # Jump
                 if keys[pygame.K_SPACE]:
                    # Note: check_support guarantees we are on floor/aligned.
                    # check_collision_y sets on_ground.
                    # Should we trust on_ground or is_supported?
                    # is_supported is stricter.
                     self.dy = self.jump_force
                     self.jump_vx = int(self.dx * 1.3) # Commit momentum with boost (2/7ths approx)
                     self.on_ground = False
             else:
                 # In Air (Falling or Jumping)
                 # No Air Control. locked to jump (or fall) momentum.
                 self.dx = self.jump_vx
                 
                 # Gravity
                 self.dy += self.gravity
                 
                 # Detect Falling state for animation?
                 # if self.dy > 0: ...

        # X Movement
        self.rect.x += self.dx
        self.check_collision_x(level)
        
        # Y Movement
        prev_bottom = self.rect.bottom
        self.rect.y += self.dy
        
        if not climbing:
            self.on_ground = False 
        
        # Always check collision Y (handles floor stop for both states)
        self.check_collision_y(level, prev_bottom)
            
        # Animation
        if not climbing and not self.on_ground:
             # Jump / Fall Frame = 2nd sprite (Index 1)
             self.current_frame = 1
        elif self.dx != 0 or (climbing and self.dy != 0):
             self.frame_timer += 1
             key_frames = self.sprites.get(self.facing, [])
             if climbing: key_frames = self.sprites['climb']
             
             if key_frames:
                 if self.frame_timer > 5:
                    self.frame_timer = 0
                    self.current_frame = (self.current_frame + 1) % len(key_frames)
        elif not climbing:
             self.current_frame = 0 # Idle frame (only reset if NOT climbing)

    def check_collision_x(self, level):
        # Constrain to screen
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH
        
        # Check Wall Collision (Floors act as obstacles if at same Y)
        # User Rule: Only check bottom half (colliders legs+belly)
        # Sprite is 16*SCALE high. Head is top 8*SCALE.
        
        row_top = (self.rect.top + 8 * SCALE) // (8 * SCALE)
        row_bottom = (self.rect.bottom - 1) // (8 * SCALE) # -1 to avoid floor below
        
        col_left = self.rect.left // (8 * SCALE)
        col_right = (self.rect.right - 1) // (8 * SCALE)
        
        # Iterate rows covered
        if self.dx < 0: # Moving Left
             # Check left edge
             for r in range(row_top, row_bottom + 1):
                  t = level.get_tile(col_left, r)
                  if t == TILE_FLOOR:
                       # Collision!
                       # Snap to right edge of that tile
                       self.rect.left = (col_left + 1) * 8 * SCALE
                       
                       # Bounce Rule: If jumping, invert direction
                       if not self.on_ground and self.state != 'climb':
                           self.dx = -self.dx
                           self.jump_vx = self.dx
                           self.facing = 'right' # Flipped
                       else:
                           self.dx = 0
                       break
                       
        elif self.dx > 0: # Moving Right
             # Check right edge
             for r in range(row_top, row_bottom + 1):
                  t = level.get_tile(col_right, r)
                  
                  if t == TILE_FLOOR:
                       # Collision!
                       # Snap to left edge of that tile
                       self.rect.right = col_right * 8 * SCALE
                       
                       # Bounce Rule
                       if not self.on_ground and self.state != 'climb':
                           self.dx = -self.dx
                           self.jump_vx = self.dx
                           self.facing = 'left' # Flipped
                       else:
                           self.dx = 0
                       break

    def check_collision_y(self, level, old_bottom):
        # Floor collision
        if self.dy >= 0: # Falling or Climbing Down
            # Check bottom edge
            bottom_y = self.rect.bottom
            row = bottom_y // (8 * SCALE)
            
            # Surface Y for this row
            surface_y = row * 8 * SCALE
            
            # Check left and right corners
            col_l = (self.rect.left + 1*SCALE) // (8 * SCALE)
            col_r = (self.rect.right - 1*SCALE) // (8 * SCALE)
            
            tile_l = level.get_tile(col_l, row)
            tile_r = level.get_tile(col_r, row)
            
            # Treat Ladder as floor if NOT climbing AND adjacent to floor
            if self.state == 'climb':
                 # Pure Floor collision only (stop if hitting bottom)
                 if tile_l == TILE_FLOOR or tile_r == TILE_FLOOR:
                      # Strict check: Only stop if we came from above
                      if old_bottom <= surface_y:
                          self.rect.bottom = surface_y
                          self.dy = 0
                          self.on_ground = True
            else:
                 # Check all columns we span
                 # If ANY of them provides solid ground, we stand.
                 
                 found_support = False
                 # span columns from col_l to col_r inclusive
                 for c in range(col_l, col_r + 1):
                     t = level.get_tile(c, row)
                     
                     if t == TILE_FLOOR:
                         found_support = True
                         break
                     elif t == TILE_LADDER_L:
                         # Ladder L is the left part of a 2-tile wide ladder (Col, Col+1)
                         # Support must be to Left of L (c-1) AND Right of R (c+2)
                         t_left = level.get_tile(c - 1, row)
                         t_right = level.get_tile(c + 2, row)
                         if t_left == TILE_FLOOR and t_right == TILE_FLOOR:
                             found_support = True
                             break
                     elif t == TILE_LADDER_R:
                         # Ladder R is the right part (Col-1, Col)
                         # Support must be to Left of L (c-2) AND Right of R (c+1)
                         t_left = level.get_tile(c - 2, row)
                         t_right = level.get_tile(c + 1, row)
                         if t_left == TILE_FLOOR and t_right == TILE_FLOOR:
                             found_support = True
                             break
                 
                 if found_support:
                    # Only snap if we were previously above or at the surface
                    if old_bottom <= surface_y:
                        self.rect.bottom = surface_y
                        self.dy = 0
                        self.on_ground = True
                
        # Collectibles (Egg/Corn)
        # Check center tile
        cx = self.rect.centerx
        cy = self.rect.centery
        col = cx // (8 * SCALE)
        row = cy // (8 * SCALE)
        
        tile = level.get_tile(col, row)
        if tile == TILE_EGG:
            print("Collected Egg!")
            level.set_tile(col, row, TILE_EMPTY)
            # score += 100
        elif tile == TILE_CORN:
            print("Collected Corn!")
            level.set_tile(col, row, TILE_EMPTY)
            # pause timer
            
        pass

    def check_support(self, level):
        bottom_y = self.rect.bottom
        # Must be aligned to grid
        if bottom_y % (8 * SCALE) != 0: return False
        
        row = bottom_y // (8 * SCALE)
        col_l = (self.rect.left + 1*SCALE) // (8 * SCALE)
        col_r = (self.rect.right - 1*SCALE) // (8 * SCALE)
        
        # Check all columns we span
        for c in range(col_l, col_r + 1):
             t = level.get_tile(c, row)
             if t == TILE_FLOOR: return True
             elif t == TILE_LADDER_L or t == TILE_LADDER_R:
                 t_left = level.get_tile(c - 1, row)
                 t_right = level.get_tile(c + 1, row)
                 if t_left == TILE_FLOOR or t_right == TILE_FLOOR: return True
        return False

    def draw(self, surface):
        anim_key = self.facing
        if self.state == 'climb':
             anim_key = 'climb'
             
        frames = self.sprites.get(anim_key, self.sprites['right'])
        if not frames: 
             # Fallback
             frames = self.sprites['right']
             
        idx = self.current_frame % len(frames)
        surface.blit(frames[idx], self.rect)
