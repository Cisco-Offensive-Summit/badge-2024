import board
from neopixel import NeoPixel
from neopixel import RGB

ORDER = RGB
NP = NeoPixel(pin=board.NEOPIXEL, n=4, brightness=0.05, pixel_order=ORDER, auto_write=True)
