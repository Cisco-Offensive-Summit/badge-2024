import board
import busio
import displayio
try:
    from FourWire import fourwire
except ImportError:
    from displayio import FourWire
from adafruit_st7735r import ST7735R
from pdepd import EPD as EPD_Class
from pdepd import BitmapFont

LCD = None
EPD = None

###############################################################################

def _init_screens():
    global LCD
    global EPD

    displayio.release_displays()
    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
    LCD = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)
    EPD = EPD_Class(d_spi)
    EPD._font = BitmapFont("font/font5x8.bin")

    return LCD, EPD

###############################################################################

def clear_lcd_screen(splash):
    for i in range(len(splash)):
        splash.pop()

###############################################################################

def clear_epd_screen():
  EPD.fill(0)

###############################################################################
if not (LCD and EPD):
  LCD, EPD = _init_screens()



