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
        
        # State Constants
        self.STATE_STAND = 0
        self.STATE_WALK_RIGHT = 1
        self.STATE_WALK_LEFT = 2
        self.STATE_CLIMB = 3
        self.STATE_AIR_UP = 4    # Jumping Up
        self.STATE_AIR_DOWN = 5  # Falling
        
        self.state = self.STATE_STAND
        self.facing = 'right' # Visual facing
        
        self.jump_timer = 0
        self.jump_vx = 0 # Horizontal velocity during jump (Committed direction)
        
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
        SPEED = 1 * SCALE
        
        # 1. DETERMINE X MOVEMENT
        move_x = 0
        
        is_airborne = self.state in [self.STATE_AIR_UP, self.STATE_AIR_DOWN]
        
        if is_airborne:
             # In Air: Ignore inputs, use committed velocity
             move_x = self.jump_vx
        elif self.state == self.STATE_CLIMB:
             # In Climb: No horizontal movement allowed (Step 2)
             move_x = 0
        else:
             # On Ground (Walk/Stand): Use Inputs
             if keys[pygame.K_LEFT]:
                  move_x = -SPEED
                  self.facing = 'left'
                  self.state = self.STATE_WALK_LEFT
             elif keys[pygame.K_RIGHT]:
                  move_x = SPEED
                  self.facing = 'right'
                  self.state = self.STATE_WALK_RIGHT
             else:
                  self.state = self.STATE_STAND
                  
        # 2. APPLY X MOVEMENT
        if move_x != 0:
             start_x = self.rect.x
             self.rect.x += move_x
             self.check_collision_x(level, move_x)
             
             # If we hit a wall in air, kill momentum
             if is_airborne:
                  # If we were pushed back (position incorrect), stop.
                  # Logic: if rect.x is not start_x + move_x?
                  # check_collision_x undoes the move => rect.x == start_x
                  if self.rect.x == start_x:
                       self.jump_vx = -self.jump_vx

        # 3. LADDER ENTRY (Step 1)
        if not is_airborne and self.state != self.STATE_CLIMB:
            # Only trigger if UP or DOWN is pressed
            if keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                
                # 1. Determine the Column (c) based on center x
                #    (We use center because we enforce alignment later)
                c = self.rect.centerx // (8 * SCALE)
                
                # 2. Determine the Row (r) based on direction
                target_tile = None
                
                if keys[pygame.K_UP]:
                    # For UP: Check the tile just ABOVE top of the body.
                    # This ensures we are physically "under" the ladder we want to climb.
                    r_up = (self.rect.top - 1) // (8 * SCALE)
                    target_tile = level.get_tile(c, r_up)
                    
                elif keys[pygame.K_DOWN]:
                    # For DOWN: Check the tile just BELOW the feet.
                    # We add +1 pixel to rect.bottom to check the tile *under* the player.
                    # This allows climbing down when standing ON TOP of a ladder.
                    r_down = (self.rect.bottom + 1) // (8 * SCALE)
                    target_tile = level.get_tile(c, r_down)

                # 3. Check if the identified tile is actually a ladder
                if target_tile in [TILE_LADDER_L, TILE_LADDER_R]:
                    
                    # 4. Alignment Check (Your existing logic)
                    if target_tile == TILE_LADDER_L:
                        target_center_x = (c + 1) * 8 * SCALE
                    else: # TILE_LADDER_R
                        target_center_x = c * 8 * SCALE
                        
                    # Authentic strict junction alignment
                    if self.rect.centerx == target_center_x:
                        self.state = self.STATE_CLIMB
                        move_x = 0

        # 4. JUMP START
        # Can only jump if on ground (not climbing, not air)
        if self.state in [self.STATE_STAND, self.STATE_WALK_LEFT, self.STATE_WALK_RIGHT] and keys[pygame.K_SPACE]:
             self.state = self.STATE_AIR_UP
             self.jump_timer = 0
             # COMMIT DIRECTION based on PRESSED KEYS
             self.jump_vx = 0
             if keys[pygame.K_LEFT]: self.jump_vx = -SPEED
             if keys[pygame.K_RIGHT]: self.jump_vx = SPEED
             # If no direction key, straight up.
             
        # 5. VERTICAL MOVEMENT (State Machine)
        if self.state == self.STATE_AIR_UP:
             # Moving Up (Jump)
             self.rect.y -= SPEED
             self.jump_timer += 1
             
             # NO CEILING CHECK
             if self.rect.top < 0: self.rect.top = 0
             
             # Timer Length (User Requested 11)
             if self.jump_timer > 11:
                  self.state = self.STATE_AIR_DOWN
                  self.jump_timer = 0
                  
        elif self.state == self.STATE_AIR_DOWN:
             # Falling
             self.rect.y += SPEED
             self.check_collision_y(level, SPEED)
             
        elif self.state == self.STATE_CLIMB:
             # CLIMBING (Step 2 & 3)
             if keys[pygame.K_UP]:
                  self.rect.y -= SPEED
                  self.update_animation() # Update climb frames
             elif keys[pygame.K_DOWN]:
                  self.rect.y += SPEED
                  self.update_animation() # Update climb frames

             c = self.rect.centerx // (8 * SCALE)
             r_bottom = (self.rect.bottom) // (8 * SCALE)

             # Vertical Exit (Step 4)
             # Check if we should exit vertically (only at tile boundaries)
             if self.rect.bottom % (8 * SCALE) == 0:
                  if keys[pygame.K_UP]:
                       # Topping out: check if there's no more ladder above us
                       # Harry is 16px high (2 tiles). Check the tile at his head level.
                       r_head = (self.rect.top - 1) // (8 * SCALE)
                       if level.get_tile(c, r_head) not in [TILE_LADDER_L, TILE_LADDER_R]:
                            self.state = self.STATE_STAND
                            
                  elif keys[pygame.K_DOWN]:
                       # Stepping off bottom onto floor or falling
                       if level.get_tile(c, r_bottom) == TILE_FLOOR:
                            self.state = self.STATE_STAND
                       elif level.get_tile(c, r_bottom) == TILE_EMPTY:
                            # If no more ladder and no floor, fall
                            self.state = self.STATE_AIR_DOWN

             # Sideways Exit (Step 3)
             # Must be aligned vertically with a "floor row"
             if self.rect.bottom % (8 * SCALE) == 0:
                  if keys[pygame.K_LEFT] and level.get_tile(c - 2, r_bottom) == TILE_FLOOR:
                       self.state = self.STATE_WALK_LEFT
                       self.facing = 'left'
                  elif keys[pygame.K_RIGHT] and level.get_tile(c + 1, r_bottom) == TILE_FLOOR:
                       self.state = self.STATE_WALK_RIGHT
                       self.facing = 'right'
             
        else:
             # GRAVITY / SUPPORT Check (when not Jumping Up or Climbing)
             if not self.check_support(level):
                  self.state = self.STATE_AIR_DOWN
                  self.rect.y += SPEED
                  self.check_collision_y(level, SPEED)
                  # If walking off ledge, do we keep momentum?
                  # For "Non-Steerable", usually yes, or fall straight.
                  # Let's assume falling straight for safety unless user wants momentum.
                  self.jump_vx = 0
             else:
                  # Landed
                  if self.state == self.STATE_AIR_DOWN:
                       self.state = self.STATE_STAND
                       self.jump_vx = 0

        self.update_animation()
        self.check_collectibles(level)

    def check_collision_x(self, level, dx):
        # Screen bounds
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH
        
        # Wall Collision
        # Use simple Rect check against wall/floor tiles
        
        # Add a small vertical tolerance (toes) to avoid hitting the floor 
        # we are walking on/falling into slightly.
        v_offset = 2 * SCALE
        # Add horizontal tolerance to allow getting closer to walls (1px authentic)
        h_offset = 1 * SCALE
        
        c_left = (self.rect.left + h_offset) // (8 * SCALE)
        c_right = (self.rect.right - 1 - h_offset) // (8 * SCALE)
        r_top = self.rect.top // (8 * SCALE)
        
        # "Toes" tolerance: Don't check the very bottom pixels against walls
        r_bottom = (self.rect.bottom - 1 - v_offset) // (8 * SCALE)
        
        for r in range(r_top, r_bottom + 1):
             for c in range(c_left, c_right + 1):
                  t = level.get_tile(c, r)
                  
                  # Floor Collision Logic
                  if t == TILE_FLOOR:
                       # If Airborne (Jump/Fall), we ignore floors (pass-through)
                       if self.state in [self.STATE_AIR_UP, self.STATE_AIR_DOWN]:
                            continue
                       
                       # If Walking/Standing, Floor is a WALL (cannot walk through check_collision_x)
                       # Note: Toes tolerance prevents colliding with the floor we stand on.
                       self.rect.x -= dx
                       return
                  
                  # Check other solid tiles (e.g. Cage parts?)
                  # Ignored tiles: Empty, Ladders, Collectibles, Floor (handled above)
                  if t != TILE_EMPTY and t not in [TILE_LADDER_L, TILE_LADDER_R, TILE_EGG, TILE_CORN]:
                       # Collision detected with a solid object (e.g. Cage)
                       # Undo move
                       self.rect.x -= dx
                       return

    def check_collision_y(self, level, dy):
        # Floor Collision (Landing)
        # MUST MATCH Support Logic for consistency.
        
        offset = 2 * SCALE
        check_points = [self.rect.centerx - offset, self.rect.centerx + offset]
        
        # We only check bottom edge for landing collision
        r_bottom = (self.rect.bottom - 1) // (8 * SCALE)
        
        for check_x in check_points:
             c = check_x // (8 * SCALE)
             t = level.get_tile(c, r_bottom)
             
             if dy > 0: # Falling
                  # Always land on Floor
                  if t == TILE_FLOOR:
                       self.rect.bottom = r_bottom * 8 * SCALE
                       self.state = self.STATE_STAND
                       return
                  
                  # Conditional Ladder Landing:
                  # Land ONLY if platforms on BOTH sides.
                  if t in [TILE_LADDER_L, TILE_LADDER_R]:
                       land_on_ladder = False
                       if t == TILE_LADDER_L:
                            left_ok = level.get_tile(c - 1, r_bottom) == TILE_FLOOR
                            right_ok = level.get_tile(c + 2, r_bottom) == TILE_FLOOR
                       elif t == TILE_LADDER_R:
                            left_ok = level.get_tile(c - 2, r_bottom) == TILE_FLOOR
                            right_ok = level.get_tile(c + 1, r_bottom) == TILE_FLOOR
                       if left_ok and right_ok:
                            land_on_ladder = True
                       
                       if land_on_ladder:
                            self.rect.bottom = r_bottom * 8 * SCALE
                            self.state = self.STATE_STAND
                            return

    def check_support(self, level):
        # Authentic 8-bit Support Check (Stricter):
        # We check a "Foot Width" around the center.
        # If either side of the "feet" is over air, we fall.
        # This reduces the overhang allowance.
        
        offset = 2 * SCALE # Small width (approx 6px total width)
        
        check_points = [self.rect.centerx - offset, self.rect.centerx + offset]
        check_y = self.rect.bottom
        
        for check_x in check_points:
             c = check_x // (8 * SCALE)
             r = check_y // (8 * SCALE)
             t = level.get_tile(c, r)
             
             # Ladders count as solid ground to walk on (Support)
             if t not in [TILE_FLOOR, TILE_LADDER_L, TILE_LADDER_R]:
                  return False # Any part of feet in air = Fall
                  
        return True

    def update_animation(self):
        # Simple frame cycler
        if self.state in [self.STATE_WALK_LEFT, self.STATE_WALK_RIGHT, self.STATE_CLIMB]:
             self.frame_timer += 1
             if self.frame_timer > 5:
                  self.frame_timer = 0
                  # Determine set
                  key = 'right'
                  if self.state == self.STATE_WALK_LEFT: key = 'left'
                  if self.state == self.STATE_CLIMB: key = 'climb'
                  
                  frames = self.sprites.get(key, self.sprites['right'])
                  self.current_frame = (self.current_frame + 1) % len(frames)
        elif self.state in [self.STATE_AIR_UP, self.STATE_AIR_DOWN]:
             self.current_frame = 1 # Jump
        else:
             self.current_frame = 0 # Idle

    def check_collectibles(self, level):
        cx = self.rect.centerx
        cy = self.rect.centery
        c = cx // (8 * SCALE)
        r = cy // (8 * SCALE)
        
        t = level.get_tile(c, r)
        if t == TILE_EGG:
             print("Collected Egg!")
             level.set_tile(c, r, TILE_EMPTY)
        elif t == TILE_CORN:
             print("Collected Corn!")
             level.set_tile(c, r, TILE_EMPTY)
 
    def draw(self, surface):
        anim_key = self.facing
        if self.state == self.STATE_CLIMB:
             anim_key = 'climb'
             
        frames = self.sprites.get(anim_key, self.sprites['right'])
        if not frames: frames = self.sprites['right']
             
        idx = self.current_frame % len(frames)
        surface.blit(frames[idx], self.rect)
