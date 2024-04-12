import board
import digitalio
import json
import microcontroller
import os
import secrets
import storage
import supervisor                                                                                     
import updater
from time import sleep
from traceback import format_exception

# boot.py will process boot options from nvm
# the process goes like this:
#  1. an appdir containing boot.json will be launched by setting
#     nvm from the boot.json, which triggers
#     microcontroller.reset(), which re-runs boot.py using
#     those nvm settings
#  3. after this setup, the app will be launched via
#     the normal soft boot.
#  4. settings will return to normal at next run of launcher

def loop_forever():                                                                                                                                   
    while True:
        sleep(1)

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

# Hold BTN1 and BTN2 during reboot to update
if not BTN1.value and not BTN2.value:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=False)
                                                                                                                                                      
    ks = True
    if not BTN4.value:
        ks = False

    # Blinkenlights
    class NeoPixelIndicator(updater.UserIndicator):
        def __init__(self):
            import board, neopixel
            self.neopixels = neopixel.NeoPixel(board.NEOPIXEL, 4, brightness=0.25, auto_write=True)
            self.cur_state = -1
            for i in range(len(self.neopixels)):
                self.neopixels[i] = 0xFFFFFF
        def advance(self):
            self.cur_state += 1
            if self.cur_state == 4:
                self.cur_state = 0
            for i in range(len(self.neopixels)):
                if i != self.cur_state:
                    self.neopixels[i] = 0xFFFFFF
                else:
                    self.neopixels[i] = 0xFF0000 
        def error(self):
            self.neopixels.fill(0x00FF00)                                                                                                             
        def complete(self):
            self.neopixels.fill(0xFF0000)

    # Print funny lines to user to show it is working
    class PrintFlavortext(updater.UserPrint):
        def __init__(self):
            import board, displayio
            import terminalio
            from adafruit_st7735r import ST7735R
            try:
                from fourwire import FourWire
            except ImportError:
                from displayio import FourWire
            from busio import SPI
            displayio.release_displays()
            d_spi = SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
            lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
            self.lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)
            splash = displayio.Group()
            fontx, fonty = terminalio.FONT.get_bounding_box()
            term_palette = displayio.Palette(2)
            term_palette[0] = 0x000000
            term_palette[1] = 0xffffff
            logbox = displayio.TileGrid(terminalio.FONT.bitmap,
                x=0,
                y=0,
                width=128 // fontx,
                height=128 // fonty,
                tile_width=fontx,
                tile_height=fonty,
                pixel_shader=term_palette)
            splash.append(logbox)                                                                                                                     
            self.logterm = terminalio.Terminal(logbox, terminalio.FONT)
            self.lcd.root_group = splash
            self.logterm.write("Update Starting!\r\n----------------\r\n")
        def do_print(self, s):
            import flavortext
            self.logterm.write("{}\r\n".format(flavortext.line()))
        def complete(self):
            self.logterm.write("------------------\r\nUpdate successful!\r\n")
        def error(self):
            self.logterm.write("------------------\r\nUpdate failed! View updater_out.txt for more information.\r\n")


    OTA = updater.Updater(secrets.WIFI_NETWORK, secrets.WIFI_PASS, secrets.GH_REPO, branch=secrets.GH_BRANCH, gh_token=secrets.GH_TOKEN, src_path=secrets.GH_SRC_FOLDER, debug=True, mpy2py=True, keep_secrets=ks)

    if not OTA.set_user_indicator_class(NeoPixelIndicator):
        print('Could not instantiate user indicator class')                                                                                           
    if not OTA.set_user_print_class(PrintFlavortext):
        print('Could not instantiate user print class')

    try:
        special_files = OTA.run()
        for tup in special_files:
            os.rename(tup[0], tup[1])
    except Exception as e:
        with open("updater_out.txt", "a") as f:
            for line in format_exception(e):
                f.write(line)
        loop_forever()

    # So I can read that it worked
    sleep(3)
    microcontroller.reset()

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
