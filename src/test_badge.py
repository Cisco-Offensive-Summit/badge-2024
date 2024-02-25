import board, neopixel, displayio, digitalio
from time import sleep
from fourwire import FourWire
from busio import SPI
from traceback import print_exception
from adafruit_st7735r import ST7735R
import pdepd

def loop_forever():
    while True:
        sleep(1)

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
        if not BTN1.value:
            pixels[3] = 0xFFFF00
            b1b = True
        if not BTN2.value:
            pixels[2] = 0xFFFF00
            b2b = True
        if not BTN3.value:
            pixels[1] = 0xFFFF00
            b3b = True
        if not BTN4.value:
            pixels[0] = 0xFFFF00
            b4b = True
        
        sleep(0.1)

    print("All buttons work!")
    sleep(1)

def run():
    try:
        pixels = neopixel.NeoPixel(board.NEOPIXEL, 4, brightness=0.25, auto_write=True)

        displayio.release_displays()
        d_spi = SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
        lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
        lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)

        test_neopixels(pixels)
        print()
        test_buttons(pixels)

        raise Exception('Test')

        pixels.fill(0xFF0000)
        print("Badge test successful!")
        loop_forever()
    except Exception as e:
        print("Badge test failed!")
        print_exception(e)
        try:
            pixels.fill(0x00FF00)
        except:
            pass
        loop_forever()