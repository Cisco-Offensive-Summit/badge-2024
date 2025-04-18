import busio
import displayio
import board
import aurora_epaper
import framebufferio
import terminalio
from adafruit_display_text import label
from adafruit_st7735r import ST7735R
from displayio import FourWire

displayio.release_displays()

d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)

t = aurora_epaper.AuroraMemoryFramebuffer(d_spi, board.EINK_CS, board.EINK_RST, board.EINK_BUSY, board.EINK_DISCHARGE, 128, 96)
t.free_bus = False 

EPD = framebufferio.FramebufferDisplay(t, auto_refresh=False)

lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
LCD = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)

# Set text, font, and color
text = "HELLO\nWORLD"
font = terminalio.FONT
color = 0xFFFFFF

# Create the text label
text_area = label.Label(font, text=text, color=color, scale=2)
lcd_text_area = label.Label(font, text=text, color=color, scale=2)

# Set the location
text_area.x = 20
lcd_text_area.x = 20
text_area.y = 20
lcd_text_area.y = 20

# Show it
EPD.root_group = text_area
LCD.root_group = lcd_text_area
EPD.refresh()
LCD.refresh()
