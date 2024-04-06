import board, time, keypad
import displayio, digitalio, terminalio
from microcontroller import nvm

from pdepd import EPD
from adafruit_st7735r import ST7735R

class ScheduleApp:
    def __init__(self, lcd: ST7735R, epd: EPD):
        self.lcd = lcd
        self.epd = epd
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)

    def __del__(self) -> None:
        pass

    # Main entry
    def run():
        pass

