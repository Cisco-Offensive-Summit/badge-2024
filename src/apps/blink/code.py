import asyncio
import os
import sys
import board
import supervisor
from adafruit_display_text.label import Label
from displayio import Bitmap
from displayio import Group
from displayio import Palette
from displayio import TileGrid
from terminalio import FONT

import badge.buttons
import badge.events as evt
from badge.constants import BLACK
from badge.constants import BB_HEIGHT
from badge.constants import BB_WIDTH
from badge.events import on
from badge.neopixels import set_neopixels
from badge.neopixels import set_neopixel
from badge.screens import EPD
from badge.screens import epd_print_exception
from badge.screens import round_button
from badge.screens import center_text_x_plane

Curcolor = 0
Pattern = [0]
Heldcount = 0
@on(evt.BTN_A_PRESSED)
def a_pressed(event):
    global Curcolor
    global Heldcount
    Curcolor |= 255 << 16
    Heldcount += 1

@on(evt.BTN_B_PRESSED)
def b_pressed(event):
    global Curcolor
    global Heldcount
    Curcolor |= 255 << 8
    Heldcount += 1

@on(evt.BTN_C_PRESSED)
def c_pressed(event):
    global Curcolor
    global Heldcount
    Curcolor |= 255
    Heldcount += 1

@on(evt.BTN_D_PRESSED)
def d_pressed(event):
    global Curcolor
    global Heldcount
    Curcolor = 0
    Heldcount += 1

@on(evt.BTN_A_RELEASED)
def a_released(event):
    global Curcolor
    update_color(Curcolor)

@on(evt.BTN_B_RELEASED)
def b_released(event):
    global Curcolor
    update_color(Curcolor)

@on(evt.BTN_C_RELEASED)
def c_released(event):
    global Curcolor
    update_color(Curcolor)

@on(evt.BTN_D_RELEASED)
def d_released(event):
    global Curcolor
    update_color(Curcolor)

def update_color(color):
    global Curcolor
    global Pattern
    global Heldcount
    Heldcount -= 1
    if (Heldcount == 0):
        Pattern.append(color)
        Curcolor = 0


def run():
    asyncio.run(main())

def text(text, scale=1, y=0):
    lb = center_text_x_plane(EPD, text, scale=scale, y=y)
    EPD.root_group.append(lb)

def background():
    group = Group()
    background = Bitmap(EPD.width, EPD.height, 1)
    palette1 = Palette(1)
    palette1[0] = BLACK
    tile_grid1 = TileGrid(background, pixel_shader=palette1)
    group.append(tile_grid1)
    EPD.root_group = group


def button_row(x, y, a_txt=None, b_txt=None, c_txt=None, d_txt=None):
    radius = 5
    splash = Group()

    lb_blue = Label (font=FONT, text=c_txt)
    lb_none = Label (font=FONT, text=d_txt)
    lb_red = Label (font=FONT, text=a_txt)
    lb_green = Label (font=FONT, text=b_txt)

    x_1 = 2 + radius
    x_2 = EPD.width - 2 - lb_none.bounding_box[BB_WIDTH] - radius
    y_1 = EPD.height - 2 - radius - (lb_none.bounding_box[BB_HEIGHT]//2)
    y_2 = EPD.height - 4 - (radius*3) - (lb_red.bounding_box[BB_HEIGHT]//2*3)

    splash.append(round_button(lb_blue, x_1, y_1, radius))
    splash.append(round_button(lb_none, x_2, y_1, radius))
    splash.append(round_button(lb_red, x_1, y_2, radius))
    splash.append(round_button(lb_green, x_2, y_2, radius))

    EPD.root_group.append(splash)

def usage():
    background()
    text(" Push buttons to\n  make blinking\n     pattern", scale=1, y=4)
    button_row(0, 107, "S4: R", "S5: G", "S6: B", "S7: N")
    EPD.refresh()

async def main():
    usage()
    button_tasks = badge.buttons.start_tasks(interval=0.05)
    event_tasks = evt.start_tasks()
    # all_tasks = [info_task, battery_task] + button_tasks + event_tasks
    all_tasks = [ ] + button_tasks + event_tasks
    i = 0 
    while(True):
        # set_neopixel("b", 0)
        patlen = len(Pattern)
        a = Pattern[i%patlen]
        b = Pattern[(i+1)%patlen]
        c = Pattern[(i+2)%patlen]
        d = Pattern[(i+3)%patlen]
        set_neopixels(a,b,c,d)
        await asyncio.sleep(0.5)
        # set_neopixel("b", 255<<8)
        # await asyncio.sleep(1.5)
        i = (i + 1) % patlen
    await asyncio.gather(*all_tasks)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        epd_print_exception(e)
