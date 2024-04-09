import board, displayio, busio
try:
    from FourWire import fourwire
except ImportError:
    from displayio import FourWire
from adafruit_st7735r import ST7735R
from pdepd import EPD
from adafruit_display_text import label, wrap_text_to_pixels
import time, terminalio

def main():
    import adafruit_imageload, io

    # Just in case...
    displayio.release_displays()
    
    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)

    lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)

    epd = EPD(d_spi)

    # Load and display logo
    epd.image('/img/epd_logo.bmp')
    epd.draw()

    group = displayio.Group()
    text_area = label.Label(terminalio.FONT, text='\n'.join(wrap_text_to_pixels("Please visit https://badger.becomingahacker.com/badge_info to update your badge", 126, terminalio.FONT)))
    text_area.anchor_point = (0,0)
    text_area.anchored_position = (2, 2)
    group.append(text_area)

    lcd.show(group)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
