
import pygame
import sys
import os
from .constants import *
from .resources import ResourceManager
from .level import Level

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chuckie Egg Python Port")
    clock = pygame.time.Clock()
    
    # Load assets
    res_manager = ResourceManager(os.path.join(os.path.dirname(__file__), '../assets'))
    res_manager.load_all()
    
    level = Level(res_manager)
    level.load_data(os.path.join(os.path.dirname(__file__), '../data/levels.json'))
    level.set_level('level_1') # Start with Level 1
    
    from .entities import Player
    player = Player(100 * SCALE, 144 * SCALE, res_manager) # Authentic spawn (100, 23 from bottom)
    
    from .hud import HUD
    hud = HUD(res_manager)
    
    # Game states
    STATE_INTRO = 0
    STATE_GAME = 1
    game_state = STATE_INTRO
    
    # Game variables
    score = 0
    lives = 4
    level_num = 1
    bonus_timer = 1000
    game_timer = 900
    timer_freeze = 0
    extra_life_target = 10000
    
    # Tick rates (50 FPS)
    # game_timer: -1 every 0.1s -> every 5 frames
    # bonus_timer: -10 every 1.0s -> every 50 frames
    frame_count = 0
    
    # Start Intro
    res_manager.play_music('theme', loops=0)
    
    running = True
    while running:
        # Event handling
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_state == STATE_INTRO:
                    game_state = STATE_GAME
                    res_manager.stop_music('theme')
                    # Init level logic
                    bonus_timer = 1000 * level_num
                    game_timer = 900
                    continue

                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    level.set_level('level_1')
                    level_num = 1
                    bonus_timer = 1000 * level_num
                    game_timer = 900
                elif event.key == pygame.K_2:
                    level.set_level('level_2')
                    level_num = 2
                    bonus_timer = 1000 * level_num
                    game_timer = 900

                    
        # Update
        if game_state == STATE_GAME:
            frame_count += 1
            
            # Skip gameplay updates if player is dead
            if player.state == player.STATE_DEATH:
                # Just wait for respawn timer (handled by main.py death logic below)
                pass
            else:
                # Timer logic (only when player is alive)
                if timer_freeze > 0:
                    timer_freeze -= 1
                else:
                    # Game Timer (every 0.1s -> 5 frames)
                    if game_timer > 0 and frame_count % 5 == 0:
                        game_timer -= 1
                        if game_timer == 0:
                            player.state = player.STATE_DEATH
                            player.death_start_time = pygame.time.get_ticks()
                            res_manager.play_sound('death')
                    
                    # Bonus Timer (every 1s -> 50 frames)
                    if frame_count % 50 == 0:
                        if bonus_timer > 0:
                            bonus_timer -= 10

                level.update_elevators()
                player.update(level, keys)
            
            # Check collections
            item = player.check_collectibles(level)
            if item:
                if item == TILE_EGG:
                    score += 100
                elif item == TILE_CORN:
                    score += 50
                timer_freeze = 150 # 3 seconds at 50 FPS
                
                # Check Extra Life
                if score >= extra_life_target:
                    lives += 1
                    extra_life_target += 10000
                    # Original game plays a sound? We don't have one extracted yet.
            
            # Check Level Completion
            # We need a way to count eggs. Let's add it to Level class.
            if level.count_eggs() == 0:
                # Level Complete!
                score += bonus_timer
                level_num += 1
                level.set_level(f'level_{((level_num-1) % 8) + 1}') 
                player.respawn() # Reset position
                bonus_timer = 1000 * level_num
                game_timer = 900
                timer_freeze = 0
            
            # Check Death Respawn (Handled in Player.update state change)
            # But we need to manage lives in main.py
            if player.state == player.STATE_DEATH and player.death_start_time and pygame.time.get_ticks() - player.death_start_time > 10000:
                lives -= 1
                if lives < 0:
                    # Game Over
                    game_state = STATE_INTRO
                    score = 0
                    lives = 5
                    level_num = 1
                    level.set_level('level_1')
                    player.respawn()
                    res_manager.play_music('theme', loops=0)
                else:
                    player.respawn()
                    game_timer = 900
                    timer_freeze = 0
        
        # Render
        screen.fill(COLOR_BLACK)
        
        if game_state == STATE_INTRO:
            if res_manager.loading_screen:
                screen.blit(res_manager.loading_screen, (0, 0))
        else:
            level.draw(screen)
            player.draw(screen)
            hud.draw(screen, score, level_num, bonus_timer, game_timer, lives)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
