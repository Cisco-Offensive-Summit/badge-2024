import board, busio, digitalio, time
import fourwire
import displayio

_INIT_SEQUENCE = bytearray(
    b"\x07\xD1" # Disable OE
    b"\x08\x02" # Power setting
    b"\x09\xC2" # Set Vcom Level
    b"\x04\x03" # Power setting
    b"\x03\x01" # Driver latch on
    b"\x03\x00" # Driver latch off
)

#class EPD_DRIVER(displayio.EPaperDisplay):
class EPD_DRIVER:

    def __init__ (self) -> None:
        init_seq = _INIT_SEQUENCE
        
        spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
        while not spi.try_lock():
            pass
        spi.configure(baudrate=20000000, phase=0, polarity=0)
        spi.unlock()

        EPD_CS = digitalio.DigitalInOut(board.EINK_CS)
        EPD_CS.direction = digitalio.Direction.OUTPUT
        EPD_RST = digitalio.DigitalInOut(board.EINK_RST)
        EPD_RST.direction = digitalio.Direction.OUTPUT
        EPD_BUSY = digitalio.DigitalInOut(board.EINK_BUSY)
        EPD_BUSY.direction = digitalio.Direction.INPUT
        EPD_DISCHARGE = digitalio.DigitalInOut(board.EINK_DISCHARGE)
        EPD_DISCHARGE.direction = digitalio.Direction.OUTPUT

        EPD_CS.value = True
        EPD_RST.value = True
        EPD_DISCHARGE.value = False
        time.sleep(0.005)

        print("Pulsing RST pin")
        EPD_RST.value = False
        time.sleep(0.005)
        EPD_RST.value = True
        time.sleep(0.005)

        print("Waiting for BUSY pin to go low.")
        while EPD_BUSY.value == True:
            time.sleep(0.001)

        EPD_CS.value = False
        
        print("Checking EPD ID, expected value is 0x12")
        EPD_id = bytearray(1)
        while not spi.try_lock():
            pass
        spi.write(b'\x71')
        spi.write_readinto(b'\x71\x00', EPD_id)
        spi.unlock()

        EPD_CS.value = False

        if EPD_id != "\x12":
            print("INIT DID NOT RETURN EXPECTED ID, EXITING.")

        #super().__init__(bus, init_seq, **kwargs)


# Testing function
def test():
    import displayio
    displayio.release_displays()

    print("Setting SPI")
    #spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    print("Setting Fourwire")
    #fw = fourwire.FourWire(spi, command=None, chip_select=board.EINK_CS, reset=board.EINK_RST, baudrate=24000000)
    
    driver = EPD_DRIVER()

### Notes
## Others code:
# https://github.com/nayuki/Pervasive-Displays-epaper-driver/blob/master/src/EpaperDriver.cpp
# https://github.com/adafruit/Adafruit_CircuitPython_ST7735R/blob/main/adafruit_st7735r.py
## Adafruit Docs
# https://docs.circuitpython.org/en/latest/shared-bindings/fourwire/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busdisplay/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busio/#busio.SPI

# EPD broke so I need a new one :(