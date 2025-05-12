"""
Leet Badge by Paul Giblock

A more leeter ID badge.  This makes it easy to draw an image of your choosing to the e-ink
and LCD screens simultaneously.  In addition, you get scrolling rainbow LEDs on top.  This
is intentionally simple and noninteractive.

To use, simply copy the image you want displayed on the e-ink display to
'img/my_epd_logo.bmp' and an image for the LCD to 'img/my_lcd_logo.bmp' prior
to running.

Hint: imagemagick makes the bit depth and format conversion easy, but it is
probably best to start with images of the correct dimensions:

2025 Small Screen Badge:    
    magick -depth 1 -compress none -resize 128x96\!  epd_logo.png /Volumes/CIRCUITPY/img/my_epd_logo.png
    magick -depth 8 -compress none -resize 128x128\! lcd_logo.png /Volumes/CIRCUITPY/img/my_lcd_logo.png

2024 Large Screen Badge:    
    magick -depth 1 -compress none -resize 200x96\!  epd_logo.png /Volumes/CIRCUITPY/img/my_epd_logo.png
    magick -depth 8 -compress none -resize 128x128\! lcd_logo.png /Volumes/CIRCUITPY/img/my_lcd_logo.png
"""

import asyncio, supervisor, time

from badge.constants import EPD_SMALL
from badge.fileops import is_file
from badge.neopixels import set_neopixels, neopixels_off
from badge.screens import LCD, EPD, clear_screen, epd_print_exception
from displayio import Group, OnDiskBitmap, Palette, TileGrid

EPD_CUSTOM_IMAGE = '/img/my_epd_logo.bmp'
EPD_LARGE_IMAGE = '/img/epd_logo.bmp'
EPD_SMALL_IMAGE = '/apps/leetbadge/img/epd_logo_small.bmp'

LCD_CUSTOM_IMAGE = '/img/my_lcd_logo.bmp'

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
    path = LCD_CUSTOM_IMAGE
    if is_file(path):
        clear_screen(LCD)
        group = Group()
        bitmap = OnDiskBitmap(path)
        tile_grid = TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        group.append(tile_grid)
        LCD.root_group = group
        return

    #       123456789012345678901")
    print("LeetBadge - pgiblock")
    print("="*21)
    print("For custom art add:")
    print(EPD_CUSTOM_IMAGE)
    print(LCD_CUSTOM_IMAGE)


def draw_epd_screen():
    path = EPD_CUSTOM_IMAGE
    if not is_file(path):
        if EPD_SMALL:
            path = EPD_SMALL_IMAGE
        else:
            path = EPD_LARGE_IMAGE

    if is_file(path):
        bitmap = OnDiskBitmap(path)
        tile_grid = TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        group = Group()
        group.append(tile_grid)
        EPD.root_group = group
        EPD.refresh()
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
    EPD.refresh()
    time.sleep(60)

supervisor.reload()
