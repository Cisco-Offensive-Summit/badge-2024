"""
A more leeter ID badge.  This makes it easy to draw an image of your choosing to the e-ink
and LCD screens simultaneously.  In addition, you get scrolling rainbow LEDs on top.  This
is intentionally simple and noninteractive.

To use, simply copy the image you want displayed on the e-ink display to
'img/my_epd_logo.bmp' and an image for the LCD to 'img/my_lcd_logo.bmp' prior
to running.

Hint: imagemagick makes the bit depth and format conversion easy, but it is
probably best to start with images of the correct dimensions:

    convert -depth 1 -resize 200x96\!  epd_logo.png /Volumes/CIRCUITPY/img/my_epd_logo.png
    convert -depth 8 -resize 128x128\! lcd_logo.png /Volumes/CIRCUITPY/img/my_lcd_logo.png
"""

import adafruit_imageload
import asyncio, supervisor, time
from badge.fileops import is_file
from badge.neopixels import set_neopixels, neopixels_off
from badge.screens import LCD, EPD, clear_lcd_screen, epd_print_exception
from displayio import Group, Bitmap, Palette, TileGrid

IMG_DIR = '/img'

EPD_IMAGES = ['my_epd_logo.bmp', 'epd_logo.bmp']
LCD_IMAGES = ['my_lcd_logo.bmp']

ONE_THIRD = 1.0 / 3.0
ONE_SIXTH = 1.0 / 6.0
TWO_THIRD = 2.0 / 3.0


def hls_to_rgb(hue, light, sat):
    if sat == 0.0:
        return light, light, light
    if light <= 0.5:
        chroma2 = light * (1.0 + sat)
    else:
        chroma2 = light + sat - (light * sat)
    chroma1 = 2.0 * light - chroma2
    return (
        int(_v(chroma1, chroma2, hue + ONE_THIRD) * 255),
        int(_v(chroma1, chroma2, hue) * 255),
        int(_v(chroma1, chroma2, hue - ONE_THIRD) * 255),
    )


def _v(chroma1, chroma2, hue):
    hue = hue % 1.0
    if hue < ONE_SIXTH:
        return chroma1 + (chroma2 - chroma1) * hue * 6.0
    if hue < 0.5:
        return chroma2
    if hue < TWO_THIRD:
        return chroma1 + (chroma2 - chroma1) * (TWO_THIRD - hue) * 6.0
    return chroma1


def make_color(h):
    r, g, b = hls_to_rgb(h, 0.5, 1.0)
    return (r << 16) | (g << 8) | (b)


def draw_lcd_screen():
    for fn in LCD_IMAGES:
        path = f"{IMG_DIR}/{fn}"
        if is_file(path):
            clear_lcd_screen(LCD.root_group)
            group = Group()  
            bitmap, palette = adafruit_imageload.load(path, bitmap=Bitmap, palette=Palette)
            tile_grid = TileGrid(bitmap, pixel_shader=palette)
            group.append(tile_grid)
            LCD.root_group = group


def draw_epd_screen():
    for fn in EPD_IMAGES:
        path = f"{IMG_DIR}/{fn}"
        if is_file(path):
            EPD.fill(0)
            EPD.image(path)
            EPD.draw()
            return


async def init_screens():
    draw_lcd_screen()
    draw_epd_screen()


async def rainbow_loop():
    offsets = (0.0, 0.075, 0.150, 0.225)
    hue = 0.0
    while True:
        colors = tuple(make_color((hue+offset) % 1.0) for offset in offsets)
        set_neopixels(*colors)

        hue += 0.01
        if hue > 1.0:
            hue %= 1.0
        
        await asyncio.sleep(0.05)


async def main():
    # Kinda silly as we nuked all the other coroutines, but you can add your own tasks here
    tasks = [asyncio.create_task(t) for t in (init_screens(), rainbow_loop())]
    await asyncio.gather(*tasks)


####

supervisor.runtime.autoreload = False
try:
    asyncio.run(main())
except Exception as e:
    epd_print_exception(e)
    EPD.draw()
    time.sleep(60)

supervisor.reload()
