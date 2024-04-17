import asyncio
import json
import sys

import badge.buttons
from badge.buttons import a_pressed as ap
from badge.buttons import d_pressed as dp
import badge.events as evt
import microcontroller
import supervisor
from badge.app import APPLIST
from badge.events import on
#from badge.launcher_ui import render_main
from badge.log import info, log
from badge.neopixels import set_neopixel, set_neopixels
from badge.ziplist import ziplist
from badge.launcher_ui import display_lcd_app_icon
from badge.launcher_ui import draw_epd_launch_screen

supervisor.runtime.autoreload = False

OFF, DIM, BRIGHT = (0, 0, 0), (0, 25, 25), (0, 106, 66)

NEO_STATES = [OFF, DIM, BRIGHT]
BOOT_CONFIG_START = len(microcontroller.nvm)//2


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


sel_entries = list(zip(APPLIST, indicators()))
SELECTO = ziplist(sel_entries)

# If there's at least one app entry, then set the indicator light.
if APPLIST:
    set_neopixels(*get_neo_update_vals(sel_entries[0][1]))


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


def clear_nvm():
    nvm = microcontroller.nvm
    nvm_len = len(microcontroller.nvm)
    zeros = b"\x00" * (nvm_len//2)
    # Check if clear is needed since nvm has a write lifetime
    if nvm[BOOT_CONFIG_START:] != zeros:
        nvm[BOOT_CONFIG_START:] = zeros


def run():
    # Use a  stored next_code_file from nvm first
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


if __name__ == "__main__":
    run()
