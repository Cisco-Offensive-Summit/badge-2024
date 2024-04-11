import asyncio
import random

import badge.buttons
import board
import supervisor
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text import label
from adafruit_display_text.label import Label
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.color import RED
from badge.colors import BLACK, WHITE
from badge.display import refresh
from badge.events import ANY_BTN_PRESSED, ANY_BTN_RELEASED
from badge.log import log
from badge.neopixels import NP as PIXELS
from badge.neopixels import neopixels_off, set_neopixel
from displayio import Group


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


def welcome_screen():
    text = """
            Welcome to MASHER.

       Watch the lights, mash the button ASAP!

           Don't mash too soon :(

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


def text(text, scale=1, x=0, y=0):
    text_area = label.Label(
        terminalio.FONT, text=text, color=BLACK, background_color=WHITE, scale=scale
    )
    return text_area


def score_screen(elapsed):
    main = Group()
    main.append(background(0, 0))
    t1 = Group(x=0, y=0)
    t1_txt = text("Time:", scale=2)
    t1_txt.anchored_position = (32, 16)
    t1_txt.anchor_point = (0.0, 0.5)
    t1.append(t1_txt)
    main.append(t1)
    t2 = Group(x=0, y=0)
    t2_txt = text(f"{elapsed} ms", scale=5)
    t2_txt.anchored_position = (296 // 2, 128 // 2)
    t2_txt.anchor_point = (0.5, 0.5)
    t2.append(t2_txt)
    main.append(t2)
    main.append(button_row(0, 107, "Quit", None, None, "Try Again"))
    board.DISPLAY.root_group = main

    refresh()

    rs = RainbowSparkle(
        PIXELS, speed=0.1, num_sparkles=1, step=32, precompute_rainbow=True
    )
    for _ in range(50000):
        rs.animate()
    neopixels_off()

    return None


def fail_screen(elapsed, answer_button, button_pressed):
    main = Group()
    main.append(background(0, 0))
    t2 = Group(x=0, y=0)
    m = ""
    if not elapsed:
        m = "Too soon.\n"
        m += random.choice(
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
        m += "Wrong button.\n"
        m += random.choice(
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

    t2_txt = text(m, scale=2)
    t2_txt.anchored_position = (296 // 2, 48)
    t2_txt.anchor_point = (0.5, 0.5)
    t2.append(t2_txt)
    main.append(t2)
    main.append(button_row(0, 107, "Quit", None, None, "Try Again"))
    board.DISPLAY.root_group = main

    a = Blink(PIXELS, speed=0.2, color=RED)
    for _ in range(10000):
        a.animate()
    neopixels_off()
    refresh()
    return None


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
