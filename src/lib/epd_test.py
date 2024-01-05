import board, busio, digitalio
import fourwire
import busdisplay

_INIT_SEQUENCE = bytearray(
    b"\x07\xD1" # Disable OE
    b"\x08\x02" # Power setting
    b"\x09\xC2" # Set Vcom Level
    b"\x04\x03" # Power setting
    b"\x03\x01" # Driver latch on
    b"\x03\x00" # Driver latch off
)

class EPD_DRIVER(busdisplay.BusDisplay):

    def __init__ (self, bus: FourWire, **kwargs: Any):
        init_seq = _INIT_SEQUENCE
        super().__init__(bus, init_seq, **kwargs)


# Testing function
def test():
    import displayio
    displayio.release_displays()

    print("Setting SPI")
    spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    print("Setting Fourwire")
    fw = fourwire.FourWire(spi, command=None, chip_select=board.EINK_CS, reset=board.EINK_RST, baudrate=24000000)

### Notes
## Others code:
# https://github.com/nayuki/Pervasive-Displays-epaper-driver/blob/master/src/EpaperDriver.cpp
# https://github.com/adafruit/Adafruit_CircuitPython_ST7735R/blob/main/adafruit_st7735r.py
## Adafruit Docs
# https://docs.circuitpython.org/en/latest/shared-bindings/fourwire/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busdisplay/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busio/#busio.SPI

# EPD broke so I need a new one :(