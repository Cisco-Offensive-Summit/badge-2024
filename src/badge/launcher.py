import displayio, asyncio, json, sys
import microcontroller, supervisor
from displayio import Group, TileGrid
from os import listdir
from storage import disable_usb_drive, remount
import adafruit_imageload
from adafruit_bitmap_font.bitmap_font import load_font
from adafruit_display_text.scrolling_label import ScrollingLabel

from badge.app import App
from badge.fileops import is_dir, is_file
from badge.colors import SITE_BLUE
from badge.colors import SITE_RED
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import clear_lcd_screen
from badge.screens import clear_epd_screen
from badge.screens import epd_round_button
import badge.buttons
from badge.buttons import a_pressed as ap
from badge.buttons import d_pressed as dp
import badge.events as evt
from badge.events import on
from badge.log import info, log
from badge.neopixels import set_neopixel, set_neopixels
from badge.ziplist import ziplist

#################### Globals ###############

### Launcher ###
BOOT_CONFIG_START = len(microcontroller.nvm)//2
SELECTO = None # Populate at run()

### Apps ###
APPS_DIR = "/apps"
APPLIST = [] # Populate at run()

### UI ###
OFF, DIM, BRIGHT = (0, 0, 0), (0, 25, 25), (0, 106, 66)
NEO_STATES = [OFF, DIM, BRIGHT]

EPD_DISP_H = EPD.height
EPD_DISP_W = EPD.width
LCD_DISP_H = LCD.height
LCD_DISP_W = LCD.width
ICON_H = 76
ICON_W = 128
FONT = load_font('font/font.pcf')

#################### Apps ##################

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

#################### UI ####################

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

def display_lcd_app_icon(app: App):
  icon = app.icon_file
  app_name = app.app_name
  meta = app.metadata_json
  text = f"{meta['app_name']}   Created By: {meta['author']}          "

  clear_lcd_screen(LCD.root_group)

  group = Group()  
  background = displayio.Bitmap(128, 128, 1)
  palette1 = displayio.Palette(1)
  palette1[0] = SITE_RED 
  bitmap, palette2 = adafruit_imageload.load(icon,bitmap=displayio.Bitmap,palette=displayio.Palette)
  tile_grid1 = TileGrid(background, pixel_shader=palette1)
  tile_grid2 = TileGrid(bitmap, pixel_shader=palette2)
  label = ScrollingLabel(font=FONT, text=text, max_characters=13, animate_time=0.2)
  y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  label.x = 5
  label.y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  LCD.root_group = group
  group.append(tile_grid1)
  group.append(tile_grid2)
  group.append(label)

  return label

def draw_epd_launch_screen():
  B1 = "S4 Next App"
  B2 = "S7 Launch"
  SUMMIT = "Offensive Summit 2024"
  HEADER = "Select An App"
  scale = 2
  button_rad = 5
  SUMMIT_x = (EPD_DISP_W //2) - (EPD._font.width(SUMMIT) // 2)
  SUMMIT_y = 1
  HEADER_x = (EPD_DISP_W //2) - ((EPD._font.width(HEADER) * scale) // 2)
  HEADER_y = (EPD_DISP_H //2) - ((EPD._font.font_height * scale) // 2)
  B1_x = 5 + button_rad
  B1_y = EPD_DISP_H - 5 - button_rad - EPD._font.font_height
  B2_x = EPD_DISP_W - 5 - button_rad - EPD._font.width(B2)
  B2_y = EPD_DISP_H - 5 - button_rad - EPD._font.font_height
  clear_epd_screen()
  EPD.text(SUMMIT,SUMMIT_x,SUMMIT_y,1,size=1)
  EPD.text(HEADER,HEADER_x,HEADER_y,1,size=scale)
  epd_round_button(B1, B1_x, B1_y, 5)
  epd_round_button(B2, B2_x, B2_y, 5)
  EPD.draw()

#################### Launcher ##############

@on(evt.BTN_A_PRESSED)
def choose_next_app(event):
    # on press, just light the light to indicate
    # press received, but don't actually advance the
    # selector until button release. not sure why, but
    # feels like this is how it should work.
    set_neopixel("a", 255)

@on(evt.BTN_A_RELEASED)
def a_released(event):
    # turn it off
    set_neopixel("a", 0)
    # advance to next app
    SELECTO.forward()
    app, indicator = SELECTO.current()
    vals = get_neo_update_vals(indicator)
    set_neopixels(*vals)
    label = display_lcd_app_icon(app)
    while not ap() and not dp():
      label.update()

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
    log("app_launching", entry.code_file, type(entry.code_file))
    launch_app(entry)

def clear_nvm():
    nvm_len = len(microcontroller.nvm)
    zeros = b"\x00" * (nvm_len - BOOT_CONFIG_START)
    # Check if clear is needed since nvm has a write lifetime
    if microcontroller.nvm[BOOT_CONFIG_START:] != zeros:
        microcontroller.nvm[BOOT_CONFIG_START:] = zeros

def nvm_store_config(new_boot_config):
    json_bytes = bytes(json.dumps(new_boot_config), "ascii")
    len_json = len(json_bytes)
    microcontroller.nvm[BOOT_CONFIG_START:BOOT_CONFIG_START + len_json] = json_bytes
    log(f"stored nvm config: {json_bytes}")

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

async def main():
    # log("main", APPLIST)
    #render_main(APPLIST)
    app,_ = SELECTO.current()
    # info_task = asyncio.create_task(info())
    button_tasks = badge.buttons.start_tasks(interval=0.05)
    event_tasks = evt.start_tasks()
    # all_tasks = [info_task, battery_task] + button_tasks + event_tasks
    all_tasks = [] + button_tasks + event_tasks
    label = display_lcd_app_icon(app)
    draw_epd_launch_screen()
    while not ap() and not dp():
      label.update()
    await asyncio.gather(*all_tasks)

def run():
    global SELECTO, APPLIST
    APPLIST = get_app_list()

    sel_entries = list(zip(APPLIST, indicators()))
    SELECTO = ziplist(sel_entries)
    if APPLIST:
        set_neopixels(*get_neo_update_vals(sel_entries[0][1]))
    
    # Use a stored next_code_file from nvm first
    next_code_file = None
    try:
        cfg = json.loads(microcontroller.nvm[BOOT_CONFIG_START:])
        next_code_file = cfg.get("next_code_file", None)
    except Exception:
        pass
        # log("ERR read_nvm_config", repr(e))
    if next_code_file:
        log("Next code file:", next_code_file)
        clear_nvm()
        supervisor.set_next_code_file(next_code_file)
        supervisor.reload()
        sys.exit(0)
    # If continuing, set nvm back to blank and continue as usual
    clear_nvm()
    asyncio.run(main())

def run_at_boot():
    global BOOT_CONFIG_START
    default_config = {
        "mount_root_rw": False,
        "disable_usb_drive": False,
        "next_code_file": None,
    }

    new_config = None
    try:
        new_config = json.loads(microcontroller.nvm[BOOT_CONFIG_START:])
    except Exception as e:
        print("nvram new_config json.loads exception:")
        print(repr(e))
        print()

    boot_config = default_config

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
            print(repr(e))


    if boot_config["mount_root_rw"]:
        try:
            remount("/", readonly=False)
        except Exception as e:
            print(repr(e))

#################### boot ##################
###
### Please put the following commented code
### in your /boot.py file.
### This is needed to allow apps to write to
### the filesystem if they specify they it.

"""
default_config = {
    "mount_root_rw": False,
    "disable_usb_drive": False,
    "next_code_file": None,
}

new_config = None
BOOT_CONFIG_START = len(microcontroller.nvm) // 2

# If first byte is 0 then its been cleared
if microcontroller.nvm[BOOT_CONFIG_START] != 0:
    try:
        new_config = json.loads(microcontroller.nvm[BOOT_CONFIG_START:])
    except Exception as e:
        print("nvram new_config json.loads exception:")
        print(repr(e))
        print()

boot_config = default_config

if new_config is not None:
    boot_config.update(new_config)

# mount_root_rw needs disable_usb_drive.
if boot_config["mount_root_rw"]:
    boot_config["disable_usb_drive"] = True

# Check boot options and do corresponding thing
if boot_config["disable_usb_drive"]:
    try:
        storage.disable_usb_drive()
    except Exception as e:
        print(repr(e))


if boot_config["mount_root_rw"]:
    try:
        storage.remount("/", readonly=False)
    except Exception as e:
        print(repr(e))


# next_code_file will be set by launcher,
# then passed back after it hard boots with the updated
# boot settings
"""
