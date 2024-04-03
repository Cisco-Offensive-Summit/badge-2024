import board
import displayio
import busio
import adafruit_miniqr
try:
    from FourWire import fourwire
except ImportError:
    from displayio import FourWire
from adafruit_st7735r import ST7735R
from pdepd import EPD
from pdepd import BitmapFont

###############################################################################

def init_screens():
    displayio.release_displays()
    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
    lcd = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)
    epd = EPD(d_spi)
    epd._font = BitmapFont("font/font5x8.bin")

    return lcd, epd

###############################################################################

def bitmap_QR(matrix):
    # monochome (2 color) palette
    BORDER_PIXELS = 2

    # bitmap the size of the screen, monochrome (2 colors)
    bitmap = displayio.Bitmap(
        matrix.width + 2 * BORDER_PIXELS, matrix.height + 2 * BORDER_PIXELS, 2
    )
    # raster the QR code
    for y in range(matrix.height):  # each scanline in the height
        for x in range(matrix.width):
            if matrix[x, y]:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 1
            else:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 0
    return bitmap

###############################################################################

def gen_qr_code(data, screen):
    qr = adafruit_miniqr.QRCode(qr_type=4, error_correct=adafruit_miniqr.L)
    qr.add_data(data.encode('utf-8'))
    qr.make()
    
    qr_bitmap = bitmap_QR(qr.matrix)
    # We'll draw with a classic black/white palette
    palette = displayio.Palette(2)
    palette[0] = 0xFFFFFF
    palette[1] = 0x000000
    # we'll scale the QR code as big as the display can handle
    scale = min(
        screen.width // qr_bitmap.width, screen.height // qr_bitmap.height
    )
    # then center it!
    pos_x = int(((screen.width / scale) - qr_bitmap.width) / 2)
    pos_y = int(((screen.height / scale) - qr_bitmap.height) / 2)
    qr_img = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=pos_x, y=pos_y)

    splash = displayio.Group(scale=scale)
    splash.append(qr_img)
    screen.root_group = splash

