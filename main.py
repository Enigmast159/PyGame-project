import os
import sys
import pygame
import random

pygame.init()

FPS = 50
WIDTH = 800
HEIGHT = 600
SCREEN_RECT = (0, 0, WIDTH, HEIGHT)
GRAVITY = 2


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
spike_group = pygame.sprite.Group()
borders = pygame.sprite.Group()
for_mask = pygame.sprite.Group()
tile_images = {
    'empty': None, 'wall': pygame.transform.scale(load_image('block.jpg'), (100, 100)), 'border': 1}
sounds = [pygame.mixer.Sound('sounds/menu_music.mp3'),
          pygame.mixer.Sound('sounds/level_music.mp3'),
          pygame.mixer.Sound('sounds/level_music_2.mp3'),
          pygame.mixer.Sound('sounds/level_music_3.mp3'),
          pygame.mixer.Sound('sounds/level_music_4.mp3'),
          pygame.mixer.Sound('sounds/level_music_5.mp3'),
          pygame.mixer.Sound('sounds/hit_in_border.mp3')]


class Border(pygame.sprite.Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(all_sprites, for_mask)
        self.add(borders)
        self.image = pygame.Surface([1, y2 - y1])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 1, y2 - y1)


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Spike(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, placed_down=True):
        super().__init__(spike_group, all_sprites, for_mask)
        if placed_down:
            self.image = pygame.transform.scale(load_image('spikes.png'), (100, 100))
        else:
            self.image = pygame.transform.scale(load_image('up_spikes.png'), (100, 100))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)
        self.mask = pygame.mask.from_surface(self.image)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.s_x, self.s_y = 5, 1
        self.count = 0
        self.jump_p = False
        self.frames = []
        for item in os.listdir(path="data/pl_go_anim"):
            item = 'pl_go_anim/' + item
            self.frames.append(pygame.transform.scale(load_image(item), (80, 80)))
        self.frames_jump = []
        for item in os.listdir(path="data/pl_jump_anim"):
            item = 'pl_jump_anim/' + item
            self.frames_jump.append(pygame.transform.scale(load_image(item), (80, 80)))
        self.cur_jump_frame = 0
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x + 15, tile_height * pos_y)

    def go(self, level_name, num):
        if self.count % 10 == 0 and self.jump_p:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.mask = pygame.mask.from_surface(self.image)
            self.cur_jump_frame = 0
        elif not self.jump_p:
            if self.count % 5 == 0:
                self.cur_jump_frame = (self.cur_jump_frame + 1) % len(self.frames_jump)
                self.image = self.frames_jump[self.cur_jump_frame]
        self.count += 1
        self.rect = self.rect.move(self.s_x, self.s_y)
        if pygame.sprite.spritecollideany(self, tiles_group):
            self.jump_p = True
            self.rect = self.rect.move(0, -self.s_y)
            self.s_y = 0
            self.s_x = 7
        elif not pygame.sprite.spritecollideany(self, tiles_group):
            self.jump_p = False
        for sprite in for_mask:
            if pygame.sprite.collide_mask(self, sprite):
                game_over(level_name, num)
        self.s_y += GRAVITY

    def jump(self):
        if self.jump_p:
            self.cur_jump_frame = 1
            self.jump_p = False
            self.s_y = -30
            self.s_x = 7


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
                Border(x * 100, y * 100 + 5, x * 100, (y + 1) * 100 - 5)
                Border((x + 1) * 100, y * 100 + 5, (x + 1) * 100, (y + 1) * 100 - 5)
                Tile('wall', x, y)
            elif level[y][x] == '@':
                new_player = Player(x, y)
            elif level[y][x] == '^':
                Spike(x, y)
            elif level[y][x] == 'v':
                Spike(x, y, False)
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
    sounds[0].play(loops=-1)
    sounds[0].set_volume(0.2)
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
                if play_b.rect.x < x < play_b.rect.x + 300 and \
                        play_b.rect.y < y < play_b.rect.y + 100:
                    play_b.kill()
                    custom.kill()
                    play()
                elif custom.rect.x < x < custom.rect.x + 300 and \
                        custom.rect.y < y < custom.rect.y + 100:
                    play_b.kill()
                    custom.kill()
                    customizing()
        button_sprite.draw(screen)
        pygame.display.flip()


def customizing():
    screen.fill((60, 107, 214))
    image = pygame.transform.scale(load_image('a_btn_1.png'), (300, 100))
    set_1 = pygame.sprite.Sprite(button_sprite)
    set_1.image = image
    set_1.rect = set_1.image.get_rect()
    set_1.rect.x, set_1.rect.y = 50, 50
    image = pygame.transform.scale(load_image('a_btn_2.png'), (300, 100))
    set_2 = pygame.sprite.Sprite(button_sprite)
    set_2.image = image
    set_2.rect = set_2.image.get_rect()
    set_2.rect.x, set_2.rect.y = 50, 200
    image = pygame.transform.scale(load_image('a_btn_3.png'), (300, 100))
    set_3 = pygame.sprite.Sprite(button_sprite)
    set_3.image = image
    set_3.rect = set_3.image.get_rect()
    set_3.rect.x, set_3.rect.y = 50, 350
    custom_running = True
    while custom_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if set_1.rect.x < x < set_1.rect.x + 300 and \
                        set_1.rect.y < y < set_1.rect.y + 100:
                    pass
                elif set_2.rect.x < x < set_2.rect.x + 300 and \
                        set_2.rect.y < y < set_2.rect.y + 100:
                    pass
                elif set_3.rect.x < x < set_3.rect.x + 300 and \
                        set_3.rect.y < y < set_3.rect.y + 100:
                    pass
        button_sprite.draw(screen)
        pygame.display.flip()


def start_level(level_name):
    sounds[0].stop()
    num = random.randint(1, 5)
    sounds[num].play(loops=-1)
    sounds[num].set_volume(0.1)
    level_running = True
    player, level_x, level_y = generate_level(load_level(level_name))
    camera = Camera((level_x, level_y))
    while level_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.jump()
        screen.fill((60, 107, 214))
        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)
        player.go(level_name, num)
        tiles_group.draw(screen)
        player_group.draw(screen)
        all_sprites.draw(screen)
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
            pygame.draw.rect(
                screen, pygame.Color('blue'), (right + i * w + i * 10, top + j * h + j * 10, w, h))
            font = pygame.font.Font(None, 30)
            text = font.render(str(name + 1), True, (100, 255, 100))
            text_w = text.get_width()
            text_h = text.get_height()
            text_x = right + i * 100 + i * 10 + w // 2 - text_w // 2
            text_y = top + j * 100 + j * 1 + h // 2 - text_h // 2
            screen.blit(text, (text_x, text_y))
        pygame.display.flip()
    terminate()


def game_over(level_name, num):
    sounds[num].stop()
    sounds[-1].play()
    sounds[-1].set_volume(0.2)
    background = pygame.transform.scale(load_image('game_over.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    for sprite in all_sprites:
        sprite.kill()
    game_over_running = True
    while game_over_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = event.pos
                    if 320 < x < 480 and 360 < y < 400:
                        start_level(level_name)
                    elif 320 < x < 480 and 410 < y < 450:
                        menu()
            button_sprite.draw(screen)
            pygame.display.flip()


start_screen()
