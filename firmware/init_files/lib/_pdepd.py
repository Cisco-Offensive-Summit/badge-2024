import board, busio, digitalio, time
import os, struct
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

    # frame repeat default
    frame_repeat = 630

    # Set this to override frame repeat calculation
    frame_iters = None

    # Super fast update, keeps the display powered on at all times
    superfast = False

    # Destructor
    def __del__(self) -> None:
        if self.superfast:
            self._power_off()
        spi = spi.deinit()
        EPD_CS = None
        EPD_RST = None
        EPD_BUSY = None
        EPD_DISCHARGE = None

    # Init function
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

    # Return height of EPD
    # TODO: Support other sizes
    def get_height(self) -> int:
        return 96

    # Return width of EPD
    # TODO: Support other sizes
    def get_width(self) -> int:
        return 200

    # Return how many bytes are needed for a line
    def get_bytes_per_line(self) -> int:
        return int(self.get_width() / 8)

    # Set frametime by ambient temp
    def set_frametime_by_temp(self, tmpr: int) -> None:
        self.frame_repeat = 630
        if   tmpr <= -10: self.frame_repeat *= 17
        elif tmpr <= -5:  self.frame_repeat *= 12
        elif tmpr <= 5:   self.frame_repeat *= 8
        elif tmpr <= 10:  self.frame_repeat *= 4
        elif tmpr <= 15:  self.frame_repeat *= 3
        elif tmpr <= 20:  self.frame_repeat *= 2
        elif tmpr <= 40:  self.frame_repeat *= 1
        else: self.frame_repeat = floor(self.frame_repeat * (7/10))

    # Enable fast update by keeping CoG driver on at all times
    def enable_fast_mode(self) -> None:
        # Fast mode already enabled, return
        if self.superfast:
            return
        
        self._power_on()
        self.superfast = True
    
    # Disable fast update and power down CoG driver
    def disable_fast_mode(self) -> None:
        # Fast mode already disabled, return
        if not self.superfast:
            return 
        
        # Stops ghosting
        self._draw_frame(self.prev_pixels, 2, 3, 2)

        self._power_off()
        self.superfast = False


    # Write two raw byte array to EPD
    # bc should only ever be 1 byte, which should either be the CommandIndex (0x70) or CommandData (0x72)
    # bd is the data of the command:
    ## For CommandIndex (0x70) it should only be 1 byte long and contain the relevant command byte
    ## For CommandData (0x72) it can be many bytes
    def _spi_write_raw(self, bc: bytes, bd: bytes) -> None:
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False
        
        self.spi.write(bc)
        self.spi.write(bd)

        self.EPD_CS.value = True
        self.spi.unlock()

    # Write CommandIndex value pair, followed immediately by CommandData value pair
    def _spi_com_write(self, com: bytes, data:bytes) -> None:
        self._spi_write_raw(b'\x70', com)
        self._spi_write_raw(b'\x72', data)

    # Write CommandIndex value pair, followed immediately by the CommandRead (0x73) special byte 
    # CommandRead only supports returning 1 byte
    def _spi_com_read(self, com: bytes) -> bytes:
        self._spi_write_raw(b'\x70', com)
        
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False

        self.spi.write(b'\x73')
        ret = bytearray(b'\x00')
        self.spi.write_readinto(b'\x00', ret)

        self.EPD_CS.value = True
        self.spi.unlock()

        return ret

    # Write CommandID (0x71) to EPD and return the ID value retured
    def _get_spi_id(self) -> bytes:
        while not self.spi.try_lock():
            pass
        self.EPD_CS.value = False

        self.spi.write(b'\x71')
        ret = bytearray(b'\x00')
        self.spi.write_readinto(b'\x00', ret)

        self.EPD_CS.value = True
        self.spi.unlock()
        
        return ret

    # Powers EPD CoG driver
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
        # TODO: Support other sizes
        self._spi_com_write(b'\x01', b'\x00\x00\x00\x00\x01\xFF\xE0\x00')
        
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
        
        # Only runs if DC/DC check fails
        self._power_off(cleanup=False)
        raise Exception("EINK display did not pass DC/DC check.")

    # Gracefully power off EPD CoG Driver
    def _power_off(self, cleanup=True):
        # Optional clean of buffer memory
        if cleanup:
            self._clean_cog_buffer()

        self._spi_com_write(b'\x0B', b'\x00') # Undocumented
        self._spi_com_write(b'\x03', b'\x01') # Latch reset turn on
        self._spi_com_write(b'\x05', b'\x03') # Power off charge pump, Vcom off
        self._spi_com_write(b'\x05', b'\x01') # Power off charge pump negative voltage, VGL & VDL off, delay 300ms
        time.sleep(0.300);
        self._spi_com_write(b'\x04', b'\x80') # Discharge internal
        self._spi_com_write(b'\x05', b'\x00') # Power off charge pump positive voltage, VGH & VDH off
        self._spi_com_write(b'\x07', b'\x01') # Turn off osc
        #time.sleep(0.050)

        self.EPD_RST.value = False
        self.EPD_CS.value = False
        self.EPD_CS.value = False
        
        self.EPD_DISCHARGE.value = True
        time.sleep(0.150)
        self.EPD_DISCHARGE.value = False

    # Separated from cleanup below for fast update mode
    def _draw_dummy_line(self):
        white_line = bytearray(b'\x00' * self.get_bytes_per_line())
        self._draw_line(0, b'\x00' * self.get_bytes_per_line(), 0, 0, 0xAA)

    # TODO: Support other sizes
    def _clean_cog_buffer(self):
        # Write Nothing frame
        white_line = bytearray(b'\x00' * self.get_bytes_per_line())
        for y in range(self.get_height()):
            # Write white line, but map all values to (No Change dot (0x00 or 0x01))
            self._draw_line(y, white_line, 0, 0, 0)
        
        # Write special border byte
        self._draw_dummy_line()

    # Lookup table
    # Maps 3 bits `& 0x5(b101)` to 4 byte EPD dot representation of the two bits we care about
    # mapping should be all possible values of input (two bits) mapped to their corresponding 2 bit dot value each
    ## Dot values: black = b11, white = b10, NoChange = b01 OR b00
    def _mapping(self, mapping: int, input: int) -> int:
        return (((mapping) >> (((input) & 0x5) << 2 )) & 0xF)

    # draw a single line to EPD
    # mwt is what value of 2 bit dot a white pixel (0x0) should be mapped to
    # mbt is what value of 2 bit dot a black pixel (0x1) should be mapped to
    # border should be 0x00 most of the time, except when powering off CoG driver
    def _draw_line(self, row: int, pixels: bytearray, mwt: int, mbt: int, border: int) -> None:
        # 'transfer' is the data header + bitpacked data we send to display
        # less memory efficient but twice as fast as sending on the fly!
        transfer = bytearray()

        # Append data start byte
        #transfer.extend(b'\x72')

        # Border byte
        border_byte = border.to_bytes(1, 'little')
        transfer.extend(border_byte)

        bytes_per_line = self.get_bytes_per_line()

        # Even bytes first
        #          if both bits are white  | b1 is white & b2 is black| b1 is black & b2 is white| both bits are black
        even_map = ((mwt << 2 | mwt) << 0) | ((mwt << 2 | mbt) <<  4) | ((mbt << 2 | mwt) << 16) | ((mbt << 2 | mbt) << 20)
        for x in range(bytes_per_line-1, -1, -1):
            p = pixels[x]
            b = ((self._mapping(even_map, p >> 4) << 4) | (self._mapping(even_map, p >> 0) << 0)).to_bytes(1, 'little')
            transfer.extend(b)

        # Scan bytes
        for y in range(floor(96 / 4) - 1, -1, -1):
            if y == floor(row / 4):
                b = (3 << ((row % 4) * 2)).to_bytes(1, 'little')
                transfer.extend(b)
            else:
                transfer.extend(b'\x00')

        # Odd bytes
        odd_map = ((mwt << 2 | mwt) <<  0) | ((mwt << 2 | mbt) << 16) | ((mbt << 2 | mwt) <<  4) | ((mbt << 2 | mbt) << 20)
        for x in range(0, bytes_per_line, 1):
            p = pixels[x]
            b = ((self._mapping(odd_map, p >> 5) << 0) | (self._mapping(odd_map, p >> 1) << 4)).to_bytes(1, 'little')
            transfer.extend(b)

        # Send line to CoG driver buffer
        self._spi_com_write(b'\x0A', transfer)
        # Flush CoG buffer to display
        self._spi_com_write(b'\x02', b'\x07')

    def _update_line(self, row: int, pixels: bytearray, border: int) -> None:
        transfer = bytearray()

        # Border byte
        border_byte = border.to_bytes(1, 'little')
        transfer.extend(border_byte)

        # Even bytes
        for x in range(self.get_bytes_per_line()-1, -1, -1):
            a = self.prev_pixels[row*self.get_bytes_per_line() + x]
            b = pixels[x]
            c = ((((a ^ b) & 0x55) << 1) | (b & 0x55)).to_bytes(1, 'little')
            transfer.extend(c)
        
        # Scan bytes
        for y in range(floor(96 / 4) - 1, -1, -1):
            if y == floor(row / 4):
                b = (3 << ((row % 4) * 2)).to_bytes(1, 'little')
                transfer.extend(b)
            else:
                transfer.extend(b'\x00')

        # Odd bytes
        for x in range(0, self.get_bytes_per_line(), 1):
            a = self.prev_pixels[row*self.get_bytes_per_line()+x]
            b = pixels[x]
            c = ((a ^ b) & 0xAA) | ((b & 0xAA) >> 1)
            c = ((c & 0x33) << 2) | ((c >> 2) & 0x33)
            c = (((c & 0x0F) << 4) | ((c >> 4) & 0x0F)).to_bytes(1, 'little')
            transfer.extend(c)

        # Send line to CoG driver buffer
        self._spi_com_write(b'\x0A', transfer)
        # Flush CoG buffer to display
        self._spi_com_write(b'\x02', b'\x07')

    # Draw a frame to display 'it' number of times
    def _draw_frame(self, frame: bytearray, mwt: int, mbt: int, it: int) -> None:
        bpl = self.get_bytes_per_line()
        height = self.get_height()
        for i in range(it):
            for y in range(height):
                self._draw_line(y, frame[bpl*y:(bpl*y)+bpl], mwt, mbt, 0)
    
    # Change image to a completely new image
    # Much slower than update method, but stops ghosting effect
    ## Roughly 3 seconds per update at >20C ambient temp
    def change_image(self, new_pixels: bytearray) -> None:
        # Check if bitpacked pixels are what we expect them to be
        if not isinstance(new_pixels, bytearray):
            raise TypeError
        if len(new_pixels) != 2400:
            raise TypeError

        # Power on CoG driver
        if not self.superfast:
            self._power_on()

        # Step 1: Compensate
        ## Send negative of current image displayed to EPD
        iters = 0
        # If frame_iters is set, just use that
        if self.frame_iters:
            iters = self.frame_iters
            self._draw_frame(self.prev_pixels, 3, 2, iters)
        # Otherwise find how many iterations of drawing gets us to out frame_repeat number of ms
        else:
            start = ticks_ms()
            while True:
                self._draw_frame(self.prev_pixels, 3, 2, 1)
                iters += 1

                if ticks_ms() - start > self.frame_repeat:
                    break
        
        # Stage 2: White
        ## Send all white pixels
        self._draw_frame(self.prev_pixels, 2, 0, iters)
        # Stage 3: Inverse
        ## Send Negative of new image
        self._draw_frame(new_pixels, 3, 0, iters)
        # Stage 4: Normal
        ## Send new image
        self._draw_frame(new_pixels, 2, 3, iters)
        
        # Override stored previous image
        self.prev_pixels[:] = new_pixels

        # Power off CoG driver
        if not self.superfast:
            self._power_off()
        else:
            self._clean_cog_buffer()

    # Update whole image with new data, may cause ghosting if used too frequently
    def update_image(self, new_pixels: bytearray) -> None:
        # Check if bitpacked pixels are what we expect them to be
        if not isinstance(new_pixels, bytearray):
            raise TypeError
        if len(new_pixels) != 2400:
            raise TypeError

        if not self.superfast:
            self._power_on()

        # If frame_iters is set, just use that
        bpl = self.get_bytes_per_line()
        if self.frame_iters:
            for i in range(self.frame_iters):
                for y in range(self.get_height()):
                    #self._draw_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 2, 3, 0)
                    self._update_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 0)

        # Otherwise find how many iterations of drawing gets us to out frame_repeat number of ms
        else:
            start = ticks_ms()
            while True:
                for y in range(self.get_height()):
                    #self._draw_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 2, 3, 0)
                    self._update_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 0)

                if ticks_ms() - start > self.frame_repeat:
                    break

        # Override stored previous image
        self.prev_pixels[:] = new_pixels

        if not self.superfast:
            self._power_off()
        else:
            self._clean_cog_buffer()

    # Update image, but only lines specified (line_nums can be range as well)
    def update_image_partial(self, new_pixels: bytearray, line_nums: range):
        if not isinstance(new_pixels, bytearray):
            raise TypeError
        if len(new_pixels) != 2400:
            raise TypeError

        if not self.superfast:
            self._power_on()
        
        # If frame_iters is set, just use that
        bpl = self.get_bytes_per_line()
        if self.frame_iters:
            for i in range(self.frame_iters):
                for y in iter(line_nums):

                    # If line out of display bounds, ignore it
                    if y < 0 or y >= self.get_height():
                        continue
                    self._update_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 0)

        # Otherwise find how many iterations of drawing gets us to out frame_repeat number of ms
        else:
            start = ticks_ms()
            while True:
                for y in iter(line_nums):
                    if y < 0 or y >= self.get_height():
                        continue
                    self._update_line(y, new_pixels[bpl*y:(bpl*y)+bpl], 0)

                if ticks_ms() - start > self.frame_repeat:
                    break

        # Override stored previous image
        self.prev_pixels[:] = new_pixels

        if not self.superfast:
            self._power_off()
        else:
            self._draw_dummy_line()