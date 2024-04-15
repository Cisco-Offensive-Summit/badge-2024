import asyncio
import random
import sys
import time

import board
import supervisor
import terminalio
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle

import badge.buttons
import badge.events as evt
from badge.buttons import any_button_downup
from badge.colors import BLACK, WHITE
from badge.screens import EPD, epd_round_button, epd_center_text
from badge.events import on
from badge.log import dbg, info
from badge.neopixels import neopixels_off, set_neopixel

DEBUG = False

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

def background():
    EPD.fill(0)

def button_row():
    radius = 5
    epd_round_button("Quit", 5 + radius, EPD.height - 5 - radius - EPD._font.font_height, radius)
    epd_round_button("Try again", EPD.width - 5 - radius - EPD._font.width("Try again"), EPD.height - 5 - radius - EPD._font.font_height, radius)

def welcome_screen():
    title = "It's not Simon!"
    subtitle1 = "Watch the pattern, remember it."
    subtitle2 = "Repeat it!"
    subtitle3 = "[ PRESS ANY BUTTON TO START ]"

    background()
    epd_center_text(title, 2, scale=2)
    epd_center_text(subtitle1, 40)
    epd_center_text(subtitle2, 50)
    epd_center_text(subtitle3, 85)
    EPD.draw()

def score_screen(score):
    background()
    EPD.text('Score:', 2, 2, 1, size=2)
    epd_center_text(f"{score}", 25, scale=4)
    button_row()
    EPD.draw()

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
