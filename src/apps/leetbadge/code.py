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

import asyncio, random, supervisor, time

from adafruit_display_text.label import Label
from adafruit_display_text.text_box import TextBox
from displayio import Group, OnDiskBitmap, Palette, TileGrid
from terminalio import FONT

import badge.events as events
import badge.buttons as buttons
from badge.constants import EPD_SMALL, BLACK, BLUE, WHITE, YELLOW, MAGENTA
from badge.fileops import is_file
from badge.neopixels import set_neopixels, neopixels_off
from badge.screens import LCD, EPD, clear_screen, epd_print_exception

from leaderboard import post_to_leaderboard

EPD_CUSTOM_IMAGE = '/img/my_epd_logo.bmp'
EPD_LARGE_IMAGE = '/img/epd_logo.bmp'
EPD_SMALL_IMAGE = '/apps/leetbadge/img/epd_logo_small.bmp'

LCD_CUSTOM_IMAGE = '/img/my_lcd_logo.bmp'


## HSL to RGB conversion

ONE_THIRD = 1.0 / 3.0
ONE_SIXTH = 1.0 / 6.0
TWO_THIRD = 2.0 / 3.0

def hsl_to_rgb(hue, sat, light):
    """
    Convert from Hue, Saturation, Lightness to Red, Green, Blue colorspaces
    """
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
    """
    HSL value mapping helper
    """
    hue = hue % 1.0
    if hue < ONE_SIXTH:
        return chroma1 + (chroma2 - chroma1) * hue * 6.0
    if hue < 0.5:
        return chroma2
    if hue < TWO_THIRD:
        return chroma1 + (chroma2 - chroma1) * (TWO_THIRD - hue) * 6.0
    return chroma1


def make_color(h):
    """
    Convert a hue (1.0 = 360 degrees) to 24bit RGB integer
    """
    global dimmer

    brightness = 0.5 * dimmer
    r, g, b = hsl_to_rgb(h, 1.0, brightness)
    return (r << 16) | (g << 8) | (b)

def random_color(brightness=128):
    """Generate a random RGB color, dimmed by brightness."""
    global dimmer

    # Scale given brightness by dimmer val
    brightness = dimmer * (float(brightness)/256.0)
    # Any color will do
    hue = random.random()
    # Favor more saturated colors
    if random.randint(0, 3) == 0:
        saturation = random.uniform(0.2, 0.75)
    else:
        saturation = random.uniform(0.75, 1.0)

    r, g, b = hsl_to_rgb(hue, saturation, brightness)
    return (r << 16) | (g << 8) | (b)

#################################

def draw_lcd_splash():
    clear_screen(LCD)

    title_lbl = TextBox(
        FONT,
        text="LeetBadge v1.1",
        width=LCD.width,
        height=TextBox.DYNAMIC_HEIGHT,
        align=TextBox.ALIGN_CENTER,
        color=YELLOW,
        background_color=BLUE)
    title_lbl.x = 0
    title_lbl.y = 6

    pgiblock_lbl = Label(
        FONT,
        text ="PGI\nBLOCK",
        padding_top = 18,
        padding_left = 4,
        padding_bottom = 3,
        padding_right = 12,
        color=WHITE,
        background_color=0x7CC343)
    pgiblock_lbl.x = 80
    pgiblock_lbl.y = 90

    instruct_lbl = Label(
        FONT,
        text = f"For custom art add:\n{EPD_CUSTOM_IMAGE}\n{LCD_CUSTOM_IMAGE}\n\nEnjoy!",
        color=WHITE)
    instruct_lbl.x = 2
    instruct_lbl.y = 20

    group = Group()
    group.append(title_lbl)
    group.append(pgiblock_lbl)
    group.append(instruct_lbl)
    group.append(status_lbl)
    LCD.root_group = group


def draw_lcd_screen():
    """
    Draw the custom image to the screen, otherwise print instructions
    """

    path = LCD_CUSTOM_IMAGE
    if is_file(path):
        group = Group()
        bitmap = OnDiskBitmap(path)
        tile_grid = TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        group.append(tile_grid)

        # Odd thing here is moving the status to our new group
        LCD.root_group.remove(status_lbl)
        group.append(status_lbl)

        LCD.root_group = group


def draw_epd_screen():
    """
    Draw the most appropriate image, favoring a custom one
    """

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
    """
    We don't ever redraw the screen, so this clears and paints them
    """
    draw_epd_screen()
    draw_lcd_screen()


#################################

async def rainbow_scroller():
    """
    Full-on double rainbow
    """

    offsets = (0.0, 0.075, 0.150, 0.225)
    hue = 0.0
    while True:
        colors = tuple(make_color((hue+offset) % 1.0) for offset in offsets)
        set_neopixels(*colors)

        hue += 0.01
        if hue > 1.0:
            hue %= 1.0

        await asyncio.sleep(0.05)


#################################

async def blinkenlights():
    """
    Simple blinking lights generator.  A bit too "coordinated"
    """
    while True:
        pixels = [random_color() for _ in range(4)]
        set_neopixels(*pixels)

        # Vary the timing slightly to create a more organic, data-flow feel
        await asyncio.sleep(random.uniform(0.05, 0.3))

        # Occasionally flash a quick burst of changes
        if random.random() < 0.05:
            for _ in range(random.randint(2, 5)):
                pixels = [random_color(128) for _ in range(4)]
                set_neopixels(*pixels)
                await asyncio.sleep(random.uniform(0.02, 0.07))

        # Occasionally pause to mimic idle/buffering behavior
        if random.random() < 0.02:
            await asyncio.sleep(random.uniform(0.5, 1.5))



#################################

async def uberblinken_light_worker(index, state, lock):
    """
    Controls a single light's independent blinking behavior.
    """
    base_delay = random.uniform(0.1, 0.6)
    blink_color = random_color()

    while True:
        # Turn on
        state[index] = blink_color
        async with lock:
            set_neopixels(*state)

        await asyncio.sleep(random.uniform(base_delay * 0.5, base_delay * 1.5))

        # Turn off
        state[index] = 0x000000
        async with lock:
            set_neopixels(*state)

        await asyncio.sleep(random.uniform(base_delay * 0.5, base_delay * 2))

        # Occasionally change color
        if random.random() < 0.1:
            blink_color = random_color()


async def uberblinken_burst_controller(state, lock):
    """
    Occasionally triggers a subtle burst effect to simulate activity.
    """
    while True:
        await asyncio.sleep(random.uniform(5, 10))  # Time between bursts

        burst_color = random_color(96)
        burst_count = random.randint(2, 8)  # How many flashes

        for _ in range(burst_count):
            for i in range(4):
                # Randomly blink some lights on
                state[i] = burst_color if random.random() > 0.5 else 0x000000
            async with lock:
                set_neopixels(*state)
            await asyncio.sleep(random.uniform(0.08, 0.15))  # Slower, more natural

        # Return to idle state
        for i in range(4):
            state[i] = 0x000000
        async with lock:
            set_neopixels(*state)


async def uberblinkenlights():
    """
    Runs the uberblinkenlights effect
    """
    state = [0x000000] * 4
    lock = asyncio.Lock()

    workers = [uberblinken_light_worker(i, state, lock) for i in range(4)]
    workers.append(uberblinken_burst_controller(state, lock))

    await asyncio.gather(*workers)


#################################

async def lights_out():
    """
    Quiet time
    """

    set_neopixels(0x000000, 0x000000, 0x000000, 0x000000)

    try:
        post_to_leaderboard(6)
    except:
        pass

    while True:
        await asyncio.sleep(10.0)


#################################

# Our disgusting globals

animations = {
    "rainbow": rainbow_scroller,
    "uberblinken": uberblinkenlights,
    "blinkenlights": blinkenlights,
    "lights out": lights_out,
}

current_animation_task = None
current_animation_name = None

dimmer = 1.0

status_lbl = Label(
        FONT,
        text="",
        color=WHITE,
        background_color=MAGENTA,
        padding_left=1,
        x=2,
        y=123)

status_hide_task = None


#################################

async def switch_animation(name):
    global current_animation_task, current_animation_name, status_hide_task, dimmer

    if name == current_animation_name:
        # Already running: change brightness
        dimmer = dimmer - 0.25
        if dimmer <=  0.0:
            dimmer = 1.0
    else:
        # Different mode: change mode and reset brightness

        # Kill existing one (if any)
        if current_animation_task:
            current_animation_task.cancel()
            try:
                await current_animation_task
            except asyncio.CancelledError:
                pass

        # New operation
        dimmer = 1.0
        current_animation_name = name
        current_animation_task = asyncio.create_task(animations[name]())

    status = f"{name} ({int(dimmer*100)}%)"
    print(status)
    status_lbl.text = status

    # Reset status timer
    if status_hide_task:
        status_hide_task.cancel()
    status_hide_task = asyncio.create_task(hide_status_later())

async def hide_status_later():
    await asyncio.sleep(2.0)
    status_lbl.text = ''

async def handle_buttons():
    while True:
        btn = await buttons.any_button_downup()
        if btn == events.BTN_A_DOWNUP:
            await switch_animation("rainbow")
        elif btn == events.BTN_B_DOWNUP:
            await switch_animation("uberblinken")
        elif btn == events.BTN_C_DOWNUP:
            await switch_animation("blinkenlights")
        elif btn == events.BTN_D_DOWNUP:
            await switch_animation("lights out")


async def main():
    # Loading..
    draw_lcd_splash()

    # Start default animation tasks
    await switch_animation("rainbow")

    # Event/button handling tasks
    button_tasks = buttons.all_tasks()
    evt_tasks = events.start_tasks()
    # Drawing our stupid screens
    asyncio.create_task(init_screens())

    # We definitely keep this task alive
    await handle_buttons()


####

supervisor.runtime.autoreload = False
try:
    asyncio.run(main())
except Exception as e:
    epd_print_exception(e)
    EPD.refresh()
    time.sleep(60)

supervisor.reload()
