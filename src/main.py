
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
    player = Player(100, 100, res_manager) # Spawn at 100,100 for test
    
    running = True
    while running:
        # Event handling
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    level.set_level('level_1')
                elif event.key == pygame.K_2:
                    level.set_level('level_2')
                elif event.key == pygame.K_3:
                    level.set_level('level_3')
                elif event.key == pygame.K_4:
                    level.set_level('level_4')
                elif event.key == pygame.K_5:
                    level.set_level('level_5')
                elif event.key == pygame.K_6:
                    level.set_level('level_6')
                elif event.key == pygame.K_7:
                    level.set_level('level_7')
                elif event.key == pygame.K_8:
                    level.set_level('level_8')
                    
        # Update
        player.update(level, keys)
        
        # Render
        screen.fill(COLOR_BLACK)
        
        level.draw(screen)
        player.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
