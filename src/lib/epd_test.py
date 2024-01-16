import board, busio, digitalio, time
import fourwire
import displayio


# com and data are of type 
def gen_spi_write_pair(com, data, delay=False):
    com_idx = b'\x70' + b"\x01" + com
    data_delay = bytearray(b'\x72' + (len(data)).to_bytes(1) + data)

    # Set delay bit and delay value
    if delay:
        data_delay[1] |= (1 << 7)
        data_delay += (delay).to_bytes(1)

    return com_idx + data_delay

# SPI FORM IS:
# \x70 + COMMAND_INDEX + \x72 + COMMAND_DATA
_INIT_SEQUENCE = bytearray(
    gen_spi_write_pair(b"\x02", b"\x40") + # Disable OE
    gen_spi_write_pair(b"\x0B", b"\x02") + # Power saving mode
    gen_spi_write_pair(b"\x01", b"\x00\x00\x00\x00\x01\xFF\xE0\x00") + # Channel Select
    gen_spi_write_pair(b"\x07", b"\xD1") + # High power mode osc setting
	gen_spi_write_pair(b"\x08", b"\x02") + # Power setting
	gen_spi_write_pair(b"\x09", b"\xC2") + # Set Vcom level
	gen_spi_write_pair(b"\x04", b"\x03") + # Power setting
	gen_spi_write_pair(b"\x03", b"\x01") + # Driver latch on
	gen_spi_write_pair(b"\x03", b"\x00") + # Driver latch off

    gen_spi_write_pair(b"\x05", b"\x01", delay=150) + # Start charge pump positive voltage, VGH & VDH on, delay 150ms
	gen_spi_write_pair(b"\x05", b"\x03", delay=90) + # Start charge pump negative voltage, VGL & VDL on, delay 90ms
    gen_spi_write_pair(b"\x05", b"\x0F", delay=40)   # Set charge pump Vcom on, delay 40ms
)

_STOP_SEQUENCE = bytearray(
    gen_spi_write_pair(b"\x0B", b"\x00") + # Undocumented
	gen_spi_write_pair(b"\x03", b"\x01") + # Latch reset turn on
	gen_spi_write_pair(b"\x05", b"\x03") + # Power off charge pump, Vcom off
	gen_spi_write_pair(b"\x05", b"\x01", delay=300) + # Power off charge pump negative voltage, VGL & VDL off, delay 300ms
	gen_spi_write_pair(b"\x04", b"\x80") + # Discharge internal
	gen_spi_write_pair(b"\x05", b"\x00") + # Power off charge pump positive voltage, VGH & VDH off
	gen_spi_write_pair(b"\x07", b"\x01")  # Turn off osc
)

#class EPD_DRIVER:
class EPD_DRIVER(displayio.EPaperDisplay):

    def __init__ (self) -> None:
        init_seq = _INIT_SEQUENCE
        
        spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
        fw = fourwire.FourWire(spi, command=None, chip_select=board.EINK_CS, reset=board.EINK_RST, baudrate=20000000)

        #spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
        #while not spi.try_lock():
        #    pass
        #spi.configure(baudrate=20000000, phase=0, polarity=0)
        #spi.unlock()
#
        #EPD_CS = digitalio.DigitalInOut(board.EINK_CS)
        #EPD_CS.direction = digitalio.Direction.OUTPUT
        #EPD_RST = digitalio.DigitalInOut(board.EINK_RST)
        #EPD_RST.direction = digitalio.Direction.OUTPUT
        #EPD_BUSY = digitalio.DigitalInOut(board.EINK_BUSY)
        #EPD_BUSY.direction = digitalio.Direction.INPUT
        #EPD_DISCHARGE = digitalio.DigitalInOut(board.EINK_DISCHARGE)
        #EPD_DISCHARGE.direction = digitalio.Direction.OUTPUT
#
        #EPD_CS.value = True
        #EPD_RST.value = True
        #EPD_DISCHARGE.value = False
        #time.sleep(0.005)
#
        #print("Pulsing RST pin")
        #EPD_RST.value = False
        #time.sleep(0.005)
        #EPD_RST.value = True
        #time.sleep(0.005)
#
        #print("Waiting for BUSY pin to go low.")
        #while EPD_BUSY.value == True:
        #    time.sleep(0.001)
#
        #EPD_CS.value = False
        #
        #print("Checking EPD ID, expected value is 0x12")
        #EPD_id = bytearray(1)
        #while not spi.try_lock():
        #    pass
        #spi.write(b'\x71')
        #spi.write_readinto(b'\x71\x00', EPD_id)
        #spi.unlock()
#
        #EPD_CS.value = False
#
        #if EPD_id != "\x12":
        #    print("INIT DID NOT RETURN EXPECTED ID, EXITING.")

        super().__init__(
            display_bus=fw,
            start_sequence=_INIT_SEQUENCE,
            stop_sequence=_STOP_SEQUENCE,
            width=200,
            height=96,
            ram_width=200,
            ram_height=96,
            colstart=0,
            rowstart=0,
            rotation=0,
        )


# Testing function
def test():
    import displayio
    from adafruit_st7735r import ST7735R
    displayio.release_displays()

    #spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
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
# https://github.com/adafruit/circuitpython/issues/7560
