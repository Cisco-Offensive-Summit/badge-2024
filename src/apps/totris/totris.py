import board, random, time, keypad
import displayio, digitalio, terminalio
from adafruit_display_text import label
from microcontroller import nvm 

from badge.neopixels import NP

class Brick:
    BRICKS = b'ftqr\xf0'
    ROTATIONS = [
        (1, 0, 0, 1, -1, -1),
        (0, 1, -1, 0, -1, 0),
        (-1, 0, 0, -1, -2, 0),
        (0, -1, 1, 0, -2, -1),
    ]

    def __init__(self, kind):
        self.x = 1
        self.y = 2
        self.color = kind % 5 + 1
        self.rotation = 0
        self.kind = kind

    def draw(self, image, color=None):
        if color is None:
            color = self.color
        data = self.BRICKS[self.kind]
        rot = self.ROTATIONS[self.rotation]
        mask = 0x01
        for y in range(2):
            y += rot[5]
            for x in range(4):
                x += rot[4]
                if data & mask:
                    try:
                        image[self.x + x * rot[0] + y * rot[1],
                              self.y + x * rot[2] + y * rot[3]] = color
                    except IndexError:
                        pass
                mask <<= 1

    def hit(self, image, dx=0, dy=0, dr=0):
        data = self.BRICKS[self.kind]
        rot = self.ROTATIONS[(self.rotation + dr) % 4]
        mask = 0x01
        for y in range(2):
            y += rot[5]
            for x in range(4):
                x += rot[4]
                if data & mask:
                    try:
                        if image[self.x + dx + x * rot[0] + y * rot[1],
                                 self.y + dy + x * rot[2] + y * rot[3]]:
                            return True
                    except IndexError:
                        return True
                mask <<= 1
        return False

class TotrisApp:
    def __init__(self, lcd: ST7735R, epd: EPD):
        self.lcd = lcd
        self.epd = epd
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)
        NP.brightness = 0.1

    def __del__(self):
        self.buttons.deinit()
    
    def setup(self):
        pass

    def run(self):
        hs = self._get_high_score()

        self.epd.image("img/totris.bmp")
        self.epd.text("High Score", 70, 78, 1)
        self.epd.text(f"{hs:04}", 88, 87, 1)
        self.epd.draw()

        while self._start_screen():
            self._start_game()
            if self._get_high_score() > hs:
                self.epd.text(f"{hs:04}", 88, 87, 0)
                hs = self._get_high_score()
                self.epd.text(f"{hs:04}", 88, 87, 1)
                self.epd.update()

    def _get_high_score(self):
        b = nvm[0:4]
        return int.from_bytes(b, "big", signed=False)

    def _start_screen(self):

        start_label = label.Label(terminalio.FONT, text="Press S7 to play")
        start_label.anchor_point = (0.5, 0.5)
        start_label.anchored_position = (64, 16)

        lights_label = label.Label(terminalio.FONT, text="Press S6 to disable\n  flashing lights")
        lights_label.anchor_point = (0.5, 0.5)
        lights_label.anchored_position = (64, 56)

        if NP.brightness == 0:
            lt = "Lights are OFF"
            lc = 0xFFFF00
        else:
            lt = "Lights are ON"
            lc = 0x00FF00

        light_indicator = label.Label(terminalio.FONT, text=lt)
        light_indicator.anchor_point = (0.5, 0.5)
        light_indicator.anchored_position = (64, 75)
        light_indicator.color = lc

        exit_label = label.Label(terminalio.FONT, text="Press S4 to exit")
        exit_label.anchor_point = (0.5, 0.5)
        exit_label.anchored_position = (64, 112)

        root = displayio.Group()
        root.append(start_label)
        root.append(lights_label)
        root.append(light_indicator)
        root.append(exit_label)
        self.lcd.show(root)

        self.buttons.events.clear()
        while True:
            event = self.buttons.events.get()
            if event and event.pressed:
                if event.key_number == 0:
                    return True
                if event.key_number == 1:
                    if NP.brightness == 0:
                        NP.brightness = 0.1
                        light_indicator.color = 0x00FF00
                        light_indicator.text = "Lights are ON"
                    else:
                        NP.brightness = 0
                        light_indicator.color = 0xFFFF00
                        light_indicator.text = "Lights are OFF"

                if event.key_number == 3:
                    return False
                else:
                    pass

    def _start_game(self):
        palette = displayio.Palette(6)
        palette[0] = 0x000000
        palette[1] = 0xaa0099
        palette[2] = 0x22aa00
        palette[3] = 0xee00bb
        palette[4] = 0xbbee00
        palette[5] = 0xbb00ee
        bg_palette = displayio.Palette(2)
        bg_palette[0] = 0x888888
        bg_palette[1] = 0x000000


        score_label_area = label.Label(terminalio.FONT, text ='Score:')
        score_label_area.anchor_point = (0.5,0.5)
        score_label_area.anchored_position = (105, 75)
        score_label_area.color = 0x000000

        score_area = label.Label(terminalio.FONT, text='0000')
        score_area.anchor_point = (0.5,0.5)
        score_area.anchored_position = (105, 90)
        score_area.color = 0x000000

        game_over_area = label.Label(terminalio.FONT, text='    GAME OVER     ')
        game_over_area.anchor_point = (0.5, 0.5)
        game_over_area.anchored_position = (64, 64)
        game_over_area.color = 0xc70000
        game_over_area.background_color = 0x000000

        preview_label_area = label.Label(terminalio.FONT, text='Next')
        preview_label_area.anchor_point = (0.5, 0.5)
        preview_label_area.anchored_position = (105, 9)
        preview_label_area.color = 0x000000

        screen = displayio.Bitmap(10, 20, 6)
        preview = displayio.Bitmap(4, 4, 6)
        bricks = displayio.Group(scale=8)
        bricks.append(displayio.TileGrid(screen, pixel_shader=palette, x=0, y=-4))
        bricks.append(displayio.TileGrid(preview, pixel_shader=palette, x=11, y=2))
        bg_bitmap = displayio.Bitmap(8, 8, 6)
        background = displayio.Group(scale=16)
        background.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0))

        root = displayio.Group()
        root.append(background)
        root.append(score_area)
        root.append(score_label_area)
        root.append(preview_label_area)
        root.append(bricks)
        self.lcd.show(root)

        brick = None
        score = 0
        next_brick = Brick(random.randint(0, 4))
        tick = time.monotonic()
        while True:
            if brick is None:
                score_area.text = (f"{score:04d}")
                next_brick.draw(preview, 0)
                brick = next_brick
                brick.x = screen.width // 2
                next_brick = Brick(random.randint(0, 4))
                next_brick.draw(preview)
                if brick.hit(screen, 0, 0):
                    break
            tick += 0.5
            pressed = 0
            event = keypad.Event()
            while True:
                self.lcd.refresh()
                time.sleep(0.075)
                if tick <= time.monotonic():
                    break
                brick.draw(screen, 0)
                while self.buttons.events:
                    self.buttons.events.get_into(event)
                    if event.pressed:
                        pressed |= 1 << event.key_number
                    else:
                        pressed &= ~(1 << event.key_number)
                if pressed & 0x08 and not brick.hit(screen, -1, 0):
                    brick.x -= 1
                if pressed & 0x04 and not brick.hit(screen, 1, 0):
                    brick.x += 1
                if pressed & 0x02 and not brick.hit(screen, 0, 1):
                    brick.y += 1
                if pressed & 0x01 and not brick.hit(screen, 0, 0, 1) and not debounce:
                    brick.rotation = (brick.rotation + 1) % 4
                    debounce = True
                if not pressed:
                    debounce = False
                brick.draw(screen)
            brick.draw(screen, 0)
            if brick.hit(screen, 0, 1):
                brick.draw(screen)
                combo = 0
                for y in range(screen.height):
                    for x in range(screen.width):
                        if not screen[x, y]:
                            break
                    else:
                        combo += 1
                        score += combo

                        for _ in range(2):
                            NP.fill(palette[random.randint(1,5)])
                            time.sleep(0.1)
                            NP.fill(0x000000)
                            time.sleep(0.1)

                        for yy in range(y, 0, -1):
                            for x in range(screen.width):
                                screen[x, yy] = screen[x, yy - 1]
                brick = None
            else:
                brick.y += 1
                brick.draw(screen)

        root.append(game_over_area)
        if score > self._get_high_score():
            b = score.to_bytes(4, "big", signed=False)
            nvm[0:4] = b

        time.sleep(4)