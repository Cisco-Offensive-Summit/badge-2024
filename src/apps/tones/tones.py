import board, random, time, keypad
import displayio, digitalio, terminalio
from adafruit_display_text import label
from microcontroller import nvm

from badge.neopixels import NP

class TonesApp:
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

        self.epd.image("img/tones.bmp")
        self.epd.text("Waveform", 5, 78, 1)
        self.epd.text("S4", 14, 87, 1)
        self.epd.text("Up", 80, 78, 1)
        self.epd.text("S5", 80, 87, 1)
        self.epd.text("Down", 120, 78, 1)
        self.epd.text("S6", 124, 87, 1)
        self.epd.text("Play", 173, 78, 1)
        self.epd.text("S7", 178, 87, 1)
        self.epd.draw()

        while self._init_screen():
            self._play_tones()

    def _init_screen(self):

        cont_label = label.Label(terminalio.FONT, text="Press S7 to continue")
        cont_label.anchor_point = (0.5, 0.5)
        cont_label.anchored_position = (64, 16)

        dac_label = label.Label(terminalio.FONT, text="Press S6 to toggle\n  DAC output:")
        dac_label.anchor_point = (0.5, 0.5)
        dac_label.anchored_position = (64, 56)

        if NP.brightness == 0:
            lt = "DAC output is OFF"
            lc = 0xFFFF00
        else:
            lt = "DAC output is ON"
            lc = 0x00FF00

        dac_status = label.Label(terminalio.FONT, text=lt)
        dac_status.anchor_point = (0.5, 0.5)
        dac_status.anchored_position = (64, 75)
        dac_status.color = lc

        exit_label = label.Label(terminalio.FONT, text="Press S4 to exit")
        exit_label.anchor_point = (0.5, 0.5)
        exit_label.anchored_position = (64, 112)

        root = displayio.Group()
        root.append(cont_label)
        root.append(dac_label)
        root.append(dac_status)
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
                        dac_status.color = 0x00FF00
                        dac_status.text = "DAC output is ON"
                    else:
                        NP.brightness = 0
                        dac_status.color = 0xFFFF00
                        dac_status.text = "DAC output is OFF"

                if event.key_number == 3:
                    return False
                else:
                    pass

    def _play_tones(self):
        TONES       = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
        FREQUENCIES = [262, 294, 330, 349, 392, 440, 494, 523]
        WAVEFORMS   = ["sine", "square", "triangle", "saw", "supersaw"]
        MINTONE     = 0
        MAXTONE     = 7
        TONE        = 5
        MINFREQ     = 0
        MAXFREQ     = 7
        FREQ        = 5
        MINWAVE     = 0
        MAXWAVE     = 4
        WAVE        = 0


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


        waveform_area = label.Label(terminalio.FONT, text ='Waveform: ')
        waveform_area.anchor_point = (0.5,0.5)
        waveform_area.anchored_position = (1, 1)
        waveform_area.color = 0x000000

        note_area = label.Label(terminalio.FONT, text='Note (Frequency): ')
        note_area.anchor_point = (0.5, 0.5)
        note_area.anchored_position = (1, 145)
        note_area.color = 0xc70000
        note_area.background_color = 0x000000

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
        root.append(waveform_area)
        root.append(note_area)
        self.lcd.show(root)

        # brick = None
        # score = 0
        # next_brick = Brick(random.randint(0, 4))
        # tick = time.monotonic()
        # while True:
        #     if brick is None:
        #         score_area.text = (f"{score:04d}")
        #         next_brick.draw(preview, 0)
        #         brick = next_brick
        #         brick.x = screen.width // 2
        #         next_brick = Brick(random.randint(0, 4))
        #         next_brick.draw(preview)
        #         if brick.hit(screen, 0, 0):
        #             break
        #     tick += 0.5
        #     pressed = 0
        #     event = keypad.Event()
        #     while True:
        #         self.lcd.refresh()
        #         time.sleep(0.075)
        #         if tick <= time.monotonic():
        #             break
        #         brick.draw(screen, 0)
        #         while self.buttons.events:
        #             self.buttons.events.get_into(event)
        #             if event.pressed:
        #                 pressed |= 1 << event.key_number
        #             else:
        #                 pressed &= ~(1 << event.key_number)
        #         if pressed & 0x08 and not brick.hit(screen, -1, 0):
        #             brick.x -= 1
        #         if pressed & 0x04 and not brick.hit(screen, 1, 0):
        #             brick.x += 1
        #         if pressed & 0x02 and not brick.hit(screen, 0, 1):
        #             brick.y += 1
        #         if pressed & 0x01 and not brick.hit(screen, 0, 0, 1) and not debounce:
        #             brick.rotation = (brick.rotation + 1) % 4
        #             debounce = True
        #         if not pressed:
        #             debounce = False
        #         brick.draw(screen)
        #     brick.draw(screen, 0)
        #     if brick.hit(screen, 0, 1):
        #         brick.draw(screen)
        #         combo = 0
        #         for y in range(screen.height):
        #             for x in range(screen.width):
        #                 if not screen[x, y]:
        #                     break
        #             else:
        #                 combo += 1
        #                 score += combo

        #                 for _ in range(2):
        #                     NP.fill(palette[random.randint(1,5)])
        #                     time.sleep(0.1)
        #                     NP.fill(0x000000)
        #                     time.sleep(0.1)

        #                 for yy in range(y, 0, -1):
        #                     for x in range(screen.width):
        #                         screen[x, yy] = screen[x, yy - 1]
        #         brick = None
        #     else:
        #         brick.y += 1
        #         brick.draw(screen)

        # root.append(game_over_area)

        time.sleep(4)
