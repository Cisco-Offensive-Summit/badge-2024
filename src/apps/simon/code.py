import asyncio
import random
import sys
import time

import board
import supervisor
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text import label
from adafruit_display_text.label import Label
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from displayio import Group

import badge.buttons
import badge.events as evt
from badge.buttons import any_button_downup
from badge.colors import BLACK, WHITE
from badge.display import refresh
from badge.events import on
from badge.log import dbg, info
from badge.neopixels import neopixels_off, set_neopixel

DEBUG = True

RED = (255,0,0)
YELLOW = (255,255,0)
GREEN = (0,255,0)
BLUE = (0,0,255)


#--- indicators when button press
@on(evt.BTN_A_PRESSED)
def on_a_pressed(e):
    set_neopixel("a", RED)

@on(evt.BTN_A_RELEASED)
def on_a_released(e):
    set_neopixel("a", 0)

@on(evt.BTN_B_PRESSED)
def on_b_pressed(e):
    set_neopixel("b", YELLOW)

@on(evt.BTN_B_RELEASED)
def on_b_released(e):
    set_neopixel("b", 0)

@on(evt.BTN_C_PRESSED)
def on_c_pressed(e):
    set_neopixel("c", GREEN)

@on(evt.BTN_C_RELEASED)
def on_c_released(e):
    set_neopixel("c", 0)

@on(evt.BTN_D_PRESSED)
def on_d_pressed(e):
    set_neopixel("d", BLUE)

@on(evt.BTN_D_RELEASED)
def on_a_released(e):
    set_neopixel("d", 0)

def background(x, y):
    g = Group(x=x, y=y)
    g.append(Rect(0, 0, 296, 128, fill=WHITE, outline=WHITE))
    return g

def text(text, scale=1, x=0, y=0):
    text_area = label.Label(
        terminalio.FONT, text=text, color=BLACK, background_color=WHITE, scale=scale
    )
    return text_area


def text_button(x, y, width, height, text):
    b1 = Group(x=x, y=y)
    b1.append(RoundRect(0, 0, width, height, 6, outline=BLACK, fill=WHITE))
    t1 = Label(terminalio.FONT, text=text, color=BLACK)
    t1.anchored_position = (width / 2, height / 2)  # center of Rectangle
    t1.anchor_point = (0.5, 0.5)
    b1.append(t1)
    return b1

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


def welcome_screen():
    text = """
            It's not Simon!

       Watch the pattern, remember it. 
                Repeat it!

         [ PRESS ANY BUTTON TO START ]
    """
    main = Group()
    text_area = label.Label(
        terminalio.FONT, text=text, color=BLACK, background_color=WHITE
    )
    text_area.x = 0
    text_area.y = 0
    main.append(background(0, 0))
    main.append(text_area)
    board.DISPLAY.root_group = main
    refresh()


def score_screen(score):
    main = Group()
    main.append(background(0, 0))
    t1 = Group(x=0, y=0)
    t1_txt = text("Score:", scale=2)
    t1_txt.anchored_position = (32, 16)
    t1_txt.anchor_point = (0.0, 0.5)
    t1.append(t1_txt)
    main.append(t1)
    t2 = Group(x=0, y=0)
    t2_txt = text(f"{score}", scale=5)
    t2_txt.anchored_position = (296 // 2, 128 // 2)
    t2_txt.anchor_point = (0.5, 0.5)
    t2.append(t2_txt)
    main.append(t2)
    main.append(button_row(0, 107, "Quit", None, None, "Try Again"))
    board.DISPLAY.root_group = main

    refresh()

    # rs = RainbowSparkle(
    #     PIXELS, speed=0.1, num_sparkles=1, step=32, precompute_rainbow=True
    # )
    # for _ in range(50000):
    #     rs.animate()
    neopixels_off()

    return None


# do blocking so no button presses
def show_pattern(pattern):
    pattern_len = len(pattern)
    on_delay = 1.0 - min(pattern_len*0.1, 0.65)
    off_delay = 1.0 - min(pattern_len*0.1, 0.9)
    str_to_color = {
        "a" : RED, "b" : YELLOW, "c" : GREEN, "d": BLUE
    }
    for c in pattern:
        set_neopixel(c, str_to_color[c])
        time.sleep(on_delay) # block
        neopixels_off()
        time.sleep(off_delay)

# convert button event to string to compare to pattern
def evt_to_str(e):
    d = { evt.BTN_A_DOWNUP : "a",
         evt.BTN_B_DOWNUP : "b",
         evt.BTN_C_DOWNUP : "c",
         evt.BTN_D_DOWNUP : "d"
    }
    return d.get(e, "never_match")


async def play_game(length):
    func = "play_game"
    DEBUG and dbg(func, "length=", length)
    pattern = [ random.choice(["a","b","c","d"]) for _ in range(length) ]
    DEBUG and dbg(func, "pattern=", pattern)
    show_pattern(pattern)
    time.sleep(0.25)
    for c in pattern:
        e = await any_button_downup()
        e_str = evt_to_str(e)
        DEBUG and dbg(func,"e_str=",e_str)
        if e_str != c:
            return False # failed
    return True # won

async def goto_fail(score):
    func = "goto_fail"
    score_screen(score)
    e = await evt.any_event([evt.BTN_A_DOWNUP, evt.BTN_D_DOWNUP])
    DEBUG and dbg(func, "e=", e)
    if e == evt.BTN_A_DOWNUP:
        supervisor.reload()
        sys.exit(0)
    if e == evt.BTN_D_DOWNUP:
        time.sleep(1)
        return

async def mainloop():
    func = "mainloop"
    DEBUG and dbg(func,"start")
    welcome_screen()
    pattern_length = 0
    won = True
    DEBUG and dbg(func,"await downup")
    await any_button_downup()
    while True:
        neopixels_off()
        time.sleep(2)
        if not won:
            await goto_fail(pattern_length)
            pattern_length = 0
        pattern_length += 1
        DEBUG and dbg(func, "pattern_length", pattern_length)
        won = await play_game(pattern_length)
        DEBUG and dbg(func, "won=", won)


async def main():
    # info_task = asyncio.create_task(info(interval=5.0))
    button_tasks = badge.buttons.all_tasks(interval=0.1)
    evt_tasks = evt.start_tasks()
    mainloop_task = asyncio.create_task(mainloop())
    # all_tasks = [ info_task, mainloop_task ] + button_tasks
    all_tasks = [ mainloop_task ] + button_tasks + evt_tasks
    await asyncio.gather(*all_tasks)

def run():
    asyncio.run(main())

if __name__ == "__main__":
    DEBUG and dbg(f"{__file__}", "__name__ == '__main__'")
    run()
