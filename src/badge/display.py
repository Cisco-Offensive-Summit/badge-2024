import asyncio
import random
import time

import board
import displayio
from adafruit_magtag.magtag import Graphics

from .colors import DARKGRAY, LIGHTGRAY, WHITE
from .magtag import magtag


def refresh():
    refreshed = False
    while not refreshed:
        try:
            board.DISPLAY.refresh()
            refreshed = True
        except RuntimeError:
            time.sleep(board.DISPLAY.time_to_refresh + 0.1)
    return


def set_background(color=WHITE):
    magtag.set_background(color)
    magtag.refresh()


def splash():
    set_background("/img/splash.bmp")


async def a_splash():
    splash()
    await asyncio.sleep(0)

dimensions = (296, 128)
graphics = Graphics(auto_refresh=False)
display = graphics.display
main_group = displayio.Group()


def rand_point():
    return (random.randrange(dimensions[0]), random.randrange(dimensions[1]))


def rand_rect():
    return rand_point() + rand_point()


# def show_rect(interval=2.0):
#     start_time = time.monotonic_ns()
#     print(f"[+] show_rect:{start_time}")
#     rect = Rect(*rand_rect(), fill=random.choice([BLACK, LIGHTGRAY, DARKGRAY]))
#     group.append(rect)
#     display.show(group)
#     end_time = time.monotonic_ns()
#     print(f"[-] show_rect:{end_time},elapsed={end_time-start_time}")


# async def show_rects():
#     # interval = 0 # ms
#     while True:
#         show_rect()
#         print(f"[+] show_rects:time_to_refresh={display.time_to_refresh}")
#         await asyncio.sleep(display.time_to_refresh + 0.1)
#         try:
#             display.refresh()
#         except RuntimeError as e:
#             print(f"[E] show_rects:{e}")
#             print(f"[-] show_rects:time_to_refresh={display.time_to_refresh}")
#             await asyncio.sleep(display.time_to_refresh + 0.1)
#         await asyncio.sleep(0.05)


async def a_refresh(group_obj):
    while True:
        await asyncio.sleep(display.time_to_refresh + 0.1)
        try:
            display.refresh()
        except RuntimeError:
            await asyncio.sleep(display.time_to_refresh + 0.1)
        await asyncio.sleep(0.05)


def show_bmpz(bmpz_filename):
    import io
    import zlib

    import adafruit_imageload
    import board
    import displayio

    bmpz = zlib.decompress(open(bmpz_filename).read())
    bmpz_io = io.BytesIO(bmpz)

    maingroup = displayio.Group()
    bitmap, palette = adafruit_imageload.load(bmpz_io)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    maingroup.append(tile_grid)

    board.DISPLAY.show(maingroup)
    board.DISPLAY.refresh()
