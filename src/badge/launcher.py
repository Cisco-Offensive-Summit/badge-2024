import adafruit_imageload
import asyncio
import displayio
import json
import microcontroller
import supervisor
import sys
from adafruit_bitmap_font.bitmap_font import load_font
from adafruit_display_text.label import Label
from adafruit_display_text.scrolling_label import ScrollingLabel
from displayio import Group
from displayio import TileGrid
from os import listdir
from storage import disable_usb_drive
from storage import remount
from terminalio import FONT

import badge.buttons
import badge.events as evt
from badge_nvm import *
from badge.app import App
from badge.buttons import a_pressed as ap
from badge.buttons import d_pressed as dp
from badge.constants import BB_HEIGHT
from badge.constants import BB_WIDTH
from badge.constants import SITE_BLUE
from badge.constants import BOOT_CONFIG
from badge.constants import DEFAULT_CONFIG
from badge.constants import LOADED_APP
from badge.events import on
from badge.fileops import is_dir, is_file
from badge.log import info, log
from badge.neopixels import set_neopixel, set_neopixels
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import center_text_x_plane
from badge.screens import clear_screen
from badge.screens import round_button
from badge.ziplist import ziplist

#################### Globals ###############

### Launcher ###
SELECTO = None # Populate at run()

### Apps ###
APPS_DIR = "/apps"
APPLIST = [] # Populate at run()

### UI ###
ICON_H = 76
ICON_W = 128
SCROLL_FONT = load_font('font/font.pcf')

OFF, DIM, BRIGHT = (0, 0, 0), (0, 25, 25), (0, 106, 66)
NEO_STATES = [OFF, DIM, BRIGHT]

LAUNCHER_UI = None # Populated at run()

############### Button Events ##############

@on(evt.BTN_A_PRESSED)
def choose_next_app(event):
    # on press, just light the light to indicate
    # press received, but don't actually advance the
    # selector until button release. not sure why, but
    # feels like this is how it should work.
    set_neopixel("a", 255)

@on(evt.BTN_A_RELEASED)
def a_released(event):
    global LAUNCHER_UI
    # turn it off
    set_neopixel("a", 0)
    # advance to next app
    SELECTO.forward()
    app, indicator = SELECTO.current()
    vals = get_neo_update_vals(indicator)
    set_neopixels(*vals)
    LAUNCHER_UI.lcd_change_app(app)

@on(evt.BTN_C_PRESSED)
def c_pressed(event):
    set_neopixel("c", 255)

@on(evt.BTN_C_RELEASED)
def c_released(event):
    # turn it off
    set_neopixel("c", 0)
    sys.exit()

@on(evt.BTN_D_PRESSED)
def D_pressed(event):
    set_neopixel("d", 255)

@on(evt.BTN_D_RELEASED)
def d_released(event):
    set_neopixel("d", 0)
    current = SELECTO.current()
    entry = current[0]
    log("app_launching", entry.code_file, type(entry.code_file), entry.appdir)
    launch_app(entry)

############## Launcher UI #################

class LauncherUI:

    root_group: Group
    bitmap_group: Group
    scroll_label_group: Group
    hold_label: int
    cache_bmps: bool
    bmps: {}

    def __init__(self, cache_bmps=False):
        self.cache_bmps = cache_bmps
        # Select app
        app, _ = SELECTO.current()

        # Init LCD and EPD
        self.root_group, self.bitmap_group, self.scroll_label_group = self.init_lcd(app)
        LCD.root_group = self.root_group
        self.hold_label = 0
        self.init_epd()

    def init_lcd(self, app: App):
        """Create inital LCD display structure, with an initial app displayed"""
        icon = app.icon_file
        app_name = app.app_name
        meta = app.metadata_json
        text = f"{meta['app_name']}   Created By: {meta['author']}          "

        clear_screen(LCD)

        group = Group()  
        
        background = displayio.Bitmap(128, 128, 1)
        background_palette = displayio.Palette(1)
        background_palette[0] = SITE_BLUE
        background_tile_grid = TileGrid(background, pixel_shader=background_palette)

        # Cache bitmaps, this will take a while
        if self.cache_bmps:
            self.bmps = { app.app_name : adafruit_imageload.load(app.icon_file,bitmap=displayio.Bitmap,palette=displayio.Palette) }
            while True:
                SELECTO.forward()
                next_app, _ = SELECTO.current()
                if next_app.app_name in self.bmps:
                    break
                else:
                    self.bmps[next_app.app_name] = adafruit_imageload.load(next_app.icon_file,bitmap=displayio.Bitmap,palette=displayio.Palette)
        
        bitmap = displayio.OnDiskBitmap(icon)
        bitmap_tile_grid = TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
        
        scroll_label = ScrollingLabel(font=SCROLL_FONT, text=text, max_characters=13, animate_time=0, current_index=0)
        scroll_label.x = 5
        scroll_label.y = LCD.height-((LCD.height-ICON_H)//2)
        
        group.append(background_tile_grid)
        group.append(bitmap_tile_grid)
        group.append(scroll_label)
        scroll_label.update(force=True)

        return group, bitmap_tile_grid, scroll_label

    def init_epd(self):
        B1 = "S4 Next"
        B2 = "S7 Run"
        SUMMIT = "Offensive Summit"
        HEADER = "Select An App"
        scale = 1
        button_rad = 5
        splash = Group()

        SUMMIT_lb = center_text_x_plane(EPD, SUMMIT)
        HEADER_lb = center_text_x_plane(EPD, HEADER, scale=scale)
        HEADER_lb.y = (EPD.height //2) - ((HEADER_lb.bounding_box[BB_HEIGHT] * scale) // 2)

        B1_lb = Label(font=FONT,text=B1)
        B1_x = button_rad
        B1_y = EPD.height - button_rad - ((B1_lb.bounding_box[BB_HEIGHT]*scale)//2)

        B2_lb = Label(font=FONT,text=B2)
        B2_x = EPD.width - button_rad - B2_lb.bounding_box[BB_WIDTH]
        B2_y = EPD.height - button_rad - ((B2_lb.bounding_box[BB_HEIGHT]*scale)//2)

        clear_screen(EPD)
        splash.append(SUMMIT_lb)
        splash.append(HEADER_lb)
        splash.append(round_button(B1_lb, B1_x, B1_y, 5))
        splash.append(round_button(B2_lb, B2_x, B2_y, 5))
        EPD.root_group = splash
        EPD.refresh()

    def lcd_change_app(self, app: APP):
        icon = app.icon_file
        app_name = app.app_name
        meta = app.metadata_json

        if self.cache_bmps:
            self.bitmap_group.bitmap, self.bitmap_group.pixel_shader = self.bmps[app.app_name]
        else:
            bitmap = displayio.OnDiskBitmap(icon)
            self.bitmap_group.bitmap = bitmap
            self.bitmap_group.pixel_shader = bitmap.pixel_shader

        scroll_text = f"{meta['app_name']}   Created By: {meta['author']}          "
        self.scroll_label_group.text = scroll_text
        self.scroll_label_group.current_index = 0
        self.hold_label = 0
        LCD.refresh()

    async def lcd_animate_label(self):
        while True:
            if self.hold_label < 5:
                self.hold_label += 1
            else:
                self.scroll_label_group.update(force=True)
            await asyncio.sleep(0.2)
        
    async def run(self):
        button_tasks = badge.buttons.start_tasks(interval=0.05)
        event_tasks = evt.start_tasks()
        all_tasks = [asyncio.create_task(self.lcd_animate_label())] + button_tasks + event_tasks
        await asyncio.gather(*all_tasks)


################## NEOPIXELS ###############

def get_neo_update_vals(pattern):
    ret = [NEO_STATES[i] for i in pattern]
    return ret

def indicators():
    i = 0
    while True:
        base = (i // 4) % 2
        val = [base] * 4
        val[i%4] = base + 1
        yield tuple(val)
        i += 1

################## LAUNCHER ################

def get_app_list():
    entries = list()
    if not is_dir(APPS_DIR):
        log("APPS_DIR not directory")
        return entries
    for e in listdir(APPS_DIR):
        # Hide an app by renaming it's directory to start with '_'
        # XXX: hack for dev
        if e.startswith("_"):
            continue
        app_path = f"{APPS_DIR}/{e}"
        if is_dir(app_path):
            app = App(app_path)
            entries.append(app)
    return entries

def nvm_store_config(new_boot_config):
    dump = json.dumps(new_boot_config)
    nvm_save(BOOT_CONFIG,dump)
    log(f"stored nvm config: {dump}")

def launch_app(entry):
    new_boot_config = entry.boot_config
    log("launch_app", repr(new_boot_config))
    if new_boot_config:
        new_boot_config["next_code_file"] = entry.code_file
        nvm_store_config(new_boot_config)
        microcontroller.reset()
        sys.exit(0)

    supervisor.set_next_code_file(entry.code_file)
    supervisor.reload()
    sys.exit(0)

def run():
    global SELECTO, APPLIST, LAUNCHER_UI, BOOT_CONFIG
    APPLIST = get_app_list()

    sel_entries = list(zip(APPLIST, indicators()))
    SELECTO = ziplist(sel_entries)
    if APPLIST:
        set_neopixels(*get_neo_update_vals(sel_entries[0][1]))
    
    # Use a stored next_code_file from nvm first
    next_code_file = None
    try:
        cfg = json.loads(nvm_open(BOOT_CONFIG))
        next_code_file = cfg.get("next_code_file", None)
    except Exception as e:
        log("ERR read_nvm_config", repr(e))
        pass
    if next_code_file:
        appdir = cfg[LOADED_APP]
        config = DEFAULT_CONFIG
        config[LOADED_APP] = appdir
        set_config(config)        
        supervisor.set_next_code_file(next_code_file)
        supervisor.reload()
        sys.exit(0)
    # If continuing, set nvm back to blank and continue as usual
    set_config()
    LAUNCHER_UI = LauncherUI(cache_bmps=False)
    asyncio.run(LAUNCHER_UI.run())

def set_config(config:dict = None):
    if not config:
        config = DEFAULT_CONFIG

    nvm_save(BOOT_CONFIG, json.dumps(config))
    

def run_at_boot():
    global BOOT_CONFIG

    new_config = None
    try:
        new_config = json.loads(nvm_open(BOOT_CONFIG))
    except Exception as e:
        log(f"nvram new_config json.loads exception: {repr(e)}")
 
    boot_config = DEFAULT_CONFIG

    if new_config is not None:
        boot_config.update(new_config)

    # mount_root_rw needs disable_usb_drive.
    if boot_config["mount_root_rw"]:
        boot_config["disable_usb_drive"] = True

    # Check boot options and do corresponding thing
    if boot_config["disable_usb_drive"]:
        try:
            disable_usb_drive()
        except Exception as e:
            log(repr(e))


    if boot_config["mount_root_rw"]:
        try:
            remount("/", readonly=False)
        except Exception as e:
            log(repr(e))
