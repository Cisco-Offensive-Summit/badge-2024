import json

import microcontroller
import storage
import supervisor

# boot.py will process boot options from nvm
# the process goes like this:
#  1. an appdir containing boot.json will be launched by setting
#     nvm from the boot.json, which triggers
#     microcontroller.reset(), which re-runs boot.py using
#     those nvm settings
#  3. after this setup, the app will be launched via
#     the normal soft boot.
#  4. settings will return to normal at next run of launcher


default_config = {
    "mount_root_rw": False,
    "disable_usb_drive": False,
    "next_code_file": None,
}

new_config = None
try:
    new_config = json.loads(microcontroller.nvm[:])
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

print(f"boot config:{repr(boot_config)}")

# clear the nvram
# microcontroller.nvm[:] = b"\x00" * len(microcontroller.nvm)
