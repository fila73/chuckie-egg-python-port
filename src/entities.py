from src.constants import SCALE
import pygame
from .constants import *

def pixel_to_row(y_pixel):
    """Convert pixel Y coordinate to grid row, accounting for map offset."""
    return (y_pixel - MAP_OFFSET_Y * SCALE) // (8 * SCALE)

def pixel_to_col(x_pixel):
    """Convert pixel X coordinate to grid column."""
    return x_pixel // (8 * SCALE)


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
        # Harry's authentic spawn point: X=100, Y=23 (Spectrum coords)
        # User confirmed (100, 144) scaled, plus 2 rows for HUD offset.
        self.spawn_x = 100 * SCALE
        self.spawn_y = (144 + MAP_OFFSET_Y) * SCALE
        
        super().__init__(self.spawn_x, self.spawn_y, 16 * SCALE, 16 * SCALE)
        self.resources = resource_manager
        
        # State Constants
        self.STATE_STAND = 0
        self.STATE_WALK_RIGHT = 1
        self.STATE_WALK_LEFT = 2
        self.STATE_CLIMB = 3
        self.STATE_AIR_UP = 4    # Jumping Up
        self.STATE_AIR_DOWN = 5  # Falling
        self.STATE_ELEVATOR = 6  # Riding an elevator
        self.STATE_DEATH = 7     # Dying (waiting for music)
        
        self.state = self.STATE_STAND
        self.facing = 'right' # Visual facing
        
        self.jump_timer = 0
        self.jump_vx = 0 # Horizontal velocity during jump (Committed direction)
        self.current_elevator = None  # Reference to elevator Harry is standing on
        
        # Spawn position for respawn after death
        self.spawn_x = x
        self.spawn_y = y
        self.death_start_time = 0 # To track death tune duration
        
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
        
        # 0. IGNORE EVERYTHING IF DEAD
        if self.state == self.STATE_DEATH:
             if pygame.time.get_ticks() - self.death_start_time > 10000: # 10s roughly
                  self.respawn()
             return

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
             # Play walk sound every 4 pixels
             if self.state in [self.STATE_WALK_LEFT, self.STATE_WALK_RIGHT] and self.rect.x % (4 * SCALE) == 0:
                  self.resources.play_sound('walk')
             
             # If we hit a wall in air, kill momentum
             if is_airborne:
                  # If we were pushed back (position incorrect), stop.
                  # Logic: if rect.x is not start_x + move_x?
                  # check_collision_x undoes the move => rect.x == start_x
                  if self.rect.x == start_x:
                       self.jump_vx = -self.jump_vx

        # 3. LADDER ENTRY (Step 1)
        if self.state != self.STATE_CLIMB:
            # Only trigger if UP or DOWN is pressed
            if keys[pygame.K_UP] or keys[pygame.K_DOWN]:
                
                # 1. Determine the Column (c) based on center x
                #    (We use center because we enforce alignment later)
                c = pixel_to_col(self.rect.centerx)
                
                # 2. Determine the Row (r) based on direction
                target_tile = None
                
                if keys[pygame.K_UP]:
                    # For UP: Check the tile just ABOVE top of the body.
                    # This ensures we are physically "under" the ladder we want to climb.
                    r_up = pixel_to_row(self.rect.top - 1)
                    target_tile = level.get_tile(c, r_up)
                    
                elif keys[pygame.K_DOWN]:
                    # For DOWN: Check the tile just BELOW the feet.
                    # We add +1 pixel to rect.bottom to check the tile *under* the player.
                    # This allows climbing down when standing ON TOP of a ladder.
                    r_down = pixel_to_row(self.rect.bottom + 1)
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
                        
                        # Snap vertically to tile grid when catching airborne
                        # to ensure exit logic (y % 24 == 0) works correctly.
                        if keys[pygame.K_UP]:
                             # Snap top to the bottom of the tile we are entering
                             self.rect.top = (r_up + 1) * 8 * SCALE + MAP_OFFSET_Y * SCALE
                        elif keys[pygame.K_DOWN]:
                             # Snap bottom to the top of the tile we are entering
                             self.rect.bottom = r_down * 8 * SCALE + MAP_OFFSET_Y * SCALE
                             
                        move_x = 0

        # 4. JUMP START
        # Can only jump if on ground or climbing
        if self.state in [self.STATE_STAND, self.STATE_WALK_LEFT, self.STATE_WALK_RIGHT, self.STATE_CLIMB] and keys[pygame.K_SPACE]:
             self.state = self.STATE_AIR_UP
             self.jump_timer = 0
             self.resources.play_sound('jump')
             # COMMIT DIRECTION based on PRESSED KEYS
             self.jump_vx = 0
             if keys[pygame.K_LEFT]: self.jump_vx = -SPEED
             if keys[pygame.K_RIGHT]: self.jump_vx = SPEED
             # If no direction key, straight up.
             
        # 5. VERTICAL MOVEMENT (State Machine)
        # Snížená vertikální rychlost pro delší skok (2 pixely při SCALE 3)
        V_SPEED = 2 * (SCALE // 3) if SCALE >= 3 else 1
        
        if self.state == self.STATE_AIR_UP:
             # Moving Up (Jump)
             self.rect.y -= V_SPEED
             self.jump_timer += 1
             
             # NO CEILING CHECK
             if self.rect.top < 0: self.rect.top = 0
             
             # Zvýšená doba letu (17 snímků) pro dosah cca 5 dlaždic
             if self.jump_timer > 17:
                  self.state = self.STATE_AIR_DOWN
                  self.jump_timer = 0
                  
        elif self.state == self.STATE_AIR_DOWN:
             # Falling
             self.rect.y += V_SPEED
             
             # Check if landing on elevator while falling
             elevator = self.check_elevator_collision(level)
             if elevator:
                  self.state = self.STATE_ELEVATOR
                  self.current_elevator = elevator
                  self.rect.bottom = elevator.rect.top
                  self.jump_vx = 0
             else:
                  self.check_collision_y(level, V_SPEED)
             
        elif self.state == self.STATE_CLIMB:
             # CLIMBING (Step 2 & 3)
             if keys[pygame.K_UP]:
                  self.rect.y -= SPEED
                  self.update_animation() # Update climb frames
                  if self.rect.y % (4 * SCALE) == 0:
                       self.resources.play_sound('climb')
             elif keys[pygame.K_DOWN]:
                  self.rect.y += SPEED
                  self.update_animation() # Update climb frames
                  if self.rect.y % (4 * SCALE) == 0:
                       self.resources.play_sound('climb')

             c = pixel_to_col(self.rect.centerx)
             r_bottom = pixel_to_row(self.rect.bottom)

             # Vertical Exit (Step 4)
             # Check if we should exit vertically (only at tile boundaries)
             if self.rect.bottom % (8 * SCALE) == 0:
                  if keys[pygame.K_UP]:
                       # Topping out: check if there's no more ladder above us
                       # Harry is 16px high (2 tiles). Check the tile at his head level.
                       r_head = pixel_to_row(self.rect.top - 1)
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
                  if keys[pygame.K_LEFT] and level.get_tile(c - 2, r_bottom) in (TILE_FLOOR, TILE_EGG, TILE_CORN):
                       self.state = self.STATE_WALK_LEFT
                       self.facing = 'left'
                  elif keys[pygame.K_RIGHT] and level.get_tile(c + 1, r_bottom) in (TILE_FLOOR, TILE_EGG, TILE_CORN):
                       self.state = self.STATE_WALK_RIGHT
                       self.facing = 'right'
             
        else:
             # GRAVITY / SUPPORT Check (when not Jumping Up or Climbing)
             
             # First check if standing on an elevator
             elevator = self.check_elevator_collision(level)
             if elevator:
                  # Land on elevator
                  self.state = self.STATE_ELEVATOR
                  self.current_elevator = elevator
                  self.rect.bottom = elevator.rect.top
                  self.jump_vx = 0
             elif self.state == self.STATE_ELEVATOR:
                  # Currently on elevator - check if still on it
                  if self.current_elevator:
                       # Move with elevator
                       self.rect.bottom = self.current_elevator.rect.top
                       
                       # Check if we've moved off horizontally
                       if not self.rect.colliderect(self.current_elevator.rect.inflate(4, 8)):
                            self.state = self.STATE_AIR_DOWN
                            self.current_elevator = None
                  else:
                       self.state = self.STATE_AIR_DOWN
             elif not self.check_support(level):
                  self.state = self.STATE_AIR_DOWN
                  self.current_elevator = None
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

        # Death check: Harry's feet fell below the lowest platform (21 rows + 2 row offset)
        if self.rect.bottom > (21 * 8 + MAP_OFFSET_Y) * SCALE:
             if self.state != self.STATE_DEATH:
                  self.state = self.STATE_DEATH
                  self.death_start_time = pygame.time.get_ticks()
                  self.resources.play_sound('death')

        self.update_animation()
        self.check_collectibles(level)

    def check_collision_x(self, level, dx):
        # Screen bounds
        if self.rect.left - SCALE < 0: self.rect.left = 0 + SCALE
        if self.rect.right + (SCALE * 2) > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH - (SCALE * 2)
        
        # In Chuckie Egg, floors act as walls when walking, 
        # but are passed through when jumping/falling vertically.
        if self.state in [self.STATE_AIR_UP, self.STATE_AIR_DOWN]:
             return

        # Check only the leading edge in the direction of movement
        if dx > 0:
             c = pixel_to_col(self.rect.right - 4)
        else:
             c = pixel_to_col(self.rect.left + 4)
             
        r_top = pixel_to_row(self.rect.top)
        # "Toes" tolerance: Don't check the very bottom pixels against walls
        # to avoid colliding with the floor Harry is standing on.
        v_offset = 2 * SCALE
        r_bottom = pixel_to_row(self.rect.bottom - 1 - v_offset)
        
        for r in range(r_top, r_bottom + 1):
             if level.get_tile(c, r) == TILE_FLOOR:
                  self.rect.x -= dx
                  return

    def check_collision_y(self, level, dy):
        # Floor Collision (Landing)
        # MUST MATCH Support Logic for consistency.
        
        # Fall if the "heel" (trailing edge based on movement) is over air.
        if self.facing == 'right':
            # Moving right: check the left edge (heel)
            check_x = self.rect.centerx
        else:
            # Moving left: check the right edge (heel)
            check_x = self.rect.centerx
            
        c = pixel_to_col(check_x)
        r = pixel_to_row(self.rect.bottom)
        t = level.get_tile(c, r)
       
        if dy > 0: # Falling
            # Always land on Floor
            if t == TILE_FLOOR:
                self.rect.bottom = r * 8 * SCALE + MAP_OFFSET_Y * SCALE
                self.state = self.STATE_STAND
                return
               
            # Conditional Ladder Landing:
            # Land ONLY if platforms on BOTH sides.
            if t in [TILE_LADDER_L, TILE_LADDER_R]:
                land_on_ladder = False
                if t == TILE_LADDER_L:
                    left_ok = level.get_tile(c - 1, r) == TILE_FLOOR
                    right_ok = level.get_tile(c + 2, r) == TILE_FLOOR
                elif t == TILE_LADDER_R:
                    left_ok = level.get_tile(c - 2, r) == TILE_FLOOR
                    right_ok = level.get_tile(c + 1, r) == TILE_FLOOR
                if left_ok and right_ok:
                    land_on_ladder = True
                    
                if land_on_ladder:
                    self.rect.bottom = r * 8 * SCALE + MAP_OFFSET_Y * SCALE
                    self.state = self.STATE_STAND
                    return

    def check_support(self, level):
        # Fall if the "heel" (trailing edge based on movement) is over air.
        if self.facing == 'right':
            # Moving right: check the left edge (heel)
            check_x = self.rect.centerx - SCALE
        else:
            # Moving left: check the right edge (heel)
            check_x = self.rect.centerx
            
        c = pixel_to_col(check_x)
        r = pixel_to_row(self.rect.bottom)
        t = level.get_tile(c, r)
        
        # Solid check
        if t not in [TILE_FLOOR, TILE_LADDER_L, TILE_LADDER_R]:
             self.rect.x += (SCALE * 4 if self.facing == 'right' else -SCALE * 4)
             return False
                  
        return True

    def check_elevator_collision(self, level):
        """
        Check if Harry is standing on an elevator.
        Returns the elevator if found, None otherwise.
        """
        # Create a small rect at Harry's feet to check for elevator collision
        feet_rect = pygame.Rect(
            self.rect.left,
            self.rect.bottom,
            self.rect.width,
            4 * SCALE  # Check a few pixels below feet
        )
        
        for elevator in level.elevators:
            # Check if Harry's feet are near the elevator's top surface
            if feet_rect.colliderect(elevator.rect):
                # Horizontal alignment check
                if (self.rect.centerx > elevator.rect.left and 
                    self.rect.centerx < elevator.rect.right):
                    return elevator
        
        return None

    def respawn(self):
        """Reset Harry to spawn position after death."""
        # No sound call here anymore, it's triggered when entering STATE_DEATH
        self.rect.x = self.spawn_x
        self.rect.y = self.spawn_y
        self.state = self.STATE_STAND
        self.jump_timer = 0
        self.jump_vx = 0
        self.current_elevator = None
        self.facing = 'right'

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
        c = pixel_to_col(cx)
        r = pixel_to_row(cy)
        
        t = level.get_tile(c, r)
        if t == TILE_EGG:
            level.set_tile(c, r, TILE_EMPTY)
            self.resources.play_sound('collect')
            return TILE_EGG
        elif t == TILE_CORN:
            level.set_tile(c, r, TILE_EMPTY)
            self.resources.play_sound('collect')
            return TILE_CORN
        return None
 
    def draw(self, surface):
        anim_key = self.facing
        if self.state == self.STATE_CLIMB:
             anim_key = 'climb'
             
        frames = self.sprites.get(anim_key, self.sprites['right'])
        if not frames: frames = self.sprites['right']
             
        idx = self.current_frame % len(frames)
        surface.blit(frames[idx], self.rect)


class Elevator(Entity):
    """
    Vertical moving platform (lift) that loops endlessly.
    Harry can stand on it and be carried up or down.
    """
    def __init__(self, x, y_top, y_bottom, speed=1, direction=-1):
        """
        Args:
            x: Horizontal position (center x of the platform).
            y_top: The top boundary (minimum y) of the elevator's range.
            y_bottom: The bottom boundary (maximum y) of the elevator's range.
            speed: Speed in pixels per frame (scaled).
            direction: -1 for moving up initially, +1 for moving down.
        """
        # Platform is 2 tiles wide (16px * SCALE) and 1 tile tall (8px * SCALE)
        width = 16 * SCALE
        height = 4 * SCALE  # Visual height of the platform bar
        
        # Start position
        start_y = y_bottom if direction == -1 else y_top
        super().__init__(x - width // 2, start_y, width, height)
        
        self.y_top = y_top
        self.y_bottom = y_bottom
        self.speed = speed * 2 # Speed in raw pixels (not scaled for slower movement)
        self.direction = direction  # -1 = up, +1 = down
        
        # Create a simple visual surface
        self.image = pygame.Surface((width, height))
        self.image.fill(COLOR_YELLOW)  # Authentic Spectrum color

    def update(self, level=None):
        """Move the elevator and wrap around at boundaries."""
        self.rect.y += self.direction * self.speed
        
        # Check wrapping
        if self.direction == -1 and self.rect.top < self.y_top:
            # Moving up, reached top -> wrap to bottom
            self.rect.bottom = self.y_bottom
        elif self.direction == 1 and self.rect.bottom > self.y_bottom:
            # Moving down, reached bottom -> wrap to top
            self.rect.top = self.y_top

    def draw(self, surface):
        """Draw the elevator platform."""
        surface.blit(self.image, self.rect)
