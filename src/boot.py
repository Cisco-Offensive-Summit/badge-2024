import board
import digitalio
import json
import microcontroller
import storage
import supervisor                                                                                     
from time import sleep
from badge.screens import EPD

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
# Hold BTN4 and BTN3 during reboot to GET a TOKEN
###############################################################################
# TODO:
#
#This whole section need to be fixed for the new EPD screen.
###############################################################################
if not BTN4.value and not BTN3.value:
  storage.remount("/", readonly=False, disable_concurrent_write_protection=False)
  from get_token import get_token
  success = get_token()
  if success:
    tag_height = EPD._font.font_height * 5
    tag_width = EPD._font.width("nobody") * 5
    EPD.fill(0)
    EPD.text("nobody", (EPD.width - tag_width) // 2, (EPD.height - tag_height) // 2, color=1, size=5)
    EPD.draw()
    while True:
      pass

  else:
    sleep(600)

###############################################################################

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
