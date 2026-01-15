"""Screen wipe effects for game transitions."""
import pygame
from .constants import *

# Spectrum attribute colors (INK = PAPER for solid fill)
WIPE_COLORS = [
    (0, 0, 205),     # BLUE
    (205, 0, 0),     # RED
    (205, 0, 205),   # MAGENTA
    (0, 205, 0),     # GREEN
    (0, 205, 205),   # CYAN
    (205, 205, 0),   # YELLOW
    (205, 205, 205), # WHITE
]

class ScreenWipe:
    def __init__(self):
        self.active = False
        self.wipe_type = None  # 'game_start' or 'level_transition'
        self.phase = 0  # 0 = colors expanding, 1 = black clearing
        self.iteration = 0
        self.max_iterations = 12
        self.frame_delay = 3  # Frames between iterations
        self.frame_counter = 0
        self.rects = []  # List of (rect, color) for current state
        
    def start_game_wipe(self):
        """Start the single expanding rectangle wipe for game start."""
        self.active = True
        self.wipe_type = 'game_start'
        self.phase = 0
        self.iteration = 0
        self.frame_counter = 0
        self.rects = []
        
    def start_level_wipe(self):
        """Start the 4-quadrant wipe for level transitions."""
        self.active = True
        self.wipe_type = 'level_transition'
        self.phase = 0
        self.iteration = 0
        self.frame_counter = 0
        self.rects = []
        
    def update(self):
        """Advance the wipe animation by one frame."""
        if not self.active:
            return
            
        self.frame_counter += 1
        if self.frame_counter < self.frame_delay:
            return
        self.frame_counter = 0
        
        if self.wipe_type == 'game_start':
            self._update_game_start_wipe()
        else:
            self._update_level_wipe()
            
    def _update_game_start_wipe(self):
        """Update single expanding rectangle from center."""
        # Center of screen (in 8x8 character grid)
        center_row, center_col = 12, 12
        
        if self.iteration < self.max_iterations:
            # Get color for this iteration
            if self.phase == 0:
                color = WIPE_COLORS[self.iteration % len(WIPE_COLORS)]
            else:
                color = COLOR_BLACK
                
            # Calculate rectangle bounds (expanding from center)
            i = self.iteration
            left = (center_col - i - 1) * 8 * SCALE
            top = (center_row - i - 1) * 8 * SCALE
            width = (10 + i * 2) * 8 * SCALE
            height = (2 + i * 2) * 8 * SCALE
            
            # Add outline rectangle (not filled, just the border)
            thickness = 8 * SCALE
            # Top edge
            self.rects.append((pygame.Rect(left, top, width, thickness), color))
            # Bottom edge
            self.rects.append((pygame.Rect(left, top + height - thickness, width, thickness), color))
            # Left edge
            self.rects.append((pygame.Rect(left, top, thickness, height), color))
            # Right edge
            self.rects.append((pygame.Rect(left + width - thickness, top, thickness, height), color))
            
            self.iteration += 1
        else:
            # End of current phase
            if self.phase == 0:
                # Switch to clearing phase
                self.phase = 1
                self.iteration = 0
                # Do NOT clear rects here - keep colored rects so black wipe draws over them
            else:
                # Animation complete
                self.active = False
                self.rects = []
                
    def _update_level_wipe(self):
        """Update 4-quadrant expanding rectangles."""
        if self.iteration < 6:
            if self.phase == 0:
                color = WIPE_COLORS[self.iteration % len(WIPE_COLORS)]
            else:
                color = COLOR_BLACK
            
            # Quadrant centers (in pixels, scaled)
            # Top-left rectangle
            self._add_quadrant_outline(6, 5, self.iteration, color, 'rect_h')
            # Top-right square
            self._add_quadrant_outline(6, 25, self.iteration, color, 'square')
            # Bottom-left square
            self._add_quadrant_outline(18, 5, self.iteration, color, 'square')
            # Bottom-right rectangle
            self._add_quadrant_outline(18, 17, self.iteration, color, 'rect_h')
            
            self.iteration += 1
        else:
            if self.phase == 0:
                self.phase = 1
                self.iteration = 0
                # Do NOT clear rects here
            else:
                self.active = False
                self.rects = []
                
    def _add_quadrant_outline(self, center_row, center_col, iteration, color, shape):
        """Add outline rectangles for a quadrant."""
        i = iteration
        thickness = 8 * SCALE
        
        if shape == 'square':
            size = (2 + i * 2) * 8 * SCALE
            left = (center_col - i - 1) * 8 * SCALE
            top = (center_row - i - 1) * 8 * SCALE
            width = size
            height = size
        else:  # rect_h (wider than tall)
            width = (4 + i * 2) * 8 * SCALE
            height = (2 + i * 2) * 8 * SCALE
            left = (center_col - i - 2) * 8 * SCALE
            top = (center_row - i - 1) * 8 * SCALE
        
        # Clamp to screen bounds
        left = max(0, left)
        top = max(0, top)
        
        # Add edges
        self.rects.append((pygame.Rect(left, top, width, thickness), color))
        self.rects.append((pygame.Rect(left, top + height - thickness, width, thickness), color))
        self.rects.append((pygame.Rect(left, top, thickness, height), color))
        self.rects.append((pygame.Rect(left + width - thickness, top, thickness, height), color))
        
    def draw(self, screen):
        """Draw all accumulated rectangles."""
        for rect, color in self.rects:
            pygame.draw.rect(screen, color, rect)
            
    def is_active(self):
        return self.active
