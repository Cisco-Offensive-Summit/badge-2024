import board, displayio, busio
try:
    from FourWire import fourwire
except ImportError:
    from FourWire import displayio
from adafruit_st7735r import ST7735R
from pdepd import EPD_DRIVER

def main():
    import adafruit_imageload, io

    # Just in case...
    displayio.release_displays()
    
    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)

    lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)

    epd = EPD_DRIVER(d_spi)

    # Load and display logo
    bmp, pal = adafruit_imageload.load('/epd_logo.bmp', bitmap=displayio.Bitmap, palette=displayio.Palette)
    epd.display_2_color_bitmap('/epd_logo.bmp')



if __name__ == "__main__":
    main()
