import board, busio, digitalio, time
from supervisor import ticks_ms
from math import floor

class EPD_DRIVER:

    spi = None
    EPD_CS = None
    EPD_RST = None
    EPD_BUSY = None
    EPD_DISCHARGE = None

    # Bitpacked display buffer
    prev_pixels = bytearray(b'\x00' * 2400)

    # frame repeat
    frame_repeat = 630

    # Set this to override frame repeat calculation
    frame_iters = None

    # TODO: Support other sizes
    def _get_height(self) -> int:
        return 96

    # TODO: Support other sizes
    def _get_bytes_per_line(self) -> int:
        return int(200 / 8)

    def set_frametime_by_temp(self, tmpr: int):
        self.frame_repeat = 630
        if   tmpr <= -10: self.frame_repeat *= 17
        elif tmpr <= -5:  self.frame_repeat *= 12
        elif tmpr <= 5:   self.frame_repeat *= 8
        elif tmpr <= 10:  self.frame_repeat *= 4
        elif tmpr <= 15:  self.frame_repeat *= 3
        elif tmpr <= 20:  self.frame_repeat *= 2
        elif tmpr <= 40:  self.frame_repeat *= 1
        else: self.frame_repeat = floor(self.frame_repeat * (7/10))


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

    def _power_on(self):
        self.EPD_CS.value = True
        self.EPD_RST.value = True
        self.EPD_DISCHARGE.value = False
        time.sleep(0.005)

        # Pulse Reset to power on COG driver
        self.EPD_RST.value = False
        time.sleep(0.005)
        self.EPD_RST.value = True
        time.sleep(0.005)

        while self.EPD_BUSY.value == True:
            time.sleep(0.001)
        
        # ID 0x12 corresponds with COG Gen 2
        eid = self._get_spi_id()
        if eid != b"\x12":
            self._power_off(cleanup=False)
            raise Exception("EINK display returned unexpected value for device ID.\nExpected: 0x12 | Returned {}".format(eid))
        
        self._spi_com_write(b"\x02", b"\x40") # Disable OE
        self._spi_com_write(b"\x0B", b"\x02") # Power saving mode
        
        # Write Channel select bytes from COG driver document
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
        
        self._power_off(cleanup=False)
        raise Exception("EINK display did not pass DC/DC check.")

    def _power_off(self, cleanup=True):
        if cleanup:
            # Write Nothing frame
            white_line = bytearray(b'\x00' * self._get_bytes_per_line())
            for y in range(self._get_height()):
                self._draw_line(y, white_line, 0, 0, 0)
            
            # Write special border byte
            self._draw_line(0, white_line, 0, 0, 170)

        self._spi_com_write(b'\x0B', b'\x00') # Undocumented
        self._spi_com_write(b'\x03', b'\x01') # Latch reset turn on
        self._spi_com_write(b'\x05', b'\x03') # Power off charge pump, Vcom off
        self._spi_com_write(b'\x05', b'\x01') # Power off charge pump negative voltage, VGL & VDL off, delay 300ms
        time.sleep(0.300);
        self._spi_com_write(b'\x04', b'\x80') # Discharge internal
        self._spi_com_write(b'\x05', b'\x00') # Power off charge pump positive voltage, VGH & VDH off
        self._spi_com_write(b'\x07', b'\x01') # Turn off osc

        self.EPD_RST.value = False
        self.EPD_CS.value = False
        self.EPD_CS.value = False
        
        self.EPD_DISCHARGE.value = True
        time.sleep(0.150)
        self.EPD_DISCHARGE.value = False

    # Lookup table
    def _mapping(self, mapping: int, input: int) -> int:
        return (((mapping) >> (((input) & 5) << 2 )) & 15)

    def _draw_line(self, row: int, pixels: bytearray, mwt: int, mbt: int, border: int):
        # Begin spi transmission command
        self._spi_write_raw(b'\x70', b'\x0A')
        
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False

        self.spi.write(b'\x72') # Begin 

        # Border byte
        border_byte = border.to_bytes(1, 'little')
        self.spi.write(border_byte)

        bytes_per_line = self._get_bytes_per_line()

        # Send even bytes first
        even_map = ((mwt << 2 | mwt) << 0) | ((mwt << 2 | mbt) <<  4) | ((mbt << 2 | mwt) << 16) | ((mbt << 2 | mbt) << 20)
        for x in range(bytes_per_line-1, -1, -1):
            p = pixels[x]
            b = ((self._mapping(even_map, p >> 4) << 4) | (self._mapping(even_map, p >> 0) << 0)).to_bytes(1, 'little')
            self.spi.write(b)

        # Send scan bytes
        for y in range(floor(96 / 4) - 1, -1, -1):
            if y == floor(row / 4):
                b = (3 << ((row % 4) * 2)).to_bytes(1, 'little')
                self.spi.write(b)
            else:
                self.spi.write(b'\x00')

        # Send odd bytes
        odd_map = ((mwt << 2 | mwt) <<  0) | ((mwt << 2 | mbt) << 16) | ((mbt << 2 | mwt) <<  4) | ((mbt << 2 | mbt) << 20)
        for x in range(0, bytes_per_line, 1):
            p = pixels[x]
            b = ((self._mapping(odd_map, p >> 5) << 0) | (self._mapping(odd_map, p >> 1) << 4)).to_bytes(1, 'little')
            self.spi.write(b)

        self.EPD_CS.value = True
        self.spi.unlock()

        self._spi_com_write(b'\x02', b'\x07')


    def _draw_frame(self, frame: bytearray, mwt: int, mbt: int, it: int):
        bytes_per_line = self._get_bytes_per_line()
        height = self._get_height()
        for i in range(it):
            for y in range(height):
                self._draw_line(y, frame[bytes_per_line*y:(bytes_per_line*y)+bytes_per_line], mwt, mbt, 0)
    

    def change_image(self, new_pixels: bytearray):
        if not isinstance(new_pixels, bytearray):
            raise TypeError
        if len(new_pixels) != 2400:
            raise TypeError

        self._power_on()

        # Step 1: Compensate
        iters = 0
        if self.frame_iters:
            iters = self.frame_iters
            self._draw_frame(self.prev_pixels, 3, 2, iters)
        else:
            start = ticks_ms()
            while True:
                self._draw_frame(self.prev_pixels, 3, 2, 1)
                iters += 1

                if ticks_ms() - start > self.frame_repeat:
                    break
        
        # Stage 2: White
        self._draw_frame(self.prev_pixels, 2, 0, iters)
        # Stage 3: Inverse
        self._draw_frame(new_pixels, 3, 0, iters)
        # Stage 4: Normal
        self._draw_frame(new_pixels, 2, 3, iters)
        
        self.prev_pixels = new_pixels

        self._power_off()

    


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

    bpl = driver._get_bytes_per_line()

    pixels = bytearray(b'\x00' * 2400)
    for y in range(20, 60, 1):
        for x in range(2, bpl-2, 1):
            pixels[(y*bpl)+x] = 255

    driver.change_image(pixels)

### Notes
## Official COG Driver pdf
# https://www.pervasivedisplays.com/wp-content/uploads/2023/02/4P018-00_04_G2_Aurora-Mb_COG_Driver_Interface_Timing_for_small-size_20231107.pdf
## Others code:
# https://github.com/nayuki/Pervasive-Displays-epaper-driver/blob/master/src/EpaperDriver.cpp
# https://github.com/adafruit/Adafruit_CircuitPython_ST7735R/blob/main/adafruit_st7735r.py
# https://github.com/peterhinch/micropython-epaper/tree/master
## Adafruit Docs
# https://docs.circuitpython.org/en/latest/shared-bindings/fourwire/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busdisplay/index.html
# https://docs.circuitpython.org/en/latest/shared-bindings/busio/#busio.SPI
# https://github.com/adafruit/circuitpython/issues/7560
