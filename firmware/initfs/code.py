import board, neopixel, displayio, digitalio
from time import sleep
try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire
from busio import SPI
from traceback import print_exception
from adafruit_st7735r import ST7735R
import framebufferio
import aurora_epaper 
import supervisor

def loop_forever():
    while True:
        sleep(1)

def test_blinky():
    print("Testing Blinky")
    print("--------------")
    led = digitalio.DigitalInOut(board.GPIO6)
    led.direction = digitalio.Direction.OUTPUT

    for i in range(6):
        led.value = True
        sleep(0.25)
        led.value = False
        sleep(0.25)
    
    led.value = True

def test_neopixels(pixels):
    print("Testing Neopixels")
    print("-----------------")

    print("Neopixels: red")
    pixels.fill(0x00FF00)
    sleep(0.5)
    print("Neopixels: green")
    pixels.fill(0xFF0000)
    sleep(0.5)
    print("Neopixels: blue")
    pixels.fill(0x0000FF)
    sleep(0.5)
    print("Neopixels: white")
    pixels.fill(0xFFFFFF)
    sleep(0.5)

def test_buttons(pixels):
    print("Testing Buttons")
    print("---------------")

    b1b = False
    b2b = False
    b3b = False
    b4b = False

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

    while not b1b or not b2b or not b3b or not b4b:
        if not BTN1.value and not b1b:
            print('Button 1')
            pixels[3] = 0xFFFF00
            b1b = True
        if not BTN2.value and not b2b:
            print('Button 2')
            pixels[2] = 0xFFFF00
            b2b = True
        if not BTN3.value and not b3b:
            print('Button 3')
            pixels[1] = 0xFFFF00
            b3b = True
        if not BTN4.value and not b4b:
            print('Button 4')
            pixels[0] = 0xFFFF00
            b4b = True
        
        sleep(0.1)

    print("All buttons work!")
    sleep(1)

def test_epd(d_spi):
    print("Testing EPD")
    print("-----------")

    framebuf = aurora_epaper.AuroraMemoryFramebuffer(d_spi, board.EINK_CS, board.EINK_RST, board.EINK_BUSY, board.EINK_DISCHARGE, 128, 96)
    framebuf.free_bus = False

    EPD = framebufferio.FramebufferDisplay(framebuf, auto_refresh=False)
    bitmap = displayio.OnDiskBitmap("/img/opossom.bmp")
    palette = displayio.Palette(2)
    palette[0] = 0xFFFFFF
    palette[1] = 0x000000
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    group = displayio.Group()
    group.append(tile_grid)
    EPD.root_group = group
    EPD.refresh()

def run():
    supervisor.runtime.autoreload = False
    displayio.release_displays()

    test_failure = False

    try:
        d_spi = SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
        lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
        lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)
    except Exception as e:
        test_failure = True
        print("Test Failed: LCD")
        print_exception(e)

    try:
        test_blinky()
        print()
    except Exception as e:
        test_failure = True
        print("Test Failed: Blinky")
        print_exception(e)

    try:
        pixels = neopixel.NeoPixel(board.NEOPIXEL, 4, brightness=0.25, auto_write=True)
        test_neopixels(pixels)
        print()
    except Exception as e:
        test_failure = True
        print("Test Failed: Neopixels")
        print_exception(e)

    try:
        test_buttons(pixels)
        print()
    except Exception as e:
        test_failure = True
        print("Test Failed: Buttons")
        print_exception(e)

    try:
        test_epd(d_spi)
        print()
    except Exception as e:
        test_failure = True
        print("Test Failed: EPD")
        print_exception(e)

        
    if test_failure:
        print("Test failed")
        try:
            pixels.fill(0x00FF00)
        except:
            pass
    else:
        pixels.fill(0xFF0000)
        print("Test successful!")
        
    loop_forever()

if __name__ == "__main__":
    run()
