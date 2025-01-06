import busio, displayio, board, aurora_epaper, framebufferio, terminalio
from adafruit_display_text import label

d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
t = aurora_epaper.AuroraMemoryFramebuffer(d_spi, board.EINK_CS, board.EINK_RST, board.EINK_BUSY, board.EINK_DISCHARGE, 128, 96)

d = framebufferio.FramebufferDisplay(t, auto_refresh=False)

# Set text, font, and color
text = "HELLO\nWORLD"
font = terminalio.FONT
color = 0xFFFFFF

# Create the text label
text_area = label.Label(font, text=text, color=color, scale=2)

# Set the location
text_area.x = 20
text_area.y = 20

# Show it
d.root_group = text_area

d.refresh()
