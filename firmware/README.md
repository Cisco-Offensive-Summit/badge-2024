# Badge Firmware

Current version CircuitPython 8.2.10

## Flashing new badges

1. Download `esp-idf`
    - https://github.com/espressif/esp-idf.git
    - Install packages for `esp-idf` by running `install.sh`
    - Enable venv packages with `$ source esp-idf/export.sh`
2. Press both Reset and Boot switches, Release Reset switch then shortly after Boot switch 
    - This is only necessary if you have a circuitpython firmware installed on the badge already.
3. Run the following commands:
    - `ls /dev/cu.usbmodem*` to determine the device name, cu.usbmodem144101 in the example below
    - `esptool.py --chip esp32s3 --port /dev/cu.usbmodem144101 write_flash -z 0x0 firmware.bin`
5. Restart the badge
    - You should see the REPL console on the oled display.

## Building firmware

**Note**: I was not able to get firmware building correctly on Mac, I *think* it
has to do with some differences between GNU `objdump` and apple `objdump` 🤷.

Links:
- https://github.com/adafruit/circuitpython
- https://learn.adafruit.com/building-circuitpython/linux
- https://www.hackster.io/wallarug/circuitpython-creating-custom-boards-8e979e
- https://todbot.com/blog/2022/05/19/multiple-displays-in-circuitpython-compiling-custom-circuitpython/


1. Install dependencies
    - ```
      sudo apt install build-essential
      sudo apt install software-properties-common
      sudo add-apt-repository ppa:pybricks/ppa
      sudo apt install git git-lfs gettext uncrustify cmake
      sudo apt install python3-pip
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
      source $HOME/.cargo/env
      ```
2. Clone CircuitPython
    - `git clone https://github.com/adafruit/circuitpython.git`
    - `cd circuitpython`
    - `git checkout 9.2.7`
        - Commit for GitHub Release
    - All steps below assume you will start in the CircuitPython git directory
3. Install python modules
    - `pip3 install --upgrade -r requirements-dev.txt`
    - unfortunately you cannot use a pip env 😔
4. Fetch submodules
    - `cd ports/espressif && make fetch-port-submodules`
5. Install and enable `esp-idf`
    - ```
      cd ports/espressif/esp-idf
      ./install.sh
      source export.sh
      ```
6. Make `mpy-cross`
    - `make -C mpy-cross`
7. Copy the `offsummit_2024` directory into `ports/espressif/boards/` directory
8. Build the firmware
    - ```
      cd ports/espressif/
      make BOARD=offsummit_2024 -j 8
      ```
    - If you get errors about missing python modules do `pip install minify_html jsmin`

## Useful defines

All GPIO pins (except GPIO0 which is attached to the BOOT button) can be
referenced via the `board` module.

EX:
```
>>> import board
>>> board.GPIO8
board.GPIO8
>>> help(board.GPIO8)
object board.GPIO8 is of type Pin
```


The UART and STEMMA-I2C connectors are configured on startup.

EX:
```
>>> import board
>>> i2c = board.I2C()
>>> uart = board.UART()
>>>
>>> help(i2c)
object <I2C> is of type I2C
  deinit -- <function>
  __enter__ -- <function>
  __exit__ -- <function>
  scan -- <function>
  try_lock -- <function>
  unlock -- <function>
  readfrom_into -- <function>
  writeto -- <function>
  writeto_then_readfrom -- <function>
>>> help(uart)
object <UART> is of type UART
  __del__ -- <function>
  deinit -- <function>
  __enter__ -- <function>
  __exit__ -- <function>
  read -- <function>
  readline -- <function>
  readinto -- <function>
  write -- <function>
  reset_input_buffer -- <function>
  baudrate -- <property>
  in_waiting -- <property>
  timeout -- <property>
  Parity -- <class 'Parity'>
```


The Neopixel data pin is defined and ready to use.

EX:
```
>>> import board, neopixel
>>> pixels = neopixel.NeoPixel(board.NEOPIXEL, 4, brightness=0.5, auto_write=True)
>>> pixels.fill(0xFF0000)
```


Buttons are defined as `BTN1/4`.

EX:
```
>>> import time
>>> import board
>>> from digitalio import DigitalInOut, Direction, Pull
>>> btn = DigitalInOut(board.BTN1)
>>> btn.direction = Direction.INPUT
>>> btn.pull = Pull.UP
>>>
>>> while True:
...     if not btn.value:
...         print("BTN is down")
...     else:
...         #print("BTN is up")
...         pass
...
BTN is down
```


The TFT LCD display is enabled and ready to use:

EX:
```
>>> import board
>>> import displayio
>>>
>>> display = board.DISPLAY_LCD
>>> splash = displayio.Group()
>>> display.root_group = splash
>>> color_bitmap = displayio.Bitmap(128, 128, 1)
>>> color_palette = displayio.Palette(1)
>>> color_palette[0] = 0xFF0000
>>>
>>> bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
>>> splash.append(bg_sprite)
```


Full list of friendly name defines:

| GPIO PIN | Friendly Name           |
| -------- | ----------------------- |
| 43       | TX                      |
| 44       | RX                      |
| 3        | SCL                     |
| 4        | SDA                     |
| 5        | NEOPIXEL                |
| 48       | NEOPIXEL_POWER_INVERTED |
| 0        | BOOT                    |
| 7        | BTN1                    |
| 15       | BTN2                    |
| 16       | BTN3                    |
| 17       | BTN4                    |
| 8        | TFT_RST                 |
| 10       | TFT_CS                  |
| 11       | TFT_MOSI                |
| 12       | TFT_CLKS                |
| 13       | TFT_DC                  |
| 47       | TFT_BL                  |
| 18       | EINK_CS                 |
| 38       | EINK_BUSY               |
| 12       | EINK_CLKS               |
| 11       | EINK_MOSI               |
| 9        | EINK_MISO               |
| 45       | EINK_RST                |
| 21       | EINK_DISCHARGE          |

## TODO

- [x] Get E-INK display set up in firmware
- [-] Get Double Tap firmware update working (uf2 file)
