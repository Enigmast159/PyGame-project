import os
import sys
import pygame

pygame.init()

FPS = 60
WIDTH = 800
HEIGHT = 500
SCREEN_RECT = (0, 0, WIDTH, HEIGHT)


screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()


def load_image(name, color_key=-1):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(pygame.Color('black'))
    pygame.display.flip()
    clock.tick(FPS)
terminate()