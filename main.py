# импортируем нужные библеотеки
import os
import sys
import pygame
import random
import sqlite3

# инициализация pygame'a
pygame.init()

# объявление констант
FPS = 50
WIDTH = 800
HEIGHT = 600
SCREEN_RECT = (0, 0, WIDTH, HEIGHT)
GRAVITY = 2
con = sqlite3.connect('db.db')
cur = con.cursor()
result = cur.execute("""Select coins from coins""").fetchall()
COINS = result[0][0]
sound_count = 2
blocks = {'Standard': 'block.jpg', 'Farmer': 'block3.png', 'Mario': 'block2.png'}
set_for_playing = 'Standard'
sets_dict = {'Standard': '', 'Farmer': 'farm_goose/',
             'Mario': 'mario_goose/', 'Sherlock': 'sherlock-goose/'}


# функция для загрузки изображений
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


# объявление важныъ списков переменных и групп
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
coins = pygame.sprite.Group()
portals = pygame.sprite.Group()
tile_images = {
    'empty': None, 'wall': pygame.transform.scale(load_image('block3.png'), (100, 100)),
    'border': 1}
sounds = [pygame.mixer.Sound('sounds/menu_music.mp3'),
          pygame.mixer.Sound('sounds/level_music.mp3'),
          pygame.mixer.Sound('sounds/level_music_2.mp3'),
          pygame.mixer.Sound('sounds/level_music_3.mp3'),
          pygame.mixer.Sound('sounds/level_music_4.mp3'),
          pygame.mixer.Sound('sounds/level_music_5.mp3'),
          pygame.mixer.Sound('sounds/store_music.mp3'),
          pygame.mixer.Sound('sounds/coin.mp3'),
          pygame.mixer.Sound('sounds/hit_in_border.mp3')]
cheated = False


# функция для контролирования звука
def sound_control():
    if sound_count % 2 != 0:
        for sound in sounds:
            sound.set_volume(0)
    else:
        for i in range(len(sounds)):
            if i == 7:
                sounds[i].set_volume(0.2)
            else:
                sounds[i].set_volume(0.05)


# класс барьеров вокруг блоков
class Border(pygame.sprite.Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(all_sprites, for_mask, borders)
        self.image = pygame.Surface([1, y2 - y1])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = pygame.Rect(x1, y1, 1, y2 - y1)


# класс блоков и пустоты
class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


# класс шипов
class Spike(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, placed_down=True):
        super().__init__(spike_group, all_sprites, for_mask)
        if placed_down:
            self.image = pygame.transform.scale(load_image('spikes.png'), (100, 100))
        else:
            self.image = pygame.transform.scale(load_image('up_spikes.png'), (100, 100))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)
        self.mask = pygame.mask.from_surface(self.image)


# класс монеток
class Coin(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, pos_x, pos_y):
        super().__init__(all_sprites, coins)
        self.count = 5
        self.x = x
        self.y = y
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)

    # нарезаем фреймы
    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, self.x, self.y)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i + i * 4, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    # обновление
    def update(self):
        if self.count % 5 == 0:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
        self.count += 1


# класс портала, для прохождения уровня
class Portal(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(portals, all_sprites)
        self.image = pygame.transform.scale(load_image('portal.jpg', None), (80, 100))
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


# игроки
class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, way=''):
        super().__init__(player_group, all_sprites)
        self.coins_count = 0
        self.s_x, self.s_y = 5, 1
        self.score = 0
        self.count = 0
        self.jump_p = False
        self.frames = []
        for item in os.listdir(path='data/' + way + "pl_go_anim"):
            item = way + 'pl_go_anim/' + item
            self.frames.append(pygame.transform.scale(load_image(item), (70, 80)))
        self.frames_jump = []
        for item in os.listdir(path='data/' + way + "pl_jump_anim"):
            item = way + 'pl_jump_anim/' + item
            self.frames_jump.append(pygame.transform.scale(load_image(item), (70, 80)))
        self.cur_jump_frame = 0
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x + 15, tile_height * pos_y)

    # функция для ходьбы и прыжка персонажа
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
        if pygame.sprite.spritecollideany(self, portals):
            win(self.coins_count, num, self.score, level_name)
        if pygame.sprite.spritecollideany(self, tiles_group):
            self.jump_p = True
            self.rect = self.rect.move(0, -self.s_y)
            self.s_y = 0
            self.s_x = 7
        elif not pygame.sprite.spritecollideany(self, tiles_group):
            self.jump_p = False
        for sprite in for_mask:
            if pygame.sprite.collide_mask(self, sprite):
                game_over(level_name, num, self.score, self.coins_count)
        for sprite in coins:
            if pygame.sprite.collide_mask(self, sprite):
                self.coins_count += 1
                sprite.kill()
                sounds[7].play()
        self.s_y += GRAVITY

    # функция прыжка
    def jump(self):
        if self.jump_p:
            self.cur_jump_frame = 0
            self.jump_p = False
            self.s_y = -29
            self.s_x = 8


# функция прекращения работы
def terminate():
    con.close()
    pygame.quit()
    sys.exit()


# функция загрузки уровня
def load_level(filename):
    filename = 'levels/' + filename
    with open(filename, 'r') as map_file:
        level_map = [line.strip() for line in map_file]
        max_width = max(map(len, level_map))
    return list(map(lambda line: line.ljust(max_width, '.'), level_map))


# функция генерирования уровня
def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if (level[y][x] == '' or level[y][x] == '.') and cheated:
                Coin(load_image('coin.png', -1), 8, 1, 60, 64, x, y)
            elif level[y][x] == '#':
                Border(x * 100, y * 100 + 5, x * 100, (y + 1) * 100 - 5)
                Border((x + 1) * 100, y * 100 + 5, (x + 1) * 100, (y + 1) * 100 - 5)
                Border(x * 100, y * 100 + 95, (x + 1) * 100, (y + 1) * 100)
                Tile('wall', x, y)
            elif level[y][x] == '@':
                new_player = Player(x, y, sets_dict[set_for_playing])
            elif level[y][x] == '^':
                Spike(x, y)
            elif level[y][x] == 'v':
                Spike(x, y, False)
            elif level[y][x] == '0':
                Coin(load_image('coin.png', -1), 8, 1, 60, 64, x, y)
            elif level[y][x] == '$':
                Portal(x, y)
    return new_player, x, y


# класс камеры
class Camera:
    def __init__(self, field_size):
        self.dx = 0
        self.field_size = field_size

    def apply(self, obj):
        obj.rect.x += self.dx

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)


# функция включения чит-режима)
def cheating():
    global cheated
    font = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()
    input_box = pygame.Rect(100, 100, 140, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        print(text)
                        if text.lower() == 'жумайсынба':
                            cheated = not cheated
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
        screen.fill((30, 30, 30))
        text_surface = font.render(text, True, color)
        width = max(200, text_surface.get_width() + 10)
        input_box.w = width
        screen.blit(text_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()
        clock.tick(30)


# функция статового экрана
def start_screen():
    sounds[0].play(loops=-1)
    sounds[0].set_volume(0.05)
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

# функция обработки списка из дб
def transform(s):
    s = list(s)
    s[0] = s[0].strip('.txt').strip('lev_')
    s[1] = str(s[1])
    s[2] = str(s[2])
    s[0] = s[0] + ' ' * (19 - len(s[0]))
    s[1] = s[1] + ' ' * 2 * (8 - len(s[1]))
    return ''.join(s)


# функция меню статистики
def statistics():
    image = pygame.transform.scale(load_image('to_menu_btn-1.png'), (320, 80))
    to_menu = pygame.sprite.Sprite(button_sprite)
    to_menu.image = image
    to_menu.rect = to_menu.image.get_rect()
    to_menu.rect.x, to_menu.rect.y = 250, 500
    res = ['Уровень   Очки   Монеты']
    res += list(map(transform, cur.execute('select * from Statistics order by level').fetchall()))
    background = pygame.transform.scale(load_image('goose1.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    font = pygame.font.Font(None, 34)
    text_coord = 50
    for line in res:
        string_render = font.render(line, True, pygame.Color('green'))
        string_rect = string_render.get_rect()
        text_coord += 10
        string_rect.top = text_coord
        string_rect.x = 10
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if to_menu.rect.x < x < to_menu.rect.x + 320 and \
                        to_menu.rect.y < y < to_menu.rect.y + 80:
                    to_menu.image = pygame.transform.scale(
                        load_image('to_menu_btn-2.png'), (320, 80))
                else:
                    to_menu.image = pygame.transform.scale(
                        load_image('to_menu_btn-1.png'), (320, 80))
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if to_menu.rect.x < x < to_menu.rect.x + 320 and \
                        to_menu.rect.y < y < to_menu.rect.y + 80:
                    to_menu.kill()
                    menu()
        button_sprite.draw(screen)
        pygame.display.flip()


# функция главного меню
def menu():
    global sound_count
    sound_control()
    background = pygame.transform.scale(load_image('goose2.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    image = pygame.transform.scale(load_image('p_button3_1.png'), (320, 80))
    sound_onoff = pygame.sprite.Sprite(button_sprite)
    sound_onoff.image = pygame.transform.scale(load_image('sound_on.png', -1), (50, 50))
    sound_onoff.rect = sound_onoff.image.get_rect()
    sound_onoff.rect.x, sound_onoff.rect.y = 720, 520
    play_b = pygame.sprite.Sprite(button_sprite)
    play_b.image = image
    play_b.rect = play_b.image.get_rect()
    play_b.rect.x, play_b.rect.y = 50, 50
    image = pygame.transform.scale(load_image('cust_button3_1.png'), (320, 80))
    custom = pygame.sprite.Sprite(button_sprite)
    custom.image = image
    custom.rect = custom.image.get_rect()
    custom.rect.x, custom.rect.y = 50, 200
    image = pygame.transform.scale(load_image('question.png'), (100, 100))
    question = pygame.sprite.Sprite(button_sprite)
    question.image = image
    question.rect = question.image.get_rect()
    question.rect.x, question.rect.y = 720, -30
    image = pygame.transform.scale(load_image('stat_button_1.png'), (320, 80))
    stats = pygame.sprite.Sprite(button_sprite)
    stats.image = image
    stats.rect = stats.image.get_rect()
    stats.rect.x, stats.rect.y = 50, 350
    running = True
    while running:
        sound_control()
        screen.blit(background, (0, 0))
        for event in pygame.event.get():
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LCTRL] and keys[pygame.K_LSHIFT]:
                cheating()
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if play_b.rect.x < x < play_b.rect.x + 320 and \
                        play_b.rect.y < y < play_b.rect.y + 80:
                    play_b.image = pygame.transform.scale(load_image('p_button3_2.png'), (320, 80))
                else:
                    play_b.image = pygame.transform.scale(load_image('p_button3_1.png'), (320, 80))
                if custom.rect.x < x < custom.rect.x + 320 and \
                        custom.rect.y < y < custom.rect.y + 80:
                    custom.image = pygame.transform.scale(
                        load_image('cust_button3_2.png'), (320, 80))
                else:
                    custom.image = pygame.transform.scale(
                        load_image('cust_button3_1.png'), (320, 80))
                if stats.rect.x < x < stats.rect.x + 320 and \
                        stats.rect.y < y < stats.rect.y + 80:
                    stats.image = pygame.transform.scale(load_image('stat_button_2.png'), (320, 80))
                else:
                    stats.image = pygame.transform.scale(load_image('stat_button_1.png'), (320, 80))
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if play_b.rect.x < x < play_b.rect.x + 320 and \
                        play_b.rect.y < y < play_b.rect.y + 80:
                    play_b.kill()
                    custom.kill()
                    stats.kill()
                    question.kill()
                    sound_onoff.kill()
                    play()
                elif custom.rect.x < x < custom.rect.x + 320 and \
                        custom.rect.y < y < custom.rect.y + 80:
                    play_b.kill()
                    custom.kill()
                    question.kill()
                    stats.kill()
                    sound_onoff.kill()
                    customizing()
                elif question.rect.x < x < question.rect.x + 100 and \
                        question.rect.y < y < question.rect.y + 100:
                    play_b.kill()
                    custom.kill()
                    stats.kill()
                    question.kill()
                    sound_onoff.kill()
                    description()
                elif stats.rect.x < x < stats.rect.x + 320 and \
                        stats.rect.y < y < stats.rect.y + 80:
                    play_b.kill()
                    stats.kill()
                    custom.kill()
                    question.kill()
                    sound_onoff.kill()
                    statistics()
                elif sound_onoff.rect.x < x < sound_onoff.rect.x + 50 and \
                        sound_onoff.rect.y < y < sound_onoff.rect.y + 50:
                    sound_count += 1
            if sound_count % 2 != 0:
                sound_onoff.image = pygame.transform.scale(load_image('sound_off.png'), (50, 50))
            else:
                sound_onoff.image = pygame.transform.scale(load_image('sound_on.png'), (50, 50))
        button_sprite.draw(screen)
        pygame.display.flip()


# функция меню кастомизации
def customizing():
    global COINS, set_for_playing, cur
    sounds[0].stop()
    sounds[6].play(loops=-1)
    sounds[6].set_volume(0.2)
    sound_control()
    screen.fill(pygame.Color(60, 107, 214))
    image = pygame.transform.scale(load_image('orig_btn-1.png'), (280, 75))
    set_1 = pygame.sprite.Sprite(button_sprite)
    set_1.image = image
    set_1.rect = set_1.image.get_rect()
    set_1.rect.x, set_1.rect.y = 10, 50
    image = pygame.transform.scale(load_image('farm_btn-1.png'), (280, 75))
    set_2 = pygame.sprite.Sprite(button_sprite)
    set_2.image = image
    set_2.rect = set_2.image.get_rect()
    set_2.rect.x, set_2.rect.y = 10, 200
    image = pygame.transform.scale(load_image('mar_btn-1.png'), (280, 75))
    set_3 = pygame.sprite.Sprite(button_sprite)
    set_3.image = image
    set_3.rect = set_3.image.get_rect()
    set_3.rect.x, set_3.rect.y = 10, 350
    image = pygame.transform.scale(load_image('a_buy_btn.png'), (200, 70))
    buy = pygame.sprite.Sprite(button_sprite)
    buy.image = image
    buy.rect = buy.image.get_rect()
    buy.rect.x, buy.rect.y = 320, 350
    image = pygame.transform.scale(load_image('a_choose_btn.png'), (200, 70))
    choose = pygame.sprite.Sprite(button_sprite)
    choose.image = image
    choose.rect = choose.image.get_rect()
    choose.rect.x, choose.rect.y = 550, 350
    to_menu = pygame.sprite.Sprite(button_sprite)
    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-1.png'), (300, 75))
    to_menu.rect = to_menu.image.get_rect()
    to_menu.rect.x, to_menu.rect.y = 250, 500
    sets_list = ['', 'Standard', 'Farmer', 'Mario', 'Sherlock']
    image = None
    pushed = 0
    custom_running = True
    is_chosen = False
    while custom_running:
        screen.fill(pygame.Color(60, 107, 214))
        text = f'Ваш баланс: {COINS} монет'
        font = pygame.font.Font(None, 30)
        text_coord = 10
        string_render = font.render(text, True, pygame.Color('green'))
        string_rect = string_render.get_rect()
        string_rect.top = text_coord
        string_rect.x = 10
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)
        text = 'Цена:'
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if set_1.rect.x < x < set_1.rect.x + 300 and \
                        set_1.rect.y < y < set_1.rect.y + 75:
                    set_1.image = pygame.transform.scale(load_image('orig_btn-2.png'), (280, 75))
                    set_2.image = pygame.transform.scale(load_image('farm_btn-1.png'), (280, 75))
                    set_3.image = pygame.transform.scale(load_image('mar_btn-1.png'), (280, 75))
                    for sprite in button_sprite:
                        if sprite.image == image:
                            sprite.kill()
                    is_chosen = True
                    pushed = 1
                    image = pygame.transform.scale(
                        load_image('pl_go_anim/goose_pl-2.png'), (125, 125))
                elif set_2.rect.x < x < set_2.rect.x + 300 and \
                        set_2.rect.y < y < set_2.rect.y + 75:
                    set_2.image = pygame.transform.scale(load_image('farm_btn-2.png'), (280, 75))
                    set_1.image = pygame.transform.scale(load_image('orig_btn-1.png'), (280, 75))
                    set_3.image = pygame.transform.scale(load_image('mar_btn-1.png'), (280, 75))
                    for sprite in button_sprite:
                        if sprite.image == image:
                            sprite.kill()
                    is_chosen = True
                    pushed = 2
                    image = pygame.transform.scale(
                        load_image('farm_goose/pl_go_anim/goose_pl-2.png'), (125, 125))
                elif set_3.rect.x < x < set_3.rect.x + 300 and \
                        set_3.rect.y < y < set_3.rect.y + 75:
                    set_1.image = pygame.transform.scale(load_image('orig_btn-1.png'), (280, 75))
                    set_2.image = pygame.transform.scale(load_image('farm_btn-1.png'), (280, 75))
                    set_3.image = pygame.transform.scale(load_image('mar_btn-2.png'), (280, 75))
                    for sprite in button_sprite:
                        if sprite.image == image:
                            sprite.kill()
                    is_chosen = True
                    pushed = 3
                    image = pygame.transform.scale(
                        load_image('mario_goose/pl_go_anim/goose_pl-2.png'), (125, 125))
                elif buy.rect.x < x < buy.rect.x + 300 and \
                        buy.rect.y < y < buy.rect.y + 75:
                    if is_chosen:
                        result = cur.execute("""Select Is_buyed from Sets Where Name=?""",
                                             (sets_list[pushed],)).fetchall()
                        if not int(result[0][0]):
                            result = cur.execute("""Select Cost from Sets Where Name=?""",
                                                 (sets_list[pushed],)).fetchall()
                            if COINS >= int(result[0][0]):
                                COINS -= int(result[0][0])
                                cur.execute("""UPDATE Sets 
                                               SET Is_buyed = 1
                                               WHERE Name = ?""", (sets_list[pushed],)).fetchall()
                                cur.execute(f"""UPDATE coins
                                               SET coins={COINS}""")
                                con.commit()
                elif choose.rect.x < x < choose.rect.x + 300 and \
                        choose.rect.y < y < choose.rect.y + 75:
                    if is_chosen:
                        result = cur.execute("""Select Is_buyed from Sets Where Name=?""",
                                             (sets_list[pushed],)).fetchall()
                        con.commit()
                        if result[0][0]:
                            set_for_playing = sets_list[pushed]
                elif to_menu.rect.x < x < to_menu.rect.x + 300 and \
                        to_menu.rect.y < y < to_menu.rect.y + 75:
                    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-2.png'),
                                                           (300, 75))
                    for sprite in button_sprite:
                        sprite.kill()
                    sounds[6].stop()
                    sounds[0].play(loops=-1)
                    menu()
        if is_chosen:
            result = cur.execute("""Select Is_buyed from Sets Where Name=?""",
                                 (sets_list[pushed],)).fetchall()
            if not int(result[0][0]):
                result = cur.execute("""Select Cost from Sets Where Name=?""",
                                     (sets_list[pushed],)).fetchall()
                price = int(result[0][0])
                text = text + ' ' + str(price)
            else:
                text = 'Куплено'
            font = pygame.font.Font(None, 30)
            text_coord = 100
            string_render = font.render(text, True, pygame.Color('green'))
            string_rect = string_render.get_rect()
            string_rect.top = text_coord
            string_rect.x = 350
            text_coord += string_rect.height
            screen.blit(string_render, string_rect)
            chosen_set = pygame.sprite.Sprite(button_sprite)
            chosen_set.image = image
            chosen_set.rect = chosen_set.image.get_rect()
            chosen_set.rect.x, chosen_set.rect.y = 450, 175
        button_sprite.draw(screen)
        pygame.display.flip()


# функция описания
def description():
    screen.fill(pygame.Color((60, 107, 214)))
    text = ['Goose game ', 'компьютерная игра в жанре 2D-платформера',
            'Главный герой - гусь, который проходит',
            'уровни с множеством препятствий под музыку']
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


# функция выйграша
def win(coins_count, num, score, level_name):
    global COINS
    COINS += coins_count
    cur.execute(f"""UPDATE coins SET coins={COINS}""")
    try:
        res = cur.execute(
            f'select Points, max_coins from Statistics where level={level_name}').fetchall()
    except Exception:
        cur.execute(
            f'insert or replace into Statistics values("{level_name}", {score}, {coins_count})')
        con.commit()
    else:
        if res[1][0] < coins_count:
            cur.execute(
                f'update Statistics set max_coins={coins_count} and points={score} '
                f'where level={level_name}')
        else:
            cur.execute(f'update Statistics set points={score} where level={level_name}')
    con.commit()
    res = cur.execute(f'select Points from Statistics where level="{level_name}"').fetchall()
    text = ['Поздравляю!', 'Вы прошли уровень!', f'Вы собрали {str(coins_count)} монет',
            f'Ваш счет: {score}', '', f'Ваш лучший счет: {str(res[0][0])}',
            'Нажмите любую кнопку,', 'чтобы перейти в меню']
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
                sounds[num].stop()
                for sprite in all_sprites:
                    sprite.kill()
                sounds[0].play()
                menu()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

# функция самого уровня(загрузка и основной цикл уровня)
def start_level(level_name):
    sounds[0].stop()
    num = random.randint(1, 5)
    sounds[num].play(loops=-1)
    sounds[num].set_volume(0.1)
    sound_control()
    sheet = pygame.sprite.Sprite(all_sprites)
    sheet.image = load_image('coin.png', -1).subsurface(pygame.Rect(0, 0, 60, 64))
    sheet.rect = sheet.image.get_rect()
    sheet.rect.x, sheet.rect.y = 60, 0
    level_running = True
    try:
        res = cur.execute(f'select Points from Statistics where level="{level_name}"').fetchall()
        best_score = res[0][0]
    except Exception:
        cur.execute(
            f'insert or replace into Statistics values("{level_name}", {0}, {0})')
        con.commit()
        res = cur.execute(f'select Points from Statistics where level="{level_name}"').fetchall()
        best_score = res[0][0]
    tile_images['wall'] = pygame.transform.scale(load_image(blocks[set_for_playing]), (100, 100))
    player, level_x, level_y = generate_level(load_level(level_name))
    camera = Camera((level_x, level_y))
    while level_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    player.jump()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                pause()
        screen.fill(pygame.Color((60, 107, 214)))
        sheet.rect = sheet.image.get_rect().move(60, 0)
        camera.update(player)
        for sprite in all_sprites:
            camera.apply(sprite)
        coins.update()
        player.go(level_name, num)
        tiles_group.draw(screen)
        player_group.draw(screen)
        all_sprites.draw(screen)
        clock.tick(FPS)
        font = pygame.font.Font(None, 72)
        text_coord = 10
        string_render = font.render(str(player.coins_count), True, pygame.Color('yellow'))
        string_rect = string_render.get_rect()
        string_rect.top = text_coord
        string_rect.x = 10
        screen.blit(string_render, string_rect)
        score = player.count // 2 + 100 * player.coins_count
        player.score = score
        text = 'Ваши очки: ' + str(score)
        font = pygame.font.Font(None, 30)
        text_coord = 10
        string_render = font.render(text, True, pygame.Color('green'))
        string_rect = string_render.get_rect()
        string_rect.top = text_coord
        string_rect.x = 600
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)
        text = 'Ваш последний счет: ' + str(best_score)
        font = pygame.font.Font(None, 30)
        text_coord = 10
        string_render = font.render(text, True, pygame.Color('green'))
        string_rect = string_render.get_rect()
        string_rect.top = text_coord
        string_rect.x = 300
        text_coord += string_rect.height
        screen.blit(string_render, string_rect)
        pygame.display.flip()


# функция паузы
def pause():
    image = pygame.transform.scale(load_image('ad.jpg'), (135, 291))
    ad = pygame.sprite.Sprite(all_sprites)
    ad.image = image
    ad.rect = ad.image.get_rect()
    ad.rect.x, ad.rect.y = 50, 200
    text = ['                                           PAUSE',
            'Шампунь "Жумайсынба" ', 'Скажи перхоти',
            'Көзіме көрінбейтін бол э, түсіндің ба!']
    font = pygame.font.Font(None, 30)
    text_coord = 50
    string_render = font.render(text[0], True, pygame.Color('blue'))
    string_rect = string_render.get_rect()
    text_coord += 10
    string_rect.top = text_coord
    string_rect.x = 10
    text_coord += string_rect.height
    screen.blit(string_render, string_rect)
    del text[0]
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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                ad.kill()
                return
        all_sprites.draw(screen)
        pygame.display.flip()


# функция выбора уровня
def play():
    files = os.listdir(path="levels")  # функция для подсчета файлов в папке
    top, right = 50, 100
    w, h = 100, 100
    image = pygame.transform.scale(load_image('lev_btn-1.png'), (w, h))
    to_menu = pygame.sprite.Sprite(button_sprite)
    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-1.png'), (300, 75))
    to_menu.rect = to_menu.image.get_rect()
    to_menu.rect.x, to_menu.rect.y = 250, 500
    for i in range(len(files)):
        name = i
        j = i // 5
        if j > 0:
            i = i - 5 * j
        btn = pygame.sprite.Sprite(button_sprite)
        btn.image = image
        btn.rect = btn.image.get_rect()
        btn.rect.x, btn.rect.y = right + i * w + i * 10, top + j * h + j * 10
    running = True
    while running:
        screen.fill((60, 107, 214))
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
                    if (right + i * w + i * 10 < x < right + i * w + i * 10 + 100 and
                            top + j * h + j * 10 < y < top + j * h + j * 10 + 100):
                        for sprite in button_sprite:
                            sprite.kill()
                        start_level(files[name])
                        terminate()
                if (to_menu.rect.x < x < to_menu.rect.x + 300 and
                        to_menu.rect.y < y < to_menu.rect.y + 75):
                    for sprite in button_sprite:
                        sprite.kill()
                    menu()
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                for sprite in button_sprite:
                    if (sprite.rect.x < x < sprite.rect.x + w and
                            sprite.rect.y < y < sprite.rect.y + h):
                        sprite.image = pygame.transform.scale(load_image('lev_btn-2.png'), (w, h))
                    else:
                        sprite.image = pygame.transform.scale(load_image('lev_btn-1.png'), (w, h))
                if (to_menu.rect.x < x < to_menu.rect.x + 300 and
                        to_menu.rect.y < y < to_menu.rect.y + 75):
                    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-2.png'),
                                                           (300, 75))
                else:
                    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-1.png'),
                                                           (300, 75))
        button_sprite.draw(screen)
        for i in range(len(files)):
            name = i
            j = i // 5
            if j > 0:
                i = i - 5 * j
            font = pygame.font.Font(None, 35)
            text = font.render(str(name + 1), True, (250, 17, 102))
            text_w = text.get_width()
            text_h = text.get_height()
            text_x = right + i * 100 + i * 10 + w // 2 - text_w // 2
            text_y = top + j * 100 + j * 1 + h // 2 - text_h // 2
            screen.blit(text, (text_x, text_y))
        pygame.display.flip()
    terminate()


# функция проигрыша
def game_over(level_name, num, score, coins):
    sounds[num].stop()
    sounds[-1].play()
    sounds[-1].set_volume(0.2)
    sound_control()
    try:
        res = cur.execute(
            f'select Points, max_coins from Statistics where level={level_name}').fetchall()
    except Exception:
        cur.execute(f'insert or replace into Statistics values("{level_name}", {score}, {coins})')
        con.commit()
    else:
        if res[1][0] < coins:
            cur.execute(
                f'update Statistics set max_coins={coins} and points={score} '
                f'where level={level_name}')
        else:
            cur.execute(f'update Statistics set points={score} where level={level_name}')
    background = pygame.transform.scale(load_image('goose4.png', None), (WIDTH, HEIGHT))
    screen.blit(background, (0, 0))
    restart = pygame.sprite.Sprite(button_sprite)
    restart.image = pygame.transform.scale(load_image('res_btn_1.png'), (300, 70))
    restart.rect = restart.image.get_rect()
    restart.rect.x, restart.rect.y = 480, 50
    to_menu = pygame.sprite.Sprite(button_sprite)
    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-1.png'), (300, 70))
    to_menu.rect = to_menu.image.get_rect()
    to_menu.rect.x, to_menu.rect.y = 480, 140
    text = [f'Не расстраивайтесь!', f'Вы на брали {score} очков!']
    for sprite in all_sprites:
        sprite.kill()
    game_over_running = True
    while game_over_running:
        screen.blit(background, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = event.pos
                    if restart.rect.x < x < restart.rect.x + 300 and\
                       restart.rect.y < y < restart.rect.y + 70:
                        for sprite in button_sprite:
                            sprite.kill()
                        start_level(level_name)
                    elif(to_menu.rect.x < x < to_menu.rect.x + 300 and
                         to_menu.rect.y < y < to_menu.rect.y + 70):
                        for sprite in button_sprite:
                            sprite.kill()
                        sounds[0].play(loops=-1)
                        sounds[0].set_volume(0.05)
                        menu()
            if event.type == pygame.MOUSEMOTION:
                x, y = event.pos
                if to_menu.rect.x < x < to_menu.rect.x + 300 and \
                   to_menu.rect.y < y < to_menu.rect.y + 70:
                    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-2.png'),
                                                           (300, 70))
                else:
                    to_menu.image = pygame.transform.scale(load_image('to_menu_btn-1.png'),
                                                           (300, 70))
                if restart.rect.x < x < restart.rect.x + 300 and \
                   restart.rect.y < y < restart.rect.y + 70:
                    restart.image = pygame.transform.scale(load_image('res_btn_2.png'), (300, 70))
                else:
                    restart.image = pygame.transform.scale(load_image('res_btn_1.png'), (300, 70))
            button_sprite.draw(screen)
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
            pygame.display.flip()


# запуск
start_screen()
