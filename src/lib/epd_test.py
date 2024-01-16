import board, busio, digitalio, time

class EPD_DRIVER:

    spi = None
    EPD_CS = None
    EPD_RST = None
    EPD_BUSY = None
    EPD_DISCHARGE = None

    def _spi_write_raw(self, b1, b2):
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False
        self.spi.write(b1)
        
        ret = bytearray(1)
        self.spi.write_readinto(b2, ret)

        self.EPD_CS.value = True
        self.spi.unlock()

        return ret


    def _spi_com_write(self, com, data):
        self._spi_write_raw(b'\x70', com)
        self._spi_write_raw(b'\x72', data)


    def _spi_com_read(self, com):
        self._spi_write_raw(b'\x70', com)
        return self._spi_write_raw(b'\x73', b'\x00')

    
    def _get_spi_id(self):
        return self._spi_write_raw(b'\x71', b'\x00')

    def __del__(self):
        spi = None
        EPD_CS = None
        EPD_RST = None
        EPD_BUSY = None
        EPD_DISCHARGE = None

    def __init__(self, spi) -> None:
        self.spi = spi
        self.EPD_CS = digitalio.DigitalInOut(board.EINK_CS)
        self.EPD_CS.direction = digitalio.Direction.OUTPUT
        self.EPD_RST = digitalio.DigitalInOut(board.EINK_RST)
        self.EPD_RST.direction = digitalio.Direction.OUTPUT
        self.EPD_BUSY = digitalio.DigitalInOut(board.EINK_BUSY)
        self.EPD_BUSY.direction = digitalio.Direction.INPUT
        self.EPD_DISCHARGE = digitalio.DigitalInOut(board.EINK_DISCHARGE)
        self.EPD_DISCHARGE.direction = digitalio.Direction.OUTPUT

        self.power_on()

    def power_on(self):
        self.EPD_CS.value = True
        self.EPD_RST.value = True
        self.EPD_DISCHARGE.value = False
        time.sleep(0.005)

        print("Pulsing RST pin")
        self.EPD_RST.value = False
        time.sleep(0.005)
        self.EPD_RST.value = True
        time.sleep(0.005)

        print("Waiting for BUSY pin to go low.")
        while self.EPD_BUSY.value == True:
            time.sleep(0.001)
        
        eid = self._get_spi_id()
        if eid != b"\x12":
            raise Exception("EINK display returned unexpected value for device ID.\nExpected: 0x12 | Returned {}".format(eid))
        
        self._spi_com_write(b"\x02", b"\x40") # Disable OE
        self._spi_com_write(b"\x0B", b"\x02") # Power saving mode
        
        # Writing a bunch of data here
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False
        self.spi.write(b"\x70\x01\x72\x00\x00\x00\x00\x01\xFF\xE0\x00") # Channel Select
        self.EPD_CS.value = True
        self.spi.unlock()
        
        self._spi_com_write(b"\x07", b"\xD1") # High power mode osc setting
        self._spi_com_write(b"\x08", b"\x02") # Power setting
        self._spi_com_write(b"\x09", b"\xC2") # Set Vcom level
        self._spi_com_write(b"\x04", b"\x03") # Power setting
        self._spi_com_write(b"\x03", b"\x01") # Driver latch on
        self._spi_com_write(b"\x03", b"\x00") # Driver latch off
        time.sleep(0.005)

        # According to spec we can retry this 4 times
        for i in range(4):
            self._spi_com_write(b"\x05", b"\x01") # Start charge pump positive voltage, VGH & VDH on, delay 150ms
            time.sleep(0.150)
            self._spi_com_write(b"\x05", b"\x03")  # Start charge pump negative voltage, VGL & VDL on, delay 90ms
            time.sleep(0.090)
            self._spi_com_write(b"\x05", b"\x0F")  # Set charge pump Vcom on, delay 40ms
            time.sleep(0.040)

            if (self._spi_com_read(b'\x0F')[0] & 64) != 0: # Check DC/DC
                self._spi_com_write(b'\x02', b'\x06')
                return
        
        raise Exception("EINK display did not pass DC/DC check.")

    def power_off(self):
        self._spi_com_write(b'\x0B', b'\x00') # Undocumented
        self._spi_com_write(b'\x03', b'\x01') # Latch reset turn on
        self._spi_com_write(b'\x05', b'\x03') # Power off charge pump, Vcom off
        self._spi_com_write(b'\x05', b'\x01') # Power off charge pump negative voltage, VGL & VDL off, delay 300ms
        time.sleep(0.300);
        self._spi_com_write(b'\x04', b'\x80') # Discharge internal
        self._spi_com_write(b'\x05', b'\x00') # Power off charge pump positive voltage, VGH & VDH off
        self._spi_com_write(b'\x07', b'\x01') # Turn off osc
    
    def mapping(self, m, i):
        return (((m) >> (((i) & 5) << 2)) & 15)

    def drawLine(self, row, pixels, mwt, mbt):
        self._spi_write_raw(b'\x70', b'\x0A')
        
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False

        self.spi.write(b'\x72') # Begin 
        self.spi.write(b'\x00') # Border

        bytes_per_line = int(200 / 8)

        even_map = (mwt << 2 | mwt) <<  0 | (mwt << 2 | mbt) <<  4 | (mbt << 2 | mwt) << 16 | (mbt << 2 | mbt) << 20
        for x in range(bytes_per_line-1, -1, -1):
            p = pixels[x]
            b = ((self.mapping(even_map, p >> 4) << 4) | (self.mapping(even_map, p >> 0) << 0)).to_bytes(1, 'little')
            self.spi.write(b)
        
        odd_map = (mwt << 2 | mwt) <<  0 | (mwt << 2 | mbt) << 16 | (mbt << 2 | mwt) <<  4 | (mbt << 2 | mbt) << 20
        for x in range(0, bytes_per_line, 1):
            p = pixels[x]
            b = ((self.mapping(odd_map, p >> 5) << 0) | (self.mapping(odd_map, p >> 1) << 4)).to_bytes(1, 'little')
            self.spi.write(b)
        
        self.EPD_CS.value = True
        self.spi.unlock()

        self._spi_com_write(b'\x02', b'\x07')

# Testing function
def test():
    import displayio
    import fourwire
    from adafruit_st7735r import ST7735R
    displayio.release_displays()
    
    spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    fw = fourwire.FourWire(spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)

    lcd = ST7735R(fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)

    driver = EPD_DRIVER(spi)
    solid_line = [255] * 200
    driver.drawLine(12, solid_line, 2, 3)
    driver.drawLine(12, solid_line, 2, 3)
    driver.drawLine(12, solid_line, 2, 3)
    driver.drawLine(13, solid_line, 2, 3)
    driver.drawLine(13, solid_line, 2, 3)
    driver.drawLine(13, solid_line, 2, 3)
    driver.drawLine(14, solid_line, 2, 3)
    driver.drawLine(14, solid_line, 2, 3)
    driver.drawLine(14, solid_line, 2, 3)
    driver.drawLine(15, solid_line, 2, 3)
    driver.drawLine(15, solid_line, 2, 3)
    driver.drawLine(15, solid_line, 2, 3)
    driver.drawLine(16, solid_line, 2, 3)
    driver.drawLine(16, solid_line, 2, 3)
    driver.drawLine(16, solid_line, 2, 3)
    driver.drawLine(17, solid_line, 2, 3)
    driver.drawLine(17, solid_line, 2, 3)
    driver.drawLine(17, solid_line, 2, 3)

### Notes
## Others code:
# https://github.com/nayuki/Pervasive-Displays-epaper-driver/blob/master/src/EpaperDriver.cpp
# https://github.com/adafruit/Adafruit_CircuitPython_ST7735R/blob/main/adafruit_st7735r.py
## Adafruit Docs
# https://docs.circuitpython.org/en/latest/shared-bindings/fourwire/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busdisplay/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busio/#busio.SPI
# https://github.com/adafruit/circuitpython/issues/7560
