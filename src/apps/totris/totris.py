import random
import displayio
import terminalio
import time
import adafruit_imageload
import json
from adafruit_display_text.label import Label
from supervisor import ticks_ms

from badge.constants import LCD_WIDTH, LCD_HEIGHT, EPD_SMALL
from badge.screens import LCD, EPD, center_text_x_plane
from badge.neopixels import NP
from badge_nvm import nvm_open
from badge.buttons import a_pressed, b_pressed, c_pressed, d_pressed
from leaderboard import post_to_leaderboard

TICKS_PERIOD = const(1<<29)
TICKS_MAX = const(TICKS_PERIOD-1)
TICKS_HALFPERIOD = const(TICKS_PERIOD//2)

def ticks_diff(ticks1, ticks2):
    "Compute the signed difference between two ticks values, assuming that they are within 2**28 ticks"
    diff = (ticks1 - ticks2) & TICKS_MAX
    diff = ((diff + TICKS_HALFPERIOD) & TICKS_MAX) - TICKS_HALFPERIOD
    return diff

# Colors
BLOCK_PALETTE  = displayio.Palette(9)
BLOCK_PALETTE[0] = 0x000000 # BLACK
BLOCK_PALETTE[1] = 0x282828 # Gray 
BLOCK_PALETTE[2] = 0x008080 # CYAN
BLOCK_PALETTE[3] = 0x808000 
BLOCK_PALETTE[4] = 0x008000
BLOCK_PALETTE[5] = 0x600080
BLOCK_PALETTE[6] = 0x800000
BLOCK_PALETTE[7] = 0x804000
BLOCK_PALETTE[8] = 0x000080
BLOCK_COLORS = [2,3,4,5,6,7,8]


# Shapes
SHAPES = [
    # Straight
    [list(".#.."),
     list(".#.."),
     list(".#.."),
     list(".#..")],

    # O
    [list("...."),
     list(".##."),
     list(".##."),
     list("....")],

    # T
    [list(".#.."),
     list("###."),
     list("...."),
     list("....")],
    
    # J
    [list(".#.."),
     list(".#.."),
     list("##.."),
     list("....")],

    # L
    [list(".#.."),
     list(".#.."),
     list(".##."),
     list("....")],

    # S
    [list("...."),
     list(".##."),
     list("##.."),
     list("....")],

    # Z
    [list("...."),
     list(".##."),
     list("..##"),
     list("....")],
]

class Totremino:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = random.choice(BLOCK_COLORS)
    
    def __getitem__(self, item):
        return self.shape[item]

    @staticmethod
    def rotate(shape):
        return list(zip(*shape[::-1]))

class Totris:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.game_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.preview_screen = None
        self.game_screen = None
        self.game_score_area = None
        self.game_score = 0
        self.level_area = None
        self.level = 0
        self.falling_totremino = None
        self.next_totremino = None

    def is_valid_move(self, tot, x_delta, y_delta):
        for i, row in enumerate(tot.shape):
            for j, cell in enumerate(row):
                try:
                    new_x = j+tot.x+x_delta
                    if cell == "#" and ((self.game_grid[i+tot.y+y_delta][new_x] != 0) or new_x < 0):
                        return False
                except IndexError:
                    return False
        
        return True
    
    def new_tot(self):
        return Totremino(self.width//2, 0, random.choice(SHAPES))
    
    def clear_and_score(self):
        cleared = 0
        for i in range(len(self.game_grid)):
            if all(cell != 0 for cell in self.game_grid[i]):
                cleared += 1
                del self.game_grid[i]
                self.game_grid.insert(0, [0 for _ in range(self.width)])
        return cleared
    
    def lock_tot(self, tot):
        for i, row in enumerate(tot.shape):
            for j, cell in enumerate(row):
                if cell == "#":
                    self.game_grid[tot.y+i][tot.x+j] = tot.color

    def get_highscore(self):
        with open("/apps/totris/metadata.json", "r") as f:
            meta = json.load(f)
            try:
                nvm = json.loads(nvm_open(meta["app_name"]))
                return nvm["score"]
            except ValueError as e:
                return 0

    def single_player_start(self):
        epd_root = displayio.Group()

        if EPD_SMALL:
            img_path = "apps/totris/img/totris_small.bmp"
        else:
            img_path = "apps/totris/img/totris.bmp"
        bmp, palette = adafruit_imageload.load(img_path, bitmap=displayio.Bitmap,palette=displayio.Palette)
        palette[0] = 0xFFFFFF
        palette[1] = 0x000000
        epd_img = displayio.TileGrid(bmp, pixel_shader=palette)

        hs = self.get_highscore()
        
        score_label = center_text_x_plane(EPD, "High Score", y=82)
        hs_label = center_text_x_plane(EPD, f"{hs:04}", y=91)

        epd_root.append(epd_img)
        epd_root.append(score_label)
        epd_root.append(hs_label)
        EPD.root_group = epd_root
        EPD.refresh()

        start_label = Label(terminalio.FONT, text="Press S7 to play")
        start_label.anchor_point = (0.5, 0.5)
        start_label.anchored_position = (64, 16)

        lights_label = Label(terminalio.FONT, text="Press S6 to disable\n  flashing lights")
        lights_label.anchor_point = (0.5, 0.5)
        lights_label.anchored_position = (64, 56)

        if NP.brightness == 0:
            lt = "Lights are OFF"
            lc = 0xFFFF00
        else:
            lt = "Lights are ON"
            lc = 0x00FF00

        light_indicator = Label(terminalio.FONT, text=lt)
        light_indicator.anchor_point = (0.5, 0.5)
        light_indicator.anchored_position = (64, 75)
        light_indicator.color = lc

        exit_label = Label(terminalio.FONT, text="Press S4 to exit")
        exit_label.anchor_point = (0.5, 0.5)
        exit_label.anchored_position = (64, 112)

        root = displayio.Group()
        root.append(start_label)
        root.append(lights_label)
        root.append(light_indicator)
        root.append(exit_label)
        LCD.root_group = root

        while True:
            if a_pressed():
                return False
            elif c_pressed():
                if NP.brightness == 0:
                    NP.brightness = 0.1
                    light_indicator.color = 0x00FF00
                    light_indicator.text = "Lights are ON"
                else:
                    NP.brightness = 0
                    light_indicator.color = 0xFFFF00
                    light_indicator.text = "Lights are OFF"
            elif d_pressed():
                return True

            time.sleep(0.1)
    
    def multi_player_start(self):
        raise NotImplementedError

    def setup_game_screen(self):
        bg_palette = displayio.Palette(1)
        bg_palette[0] = 0x888888

        score_label_area = Label(terminalio.FONT, text ='Score:')
        score_label_area.anchor_point = (0.5,0.5)
        score_label_area.anchored_position = (105, 110)
        score_label_area.color = 0x000000

        self.game_score_area = Label(terminalio.FONT, text='0000')
        self.game_score_area.anchor_point = (0.5,0.5)
        self.game_score_area.anchored_position = (105, 120)
        self.game_score_area.color = 0x000000
        
        level_label_area = Label(terminalio.FONT, text="Level:")
        level_label_area.anchor_point = (0.5,0.5)
        level_label_area.anchored_position = (105, 75)
        level_label_area.color = 0x000000

        self.level_area = Label(terminalio.FONT, text='1')
        self.level_area.anchor_point = (0.5,0.5)
        self.level_area.anchored_position = (105, 85)
        self.level_area.color = 0x000000


        preview_label_area = Label(terminalio.FONT, text='Next')
        preview_label_area.anchor_point = (0.5, 0.5)
        preview_label_area.anchored_position = (105, 9)
        preview_label_area.color = 0x000000

        bg_bitmap = displayio.Bitmap(8,8,6)
        bg = displayio.Group(scale=16)
        bg.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0))

        self.game_screen = displayio.Bitmap(10, 20, 6)
        self.preview_screen = displayio.Bitmap(4, 4, 6)
        bricks = displayio.Group(scale=8)
        bricks.append(displayio.TileGrid(self.game_screen, pixel_shader=BLOCK_PALETTE, x=0, y=-4))
        bricks.append(displayio.TileGrid(self.preview_screen, pixel_shader=BLOCK_PALETTE, x=11, y=2))

        root = displayio.Group()
        root.append(bg)
        root.append(score_label_area)
        root.append(self.game_score_area)
        root.append(level_label_area)
        root.append(self.level_area)
        root.append(preview_label_area)
        root.append(bricks)
        LCD.root_group = root
    
    def game_loop(self):
        game_tick_time_ms = 5 # Game speed
        fall_tick_time_ms = 500 # Initial speed for totreminos to decend
        fall_tick_time_ms_min = 100 # Minimum game speed
        btn_wait_time_ms = 100 # Time to wait for new button events

        rot_debounce = False
        self.level = 1
        self.game_score = 0
        total_cleared = 0

        tick = ticks_ms()
        fall_last_tick = tick
        btn_last_tick = tick
        while True:
            nt = ticks_ms()
            if ticks_diff(nt, tick) < game_tick_time_ms:
                continue
            
            tick = nt
            
            #Check for scoring lines
            cleared = self.clear_and_score()
            total_cleared += cleared
            if cleared:
                self.game_score += cleared ** 2
                self.update_score()

                self.level = (total_cleared // 10) + 1  
                self.update_level()  

                self.blinka(cleared)
            
            if ticks_diff(tick, btn_last_tick) >= btn_wait_time_ms:
                btn_last_tick = tick
                if a_pressed():
                    if self.is_valid_move(self.falling_totremino, -1, 0):
                        self.falling_totremino.x -= 1
                        self.update_game_screen()
                if b_pressed():
                    if self.is_valid_move(self.falling_totremino, 1, 0):
                        self.falling_totremino.x += 1
                        self.update_game_screen()
                if c_pressed():
                    if self.is_valid_move(self.falling_totremino, 0, 1):
                        self.falling_totremino.y += 1
                        self.update_game_screen()
                if d_pressed():
                    if not rot_debounce:
                        rot_debounce = True
                        cur_shape = self.falling_totremino.shape
                        self.falling_totremino.shape = self.falling_totremino.rotate(cur_shape)
                        if self.is_valid_move(self.falling_totremino, 0, 0):
                            self.update_game_screen()
                        else:
                            self.falling_totremino.shape = cur_shape
                else:
                    rot_debounce = False

            if ticks_diff(tick, fall_last_tick) >= int(max(fall_tick_time_ms * (1-((self.level - 1) * 0.1)), fall_tick_time_ms_min)):
                if self.is_valid_move(self.falling_totremino, 0, 1):
                    self.falling_totremino.y += 1
                else:
                    self.lock_tot(self.falling_totremino)
                    self.falling_totremino = self.next_totremino
                    self.next_totremino = self.new_tot()
                    self.update_game_preview()
                    if not self.is_valid_move(self.falling_totremino, 0, 0):
                        break
                fall_last_tick = tick
                self.update_game_screen()
    
    def update_game_preview(self):
        for y in range(4):
            for x in range(4):
                if self.next_totremino[y][x] == '#':
                    self.preview_screen[x, y] = self.next_totremino.color
                else:
                    self.preview_screen[x, y] = 0

    def update_game_screen(self):
        for y, row in enumerate(self.game_grid):
            for x, cell in enumerate(row):
                self.game_screen[x, y] = cell
        for y in range(4):
            for x in range(4):
                if self.falling_totremino[y][x] == '#':
                    self.game_screen[x+self.falling_totremino.x, y+self.falling_totremino.y] = self.falling_totremino.color
    
    def update_score(self):
        self.game_score_area.text = f"{self.game_score:04d}"

    def update_level(self):
        self.level_area.text = f"{self.level}"
    
    def blinka(self, cleared):
        for _ in range(cleared):
            NP.fill(random.choice(BLOCK_PALETTE))
            time.sleep(0.1)
            NP.fill(0x000000)
            time.sleep(0.1)

    def single_player_game(self):
        while self.single_player_start():
            self.setup_game_screen()
            self.falling_totremino = self.new_tot()
            self.next_totremino = self.new_tot()
            self.update_game_preview()
            self.update_game_screen()

            self.game_loop()
            game_over_area = Label(terminalio.FONT, text='    GAME OVER     ')
            game_over_area.anchor_point = (0.5, 0.5)
            game_over_area.anchored_position = (64, 64)
            game_over_area.color = 0xc70000
            game_over_area.background_color = 0x000000
            LCD.root_group.append(game_over_area)
            time.sleep(3)
            post_to_leaderboard(self.game_score)

    def multi_player_game(self):
        raise NotImplementedError

    def run(self):
        self.single_player_game()