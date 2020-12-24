import os
import sys
import pygame
from math import ceil

pygame.init()

FPS = 60
WIDTH = 800
HEIGHT = 600
SCREEN_RECT = (0, 0, WIDTH, HEIGHT)
SPEED = 500


def load_image(name, color_key=-1):
    try:
        fullname = os.path.join('data/', name)
        image = pygame.image.load(fullname).convert()
    except Exception as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
tile_width = tile_height = 100
button_sprite = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tile_images = {'empty': None, 'wall': pygame.transform.scale(load_image('block.jpg'), (100, 100))}
player_image = pygame.transform.scale(load_image('pl.png'), (100, 100))


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect().move(tile_width * pos_x + 15, tile_height * pos_y + 5)

    def go(self):
        self.rect = self.image.get_rect().move(10, 0)


def terminate():
    pygame.quit()
    sys.exit()


def load_level(filename):
    filename = 'levels/' + filename
    with open(filename, 'r') as map_file:
        level_map = [line.strip() for line in map_file]
        max_width = max(map(len, level_map))
    return list(map(lambda line: line.ljust(max_width, '.'), level_map))


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '' or level[y][x] == '.':
                pass
            elif level[y][x] == '#':
                Tile('wall', x, y)
            elif level[y][x] == '@':
                new_player = Player(x, y)
    return new_player, x, y


class Camera:
    def __init__(self, field_size):
        self.dx = 0
        self.field_size = field_size

    def apply(self, obj):
        obj.rect.x += self.dx

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)


def start_screen():
    text = ['Welcome to ', '', 'Goose game']
    background = pygame.transform.scale(load_image('goose1.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in text:
        string_render = font.render(line, True, pygame.Color('green'))
        string_rect = string_render.get_rect()
        text_coord += 10
        string_rect.top = text_coord
        string_rect.x = 10
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                menu()
        pygame.display.flip()
        clock.tick(FPS)


def menu():
    background = pygame.transform.scale(load_image('goose2.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    image = pygame.transform.scale(load_image('p_button2.png', -1), (300, 100))
    play_b = pygame.sprite.Sprite(button_sprite)
    play_b.image = image
    play_b.rect = play_b.image.get_rect()
    play_b.rect.x, play_b.rect.y = 50, 50
    image = pygame.transform.scale(load_image('customize_button.png', -1), (300, 100))
    custom = pygame.sprite.Sprite(button_sprite)
    custom.image = image
    custom.rect = custom.image.get_rect()
    custom.rect.x, custom.rect.y = 50, 200
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if play_b.rect.x < x < play_b.rect.x + 300 and play_b.rect.y < y < play_b.rect.y + 100:
                    files = os.listdir(path="levels") # функция для подсчета файлов в папке,
                    print(len(files)) # будем использовать её для подсчета уровней
                    print('play')
                    play()
                elif custom.rect.x < x < custom.rect.x + 300 and custom.rect.y < y < custom.rect.y + 100:
                    print('customize')
                    customizing()
        button_sprite.draw(screen)
        pygame.display.flip()


def customizing():
    pass


def play():
    pass


start_screen()