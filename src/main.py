
import pygame
import sys
import os
from .constants import *
from .resources import ResourceManager
from .level import Level
from .effects import ScreenWipe
from .hen import Hen, MotherDuck, spawn_hens

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
    
    from .entities import Player
    player = Player(100 * SCALE, 168 * SCALE, res_manager)
    
    from .hud import HUD
    hud = HUD(res_manager)
    
    # Effects and Enemies
    wipe = ScreenWipe()
    mother_duck = MotherDuck(res_manager)
    hens = []
    
    # Game states
    STATE_INTRO = 0
    STATE_GAME = 1
    STATE_BONUS_COUNTDOWN = 2
    STATE_TRANSITION = 3
    game_state = STATE_INTRO
    
    # Game variables
    score = 0
    lives = 4
    level_num = 1
    cleared_levels = 0  # Total levels cleared (for difficulty progression)
    bonus_timer = 1000
    game_timer = 900
    timer_freeze = 0
    extra_life_target = 10000
    
    frame_count = 0
    
    # Helper to start a level
    def start_level(num, reset_player=True):
        nonlocal bonus_timer, game_timer, timer_freeze
        level.set_level(f'level_{((num - 1) % 8) + 1}') 
        
        # Spawn enemies
        nonlocal hens
        hens = spawn_hens(num, cleared_levels, res_manager)
        mother_duck.activate(cleared_levels)
        mother_duck.reset()
        
        if reset_player:
            player.respawn()
            
        bonus_timer = 1000 * ((num - 1) % 8 + 1)
        game_timer = 900
        timer_freeze = 0
        
    # Start Intro Music
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
                    start_level(level_num)
                    wipe.start_game_wipe()
                    continue

                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    level_num = 1
                    cleared_levels = 0
                    start_level(level_num)
                elif event.key == pygame.K_2:
                    level_num = 2
                    cleared_levels = 1
                    start_level(level_num)
                elif event.key == pygame.K_3:
                    level_num = 3
                    cleared_levels = 2
                    start_level(level_num)
                elif event.key == pygame.K_4:
                    level_num = 4
                    cleared_levels = 3
                    start_level(level_num)
                elif event.key == pygame.K_5:
                    level_num = 5
                    cleared_levels = 4
                    start_level(level_num)
                elif event.key == pygame.K_6:
                    level_num = 6
                    cleared_levels = 5
                    start_level(level_num)
                elif event.key == pygame.K_7:
                    level_num = 7
                    cleared_levels = 6
                    start_level(level_num)
                elif event.key == pygame.K_8:
                    level_num = 8
                    cleared_levels = 7
                    start_level(level_num)
                elif event.key == pygame.K_9:
                    level_num = 9
                    cleared_levels = 8
                    start_level(level_num)
                    
        # Update
        frame_count += 1
        wipe.update()
        
        # Logic blocked by wipe animation
        if not wipe.is_active():
            
            if game_state == STATE_BONUS_COUNTDOWN:
                if bonus_timer > 0:
                    subtract = min(10, bonus_timer)
                    bonus_timer -= subtract
                    score += subtract
                    res_manager.play_sound('bonus')
                else:
                    # Bonus done, next level
                    game_state = STATE_GAME
                    cleared_levels += 1
                    level_num += 1
                    wipe.start_level_wipe()
                    start_level(level_num)
        
            elif game_state == STATE_GAME:
                # Death Logic
                if player.state == player.STATE_DEATH:
                    # Wait for death sound to finish
                    playing = False
                    if player.death_channel:
                        playing = player.death_channel.get_busy()
                    
                    time_passed = pygame.time.get_ticks() - player.death_start_time
                    
                    # Wait until sound finishes (or 500ms min fallback if sound failed)
                    if not playing and time_passed > 500:
                        lives -= 1
                        if lives < 0:
                            # Game Over
                            game_state = STATE_INTRO
                            score = 0
                            lives = 4
                            level_num = 1
                            cleared_levels = 0
                            res_manager.play_music('theme', loops=0)
                        else:
                            start_level(level_num, reset_player=True)
                else:
                    # Normal Gameplay
                    if timer_freeze > 0:
                        timer_freeze -= 1
                    else:
                        # Timers
                        if game_timer > 0 and frame_count % 5 == 0:
                            game_timer -= 1
                            if game_timer == 0:
                                player.state = player.STATE_DEATH
                                player.death_start_time = pygame.time.get_ticks()
                                player.death_channel = res_manager.play_sound('death')
                        
                        if frame_count % 50 == 0 and bonus_timer > 0:
                            bonus_timer -= 10

                    # Updates
                    level.update_elevators()
                    player.update(level, keys)
                    
                    # Enemies
                    # Determine hen/duck junction counter (frame count)
                    junction_counter = frame_count 
                    

                    # hen/duck disabled per user request
                    for hen in hens:
                        hen.update(level, junction_counter)
                        if hen.check_collision(player):
                            player.state = player.STATE_DEATH
                            player.death_start_time = pygame.time.get_ticks()
                            player.death_channel = res_manager.play_sound('death')
                            
                    mother_duck.update(player.rect.x, player.rect.y, cleared_levels)
                    if mother_duck.check_collision(player):
                        player.state = player.STATE_DEATH
                        player.death_start_time = pygame.time.get_ticks()
                        player.death_channel = res_manager.play_sound('death')


                    # Collections
                    item = player.check_collectibles(level)
                    if item:
                        if item == TILE_EGG:
                            score += 100
                        elif item == TILE_CORN:
                            score += 50
                        timer_freeze = 150 
                        
                        if score >= extra_life_target:
                            lives += 1
                            extra_life_target += 10000
                
                # Check Level Completion
                if level.count_eggs() == 0 and player.state != player.STATE_DEATH:
                    # All eggs collected -> Bonus Countdown
                    game_state = STATE_BONUS_COUNTDOWN
        
        # Render
        screen.fill(COLOR_BLACK)
        
        if game_state == STATE_INTRO:
            if res_manager.loading_screen:
                screen.blit(res_manager.loading_screen, (0, 0))
        else:
            # Only draw game if wipe is NOT active (or at least map)
            # User wants: "hra nesmí vykreslit level, dokud se nedokončí wipe efekt"
            # AMENDMENT: Drawing level underneath so wipe overwrites it correctly.
            
            # Special case for Game Start Wipe: Draw Loading Screen behind it
            if wipe.is_active() and getattr(wipe, 'wipe_type', '') == 'game_start':
                if res_manager.loading_screen:
                    screen.blit(res_manager.loading_screen, (0, 0))
            else:
                level.draw(screen)
                mother_duck.draw_cage(screen) # Draw cage background
                for hen in hens:
                    hen.draw(screen)
                mother_duck.draw(screen)
                player.draw(screen)
                hud.draw(screen, score, level_num, bonus_timer, game_timer, lives)
            
        # Draw Wipe over everything
        if wipe.is_active():
            wipe.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

