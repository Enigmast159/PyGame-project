import os
import sys
import pygame

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
player_image = pygame.transform.scale(load_image('goose_pl-1.png'), (100, 100))


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

    def go(self, s_x, s_y):
        self.rect = self.rect.move(s_x, s_y)
        if pygame.sprite.spritecollideany(self, tiles_group):
            self.rect = self.rect.move(-s_x, -s_y)


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
    pygame.mixer.music.load('sounds/menu_bg_sound.mp3')
    pygame.mixer.music.play(loops=-1)
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
                    play_b.kill()
                    custom.kill()
                    play()
                elif custom.rect.x < x < custom.rect.x + 300 and custom.rect.y < y < custom.rect.y + 100:
                    play_b.kill()
                    custom.kill()
                    customizing()
        button_sprite.draw(screen)
        pygame.display.flip()


def customizing():
    pass


def start_level(level_name):
    level_running = True
    player, tiles_w, tiles_h = generate_level(load_level(level_name))
    while level_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pass
        screen.fill((0, 0, 0))
        player.go(5, 10)
        tiles_group.draw(screen)
        player_group.draw(screen)
        clock.tick(FPS)
        pygame.display.flip()


def play():
    running = True
    while running:
        screen.fill((60, 107, 214))
        files = os.listdir(path="levels")  # функция для подсчета файлов в папке
        top, right = 50, 100
        w, h = 100, 100
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i in range(len(files)):
                    name = i
                    j = i // 5
                    if j > 0:
                        i = i - 5 * j
                    if(right + i * w + i * 10 < x < right + i * w + i * 10 + 100 and
                       top + j * h + j * 10 < y < top + j * h + j * 10 + 100):
                        start_level(files[name])
                        terminate()
        for i in range(len(files)):
            name = i
            j = i // 5
            if j > 0:
                i = i - 5 * j
            pygame.draw.rect(screen, pygame.Color('blue'), (right + i * w + i * 10, top + j * h + j * 10, w, h))
            font = pygame.font.Font(None, 30)
            text = font.render(str(name + 1), True, (100, 255, 100))
            text_w = text.get_width()
            text_h = text.get_height()
            text_x = right + i * 100 + i * 10 + w // 2 - text_w // 2
            text_y = top + j * 100 + j * 1 + h // 2 - text_h // 2
            screen.blit(text, (text_x, text_y))
        pygame.display.flip()
    terminate()


start_screen()
