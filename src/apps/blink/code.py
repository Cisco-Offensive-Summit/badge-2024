
import asyncio
import os
import sys

import board
import supervisor

import badge.buttons
import badge.events as evt
from badge.events import on
import badge.display

from badge.neopixels import set_neopixel, set_neopixels
from displayio import Group
from adafruit_display_text import label
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from badge.colors import BLACK, WHITE
from badge.display import refresh
import terminalio

badge.display.set_background()


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
    text_area = label.Label(
        terminalio.FONT, text=text, color=BLACK, background_color=WHITE, scale=scale
    )
    return text_area

def background(x, y):
    g = Group(x=x, y=y)
    g.append(Rect(0, 0, 296, 128, fill=WHITE, outline=WHITE))
    return g


def button_row(x, y, a_txt=None, b_txt=None, c_txt=None, d_txt=None):
    spacing = 12
    width = 64
    height = 20
    g = Group(x=x, y=y)
    for n, txt in enumerate([a_txt, b_txt, c_txt, d_txt]):
        if txt is None:
            continue
        btn = text_button(n * (width + spacing) + 2, 0, width, height, txt)
        g.append(btn)
    return g


def text_button(x, y, width, height, text):
    b1 = Group(x=x, y=y)
    b1.append(RoundRect(0, 0, width, height, 6, outline=BLACK, fill=WHITE))
    t1 = Label(terminalio.FONT, text=text, color=BLACK)
    t1.anchored_position = (width / 2, height / 2)  # center of Rectangle
    t1.anchor_point = (0.5, 0.5)
    b1.append(t1)
    return b1

def usage():
    main = Group()
    main.append(background(0, 0))
    t1 = Group(x=0, y=0)
    t1_txt = text("""Push buttons to make 
  blinking pattern""", scale=2)
    t1_txt.anchored_position = (32, 32)
    t1_txt.anchor_point = (0.0, 0.5)
    t1.append(t1_txt)
    main.append(t1)
    main.append(button_row(0, 107, "Red", "Green", "Blue", "Blank"))
    board.DISPLAY.root_group = main

    refresh()

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
