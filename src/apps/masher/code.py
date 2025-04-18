import asyncio
import random
import badge.buttons
import board
import supervisor

from adafruit_display_text.label import Label
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.color import RED
#from badge.screens import EPD, epd_round_button, epd_center_text, epd_print_exception
from badge.constants import BLACK
from badge.constants import WHITE
from badge.constants import EPD_HEIGHT
from badge.constants import EPD_WIDTH
from badge.constants import BB_HEIGHT
from badge.constants import BB_WIDTH
from badge.screens import *
from badge.events import ANY_BTN_PRESSED, ANY_BTN_RELEASED
from badge.log import log
from badge.neopixels import NP as PIXELS
from badge.neopixels import neopixels_off, set_neopixel, neopixel_reinit
from displayio import Group
from terminalio import FONT
from time import sleep


def button_row():
    splash = Group()

    quit_lb = Label(font=FONT,text="Quit",color=WHITE)
    again_lb = Label(font=FONT,text="Again?",color=WHITE)
    radius = 5
    quit_x = radius
    quit_y = EPD_HEIGHT - radius - ((quit_lb._font.get_bounding_box()[1] * quit_lb.scale)//2)
    again_x = EPD_WIDTH - radius - again_lb.bounding_box[BB_WIDTH] * again_lb.scale
    again_y = quit_y
    splash.append(round_button(quit_lb, quit_x, quit_y, radius))
    splash.append(round_button(again_lb, again_x, again_y, radius))

    return splash

def welcome_screen():

    splash = Group()
    title1 = "Welcome to"
    title2 = "MASHER."
    subtitle1 = "Watch the lights"
    subtitle2 = "mash the button"
    subtitle3 = "ASAP!"
    subtitle4 = "Don't mash too soon!"
    subtitle5 = "[ PRESS ANY BUTTON"
    subtitle6 = "TO START ]"

    set_background(LCD, BLACK)
    title_lb = center_text_y_plane(LCD, center_text_x_plane(LCD, title1, 2, scale=2))
    title_lb.y = title_lb.y - 1 - ((title_lb.bounding_box[BB_HEIGHT]*title_lb.scale)//2)
    title2_lb = center_text_y_plane(LCD, center_text_x_plane(LCD, title2, 2, scale=2))
    title2_lb.y = title2_lb.y + 1 + ((title2_lb.bounding_box[BB_HEIGHT]*title2_lb.scale)//2)
    splash.append(title_lb)
    splash.append(title2_lb)
    LCD.root_group.append(splash)
    
    sleep(2)

    clear_screen(LCD)
    splash = Group()
    sub1 = center_text_x_plane(LCD, subtitle1, y=10)
    text_space = sub1.bounding_box[BB_HEIGHT]+2
    sub2 = center_text_x_plane(LCD, subtitle2, y=sub1.y + text_space)
    sub3 = center_text_x_plane(LCD, subtitle3, y=sub2.y + text_space)
    sub4 = center_text_x_plane(LCD, subtitle4, y=sub3.y + text_space)
    sub5 = center_text_x_plane(LCD, subtitle5, y=sub4.y + text_space)
    sub6 = center_text_x_plane(LCD, subtitle6, y=sub5.y + text_space)
    splash.append(sub1)
    splash.append(sub2)
    splash.append(sub3)
    splash.append(sub4)
    splash.append(sub5)
    splash.append(sub6)
    
    LCD.root_group.append(splash)

def score_screen(elapsed):
    global PIXELS
    clear_screen(EPD)
    set_background(EPD, BLACK)

    EPD.root_group.append(Label(font=FONT,text='Time:', x=2, y=FONT.get_bounding_box()[1], scale=2, color=WHITE))
    EPD.root_group.append(center_text_y_plane(EPD, center_text_x_plane(EPD, f"{elapsed} ms", scale=3)))

    EPD.root_group.append(button_row())  #Need to connect splash to something.
    EPD.refresh()

    rs = RainbowSparkle(
        PIXELS, speed=0.1, num_sparkles=1, step=32, precompute_rainbow=True
    )
    for _ in range(50000):
        rs.animate()
    neopixels_off()
    PIXELS = neopixel_reinit()

    return None


def fail_screen(elapsed, answer_button, button_pressed):
    set_background(EPD, BLACK)
    reason = ""
    roast = ""
    fail_screen = Group()
    if not elapsed:
        reason = "Too soon"
        roast = random.choice(
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
        reason = "Wrong button"
        roast = random.choice(
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

    fail_screen.append(center_text_x_plane(EPD, reason, y=(FONT.get_bounding_box()[1]//2)+1, scale=1))
    fail_screen.append(center_text_y_plane(EPD, center_text_x_plane(EPD, wrap_message(EPD,roast))))
    fail_screen.append(button_row())  # NEEDs to connect ot something

    a = Blink(PIXELS, speed=0.2, color=RED)
    for _ in range(10000):
        a.animate()
    neopixels_off()

    EPD.root_group.append(fail_screen)
    EPD.refresh()

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


try:
    asyncio.run(main())
except Exception as e:
    epd_print_exception(e)
