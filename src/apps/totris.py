import board, random, time, keypad
import displayio, digitalio, terminalio
from microcontroller import nvm 

from app import App

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

class TotrisApp(App):
    def __init__(self, lcd: ST7735R, epd: EPD):
        super().__init__(lcd, epd)
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)

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
        palette = displayio.Palette(6)
        palette[0] = 0x111111
        palette[1] = 0xaa0099
        palette[2] = 0x22aa00
        palette[3] = 0xee00bb
        palette[4] = 0xbbee00
        palette[5] = 0xbb00ee

        text_palette = displayio.Palette(2)
        text_palette[0] = 0x000000
        text_palette[1] = 0xffeedd

        screen = displayio.Bitmap(32, 32, 6)
        bricks = displayio.Group(scale=4)
        bricks.append(displayio.TileGrid(screen, pixel_shader=palette, x=0, y=-8))


        w, h = terminalio.FONT.get_bounding_box()
        text_grid = displayio.TileGrid(terminalio.FONT.bitmap,
            tile_width=w, tile_height=h, pixel_shader=text_palette, width=21, height=8)
        text_grid.x = 0
        text_grid.y = 0
        text = terminalio.Terminal(text_grid, terminalio.FONT)
        text.write("  Press S7 to play\n\n\n\r  Press S4 to exit")

        root = displayio.Group()
        root.append(text_grid)
        self.lcd.show(root)

        self.buttons.events.clear()
        while True:
            event = self.buttons.events.get()
            if event:
                if event.key_number == 3:
                    return False
                else:
                    return True

    def _start_game(self):
        palette = displayio.Palette(6)
        palette[0] = 0x000000
        palette[1] = 0xaa0099
        palette[2] = 0x22aa00
        palette[3] = 0xee00bb
        palette[4] = 0xbbee00
        palette[5] = 0xbb00ee
        text_palette = displayio.Palette(2)
        text_palette[0] = 0x111111
        text_palette[1] = 0xffeedd
        game_over_palette = displayio.Palette(2)
        game_over_palette[0] = 0x111111
        game_over_palette[1] = 0xc70000

        w, h = terminalio.FONT.get_bounding_box()
        text_grid = displayio.TileGrid(terminalio.FONT.bitmap,
            tile_width=w, tile_height=h, pixel_shader=text_palette, width=4, height=2)
        text_grid.x = 96
        text_grid.y = 48
        text = terminalio.Terminal(text_grid, terminalio.FONT)

        game_over_grid = displayio.TileGrid(terminalio.FONT.bitmap, 
            tile_width=w, tile_height=h, pixel_shader=game_over_palette, width=9, height=2)
        game_over_grid.x = 32
        game_over_grid.y = 60
        game_over_text = terminalio.Terminal(game_over_grid, terminalio.FONT)
        game_over_text.write("GAME OVER")

        screen = displayio.Bitmap(10, 20, 6)
        preview = displayio.Bitmap(4, 4, 6)
        bricks = displayio.Group(scale=8)
        bricks.append(displayio.TileGrid(screen, pixel_shader=palette, x=0, y=-4))
        bricks.append(displayio.TileGrid(preview, pixel_shader=palette, x=12, y=0))
        root = displayio.Group()
        root.append(bricks)
        root.append(text_grid)
        root[0] = displayio.Group()
        root[0] = bricks
        self.lcd.show(root)

        brick = None
        score = 0
        next_brick = Brick(random.randint(0, 4))
        tick = time.monotonic()
        while True:
            if brick is None:
                text.write(f"\r\n\r\n{score:04d}")
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
                        for yy in range(y, 0, -1):
                            for x in range(screen.width):
                                screen[x, yy] = screen[x, yy - 1]
                brick = None
            else:
                brick.y += 1
                brick.draw(screen)

        root.append(game_over_grid)
        if score > self._get_high_score():
            b = score.to_bytes(4, "big", signed=False)
            nvm[0:4] = b

        time.sleep(4)