import board, displayio, busio
try:
    from FourWire import fourwire
except ImportError:
    from displayio import FourWire
from adafruit_st7735r import ST7735R
from pdepd import EPD

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


if __name__ == "__main__":
    main()
