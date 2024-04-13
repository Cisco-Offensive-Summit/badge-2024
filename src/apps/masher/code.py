import asyncio
import random

import badge.buttons
import board
import supervisor
import terminalio
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.color import RED
from badge.screens import EPD, epd_round_button
from badge.events import ANY_BTN_PRESSED, ANY_BTN_RELEASED
from badge.log import log
from badge.neopixels import NP as PIXELS
from badge.neopixels import neopixels_off, set_neopixel, neopixel_reinit
from displayio import Group


def background():
    EPD.fill(0)


def button_row():
    radius = 5
    epd_round_button("Quit", 5 + radius, EPD.height - 5 - radius - EPD._font.font_height, radius)
    epd_round_button("Try again", EPD.width - 5 - radius - EPD._font.width("Try again"), EPD.height - 5 - radius - EPD._font.font_height, radius)

def center_text(txt, y, scale=1):
    EPD.text(txt, (EPD.width - (EPD._font.width(txt) * scale)) // 2, y, 1, size=scale)

def welcome_screen():
    title1 = "Welcome to"
    title2 = "MASHER."
    subtitle1 = "Watch the lights, mash the button"
    subtitle2 = "ASAP!"
    subtitle3 = "Don't mash too soon :("
    subtitle4 = "[ PRESS ANY BUTTON TO START ]"

    background()
    center_text(title1, 2, scale=2)
    center_text(title2, 20, scale=2)
    center_text(subtitle1, 40)
    center_text(subtitle2, 50)
    center_text(subtitle3, 60)
    center_text(subtitle4, 85)
    EPD.draw()

def score_screen(elapsed):
    background()

    EPD.text('Time:', 2, 2, 1, size=2)
    center_text(f"{elapsed} ms", 25, scale=4)

    button_row()
    EPD.draw()

    rs = RainbowSparkle(
        PIXELS, speed=0.1, num_sparkles=1, step=32, precompute_rainbow=True
    )
    for _ in range(50000):
        rs.animate()
    neopixels_off()

    return None


def fail_screen(elapsed, answer_button, button_pressed):
    background()
    r = ""
    m = ""
    if not elapsed:
        r = "Too soon"
        m = random.choice(
            [
                "You jumped the gun.",
                "Hold your horses!",
                "Too quick on the draw.",
                "Err: <premature press>",
                "Cool your jets turbo!",
                "Slow your roll chief!",
            ]
        )
    elif answer_button != button_pressed:
        r = "Wrong button"
        m = random.choice(
            [
                "De-stress, look, press.",
                "You're all thumbs.",
                "You'll get it next time.",
                "This is not the way.",
                "Use the force.",
                "'Twas but a typo...",
            ]
        )
    else:
        "Failure.\nReason unknown."

    center_text(r, 4, scale=2)
    center_text(m, 40)
    button_row()

    a = Blink(PIXELS, speed=0.2, color=RED)
    for _ in range(10000):
        a.animate()
    neopixels_off()

    EPD.draw()

RACE_START_TIME = None  # None or a ticks_ms() value.


def hit_the_lights():
    log("hit_the_lights")
    rc = RainbowChase(PIXELS, speed=0.075, size=3, spacing=5, step=32)
    for _ in range(random.randrange(10000, 22000)):
        rc.animate()
    rc = RainbowChase(PIXELS, speed=0.05, size=2, spacing=3, step=64, reverse=True)
    for _ in range(random.randrange(5000, 10000)):
        rc.animate()
    neopixels_off()


async def xmas_tree(answer_button):
    global RACE_START_TIME
    RACE_START_TIME = False
    hit_the_lights()
    # Hack to get neopixels to work correctly
    global PIXELS
    PIXELS = neopixel_reinit()
    print(f"xmas-tree:{answer_button}")
    wait_time = random.randrange(1200, 2750)
    await asyncio.sleep_ms(wait_time)  # random sleep between 1250 and 2250 ms
    print("xmas_tree:set_neopixel on")
    set_neopixel(answer_button, (0, 255, 0))
    # PIXELS.show()
    RACE_START_TIME = supervisor.ticks_ms()
    print(f"xmas_tree:returning {RACE_START_TIME}")
    return


async def play():
    global RACE_START_TIME
    RACE_START_TIME = None
    answer_button = random.choice(["A", "B", "C", "D"])

    # Start the lights in the background. This allows receipt of button press
    # to show "too soon" when user pressed button before light goes on.

    xmas_tree_task = asyncio.create_task(xmas_tree(answer_button))

    # Wait for keypress
    await ANY_BTN_PRESSED.wait()
    xmas_tree_task.cancel()

    button_pressed = ANY_BTN_PRESSED.data["name"]
    stop_msecs = supervisor.ticks_ms()
    neopixels_off()

    elapsed = None

    if RACE_START_TIME:
        elapsed = stop_msecs - RACE_START_TIME

    if (button_pressed == answer_button) and elapsed:
        score_screen(elapsed)
    else:
        fail_screen(elapsed, answer_button, button_pressed)

    keep_playing = True

    while True:
        await ANY_BTN_PRESSED.wait()
        b_pressed = ANY_BTN_PRESSED.data["name"]
        await ANY_BTN_RELEASED.wait()
        b_released = ANY_BTN_PRESSED.data["name"]
        if b_pressed != b_released:
            continue
        button = b_pressed
        if button == "A":
            # print(f"play.PRESS_RELEASE = {button}")
            keep_playing = False
            break
        if button == "D":
            # print(f"play.PRESS_RELEASE = {button}")
            keep_playing = True
            break
        continue
    return keep_playing


async def main():
    neopixels_off()
    _ = badge.buttons.start_tasks(interval=0.001)
    welcome_screen()
    await ANY_BTN_RELEASED.wait()
    keep_playing = True
    while keep_playing:
        keep_playing = await play()
        print(f"main. keep_playing={keep_playing}")
    print("main.reloading")
    supervisor.reload()


asyncio.run(main())
