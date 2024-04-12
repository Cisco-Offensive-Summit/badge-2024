import board
from neopixel import NeoPixel
from neopixel import RGB
import adafruit_led_animation.color as color
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.helper import PixelSubset
from badge.colors import OFF

ORDER = RGB
NP = NeoPixel(pin=board.NEOPIXEL, n=4, brightness=0.05, pixel_order=ORDER, auto_write=True)

NEO_A = PixelSubset(NP, 0, 1)
NEO_B = PixelSubset(NP, 1, 2)
NEO_C = PixelSubset(NP, 2, 3)
NEO_D = PixelSubset(NP, 3, 4)


def set_neopixels(a=OFF, b=OFF, c=OFF, d=OFF):
    global NP    

    NP[0] = a
    NP[1] = b
    NP[2] = c
    NP[3] = d


def neopixels_off():
    set_neopixels(0, 0, 0, 0)
    NP.show()


def set_neopixel(name: str, val):
    d = {"a": 0, "b": 1, "c": 2, "d": 3}
    NP[d[name.lower()]] = val
    NP.show()


def animate(pixel_obj=NP):
    blink = Blink(pixel_obj, 0.1, color.PURPLE)
    for _ in range(5000):
        blink.animate()
    pixel_obj.fill((0, 0, 0))
    pixel_obj.show()


def animate_comet(c=color.BLUE):
    comet = Comet(NP, 0.2, color=c, tail_length=3)
    for _ in range(100000):
        comet.animate()


def anim_rainbow_chase():
    rc = RainbowChase(NP, speed=0.1, size=3, spacing=5, step=32)
    for _ in range(100000):
        rc.animate()


def anim_rainbow_comet():
    rc = RainbowComet(NP, speed=0.1, bounce=True)
    while True:
        rc.animate()

set_neopixels()
