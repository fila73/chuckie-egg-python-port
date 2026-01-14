import pygame
from .constants import *

class HUD:
    def __init__(self, res_manager):
        self.res = res_manager
        
    def draw(self, screen, score, level, bonus, time, lives):
        # Row 1: SCORE label + Score value (Red background)
        
        # SCORE Label (24x8)
        pygame.draw.rect(screen, COLOR_RED, (0, 0, 72, 8 * SCALE))
        screen.blit(pygame.transform.scale(self.res.hud_assets['score'], (24 * SCALE, 8 * SCALE)), (0, 0))
        
        # Score Digits (Right of SCORE label)
        score_x = 8 * SCALE
        score_width = 6
        pygame.draw.rect(screen, COLOR_RED, (score_x + 32 * SCALE, 0, score_width * 8 * SCALE, 8 * SCALE))
        self.draw_number(screen, score, score_width, score_x + 32 * SCALE, 0, font_type='score')
        
        # Row 2: PLAYER, LEVEL, BONUS, TIME (Red background)
        
        # PLAYER (32x8)
        player_x = 0
        player_width = 5
        pygame.draw.rect(screen, COLOR_RED, (player_x, 16 * SCALE, player_width * 8 * SCALE, 8 * SCALE))
        screen.blit(pygame.transform.scale(self.res.hud_assets['player'], (32 * SCALE, 8 * SCALE)), (player_x, 16 * SCALE))
        
        # LEVEL Label + Value
        level_x = 56 * SCALE
        level_width = 6
        pygame.draw.rect(screen, COLOR_RED, (level_x, 16 * SCALE, level_width * 8 * SCALE, 8 * SCALE))
        screen.blit(pygame.transform.scale(self.res.hud_assets['level'], (24 * SCALE, 8 * SCALE)), (level_x, 16 * SCALE))
        level_width = 2
        self.draw_number(screen, level, level_width, level_x + 32 * SCALE, 16 * SCALE)
        
        # BONUS Label + Value
        bonus_x = 120 * SCALE
        bonus_width = 8
        pygame.draw.rect(screen, COLOR_RED, (bonus_x, 16 * SCALE, bonus_width * 8 * SCALE, 8 * SCALE))
        screen.blit(pygame.transform.scale(self.res.hud_assets['bonus'], (24 * SCALE, 8 * SCALE)), (bonus_x, 16 * SCALE))
        bonus_width = 4
        self.draw_number(screen, bonus, 4, bonus_x + 32 * SCALE, 16 * SCALE)
        
        # TIME Label + Value
        time_x = 200 * SCALE
        time_width = 7
        pygame.draw.rect(screen, COLOR_RED, (time_x, 16 * SCALE, time_width * 8 * SCALE, 8 * SCALE))
        screen.blit(pygame.transform.scale(self.res.hud_assets['time'], (24 * SCALE, 8 * SCALE)), (time_x, 16 * SCALE))
        time_width = 3
        self.draw_number(screen, time, 3, time_x + 32 * SCALE, 16 * SCALE)
        
        # LIVES (icons below score, row 3 area - but only 2 HUD rows, so under score digits)
        # Position below score digits (around x=32, y=16 which is row 2, but user says below score data)
        # Actually: place below the score value in row 1
        life_icon = self.res.hud_assets['lives']
        lives_start_x = 40 * SCALE
        lives_y = 8 * SCALE  # Below row 2 (inside the game area technically, but as per user request)
        for i in range(lives):
            screen.blit(pygame.transform.scale(life_icon, (8 * SCALE, 8 * SCALE)), (lives_start_x + i * 8 * SCALE, lives_y))

    def draw_number(self, screen, value, digits, x, y, font_type='data'):
        value = max(0, value)  # Clamp to prevent negative display
        s_val = str(value).zfill(digits)
        font = self.res.fonts[font_type]
        for i, char in enumerate(s_val):
            digit_idx = int(char)
            img = font[digit_idx]
            screen.blit(pygame.transform.scale(img, (8 * SCALE, 8 * SCALE)), (x + i * 8 * SCALE, y))
