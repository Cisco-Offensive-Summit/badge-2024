import asyncio
import os
import sys

import board
import supervisor

import badge.buttons
import badge.events as evt
from badge.events import on

from badge.neopixels import set_neopixel, set_neopixels
from displayio import Group
from adafruit_display_text import label
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from badge.colors import BLACK, WHITE
import badge.screens
from badge.screens import EPD
import terminalio

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

def text(text, scale=1, x=0, y=0):
    EPD.text(text, x, y, 1, size=scale)

def background():
    EPD.fill(0)


def button_row(x, y, a_txt=None, b_txt=None, c_txt=None, d_txt=None):
    spacing = 17
    radius = 5
    for n, txt in enumerate([a_txt, b_txt, c_txt, d_txt]):
        if txt is None:
            continue
        badge.screens.epd_round_button(txt, 7 + n * (EPD._font.width(txt) + radius + spacing), EPD.height - 5 - radius - EPD._font.font_height, radius)

def usage():
    background()
    text(" Push buttons to\n  make blinking\n     pattern", 2, 0, 4)
    button_row(0, 107, "S4: R", "S5: G", "S6: B", "S7: N")
    EPD.draw()

async def main():
    button_tasks = badge.buttons.start_tasks(interval=0.05)
    event_tasks = evt.start_tasks()
    # all_tasks = [info_task, battery_task] + button_tasks + event_tasks
    all_tasks = [ ] + button_tasks + event_tasks
    usage()
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

run()