import board
import digitalio
import json
import microcontroller
import storage
import supervisor
import os
from badge_nvm import nvm_open                                                                                     
from time import sleep
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import center_text_x_plane
from badge.screens import center_text_y_plane
from badge.screens import clear_screen
from badge.log import log
from badge.constants import LOADED_APP
from badge.constants import BOOT_CONFIG
from badge.constants import DEFAULT_CONFIG
from displayio import Group
from terminalio import FONT
from adafruit_display_text.label import Label

#os.rename("boot_out.txt", "boot_out.txt.bak")

###############################################################################

# boot.py will process boot options from nvm
# the process goes like this:
#  1. an appdir containing boot.json will be launched by setting
#     nvm from the boot.json, which triggers
#     microcontroller.reset(), which re-runs boot.py using
#     those nvm settings
#  3. after this setup, the app will be launched via
#     the normal soft boot.
#  4. settings will return to normal at next run of launcher

supervisor.runtime.autoreload = False

BTN1 = digitalio.DigitalInOut(board.BTN1)
BTN1.direction = digitalio.Direction.INPUT
BTN1.pull = digitalio.Pull.UP

BTN2 = digitalio.DigitalInOut(board.BTN2)
BTN2.direction = digitalio.Direction.INPUT
BTN2.pull = digitalio.Pull.UP

BTN3 = digitalio.DigitalInOut(board.BTN3)
BTN3.direction = digitalio.Direction.INPUT
BTN3.pull = digitalio.Pull.UP

BTN4 = digitalio.DigitalInOut(board.BTN4)
BTN4.direction = digitalio.Direction.INPUT
BTN4.pull = digitalio.Pull.UP

###############################################################################
# Hold BTN1 and BTN4 during reboot to enter safe mode
###############################################################################
if not BTN1.value and not BTN4.value:
    microcontroller.on_next_reset(microcontroller.RunMode.SAFE_MODE)
    microcontroller.reset()

###############################################################################
# Hold BTN1 and BTN2 during reboot to do the OTA
###############################################################################
if not BTN1.value and not BTN2.value:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=False)

    from badge.wifi import WIFI
    from badge.utils import download_file
    import json

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    wifi = WIFI()
    if wifi.connect_wifi():
        rsp = wifi.requests(method='GET',url=wifi.host+'badge/OTA',headers=headers)
        files = rsp.json()['files']

        i = 1
        total = len(files)
        for file in files:
            print(f'Downloading file {i} of {total}')
            i +=1
            if not download_file(file, wifi):
                print(f'Failed to download file {file}')
            
###############################################################################
# Hold BTN4 and BTN3 during reboot to GET a TOKEN
###############################################################################
if not BTN3.value and not BTN4.value:
  storage.remount("/", readonly=False, disable_concurrent_write_protection=False)
  from get_token import get_token
  success = get_token()
  if success:
    nobody = center_text_y_plane(EPD, center_text_x_plane(EPD, Label(font=FONT, text='nobody', scale=3)))
    clear_screen(EPD)
    EPD.root_group.append(nobody)
    EPD.refresh()
    while True:
      pass

  else:
    sleep(600)

###############################################################################

new_config = None

try:
    new_config = json.loads(nvm_open(BOOT_CONFIG))
    log(f'Config read from NVM: {new_config}')
except KeyError:
    log(f"boot.py: No config found")

boot_config = DEFAULT_CONFIG

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
        log(repr(e))

if boot_config["mount_root_rw"]:
    try:
        storage.remount("/", readonly=False)
    except Exception as e:
        log(repr(e))


# next_code_file will be set by launcher,
# then passed back after it hard boots with the updated
# boot settings
