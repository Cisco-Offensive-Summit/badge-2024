import board
from neopixel import NeoPixel
from neopixel import RGB
from badge.constants import OFF

ORDER = RGB
DEFAULT_BRIGHTNESS = 0.05
NP = NeoPixel(pin=board.NEOPIXEL, n=4, brightness=DEFAULT_BRIGHTNESS, pixel_order=ORDER, auto_write=True)

def set_neopixel(name: str, val):
    d = {"a": 0, "b": 1, "c": 2, "d": 3}
    NP[d[name.lower()]] = val

def set_neopixel_brightness(name: str, val, brightness):
    d = {"a": 0, "b": 1, "c": 2, "d": 3}
    NP[d[name.lower()]]= val
    NP[d[name.lower()]].brightness = brightness

def set_neopixels(a=OFF, b=OFF, c=OFF, d=OFF):
    global NP    

    NP[0] = a
    NP[1] = b
    NP[2] = c
    NP[3] = d

def neopixels_off():
    set_neopixels(0, 0, 0, 0)

def neopixel_reinit():
    global NP
    NP.deinit()
    NP = NeoPixel(pin=board.NEOPIXEL, n=4, brightness=0.05, pixel_order=ORDER, auto_write=True)
    return NP