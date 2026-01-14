import pygame
import os

pygame.init()
pygame.display.set_mode((1, 1))

sprites_dir = 'assets/sprites'
for f in os.listdir(sprites_dir):
    if f.endswith('.png'):
        path = os.path.join(sprites_dir, f)
        img = pygame.image.load(path)
        print(f"{f}: {img.get_width()}x{img.get_height()}")
pygame.quit()
