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

# SPDX-FileCopyrightText: <text> 2018 Kattni Rembor, Melissa LeBlanc-Williams
# and Tony DiCola, for Adafruit Industries.
# Original file created by Damien P. George </text>
#
# SPDX-License-Identifier: MIT

# Modified and minified for Offensive Summit badges

# Currently only supported size is 200x96
# TODO: Implement other sizes later
class PDEPDFormat:
    """PDEPDFormat"""

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        """Set a given pixel to a color."""
        bytes_per_line = 200//8
        byte_pos = x % 8
        i = 0
        while x-8 >= 0:
            x -= 8
            i+=1
        val = 1 if color else 0
        index = (y*bytes_per_line) + i
        framebuf.buf[index] &= ~(1 << byte_pos)
        framebuf.buf[index] |= (val << byte_pos)

    @staticmethod
    def get_pixel(framebuf, x, y):
        """Get the color of a given pixel"""
        bytes_per_line = 200//8
        byte_pos = x % 8
        i = 0
        while x-8 >= 0:
            x -= 8
            i+=1
        index = (y*bytes_per_line) + i
        return (framebuf.buf[index] >> byte_pos) & 0b1

    @staticmethod
    def fill(framebuf, color):
        """completely fill/clear the buffer with a color"""
        if color:
            fill = 0xFF
        else:
            fill = 0x00
        for i in range(len(framebuf.buf)):  # pylint: disable=consider-using-enumerate
            framebuf.buf[i] = fill

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        """Draw a rectangle at the given location, size and color. The ``fill_rect`` method draws
        both the outline and interior."""
        # pylint: disable=too-many-arguments
        bytes_per_line = 200//8
        val = 1 if color else 0
        while height > 0:
            for w_w in range(width):
                cur_x = w_w + x
                byte_pos = cur_x % 8
                i = 0
                while cur_x-8 >= 0:
                    cur_x -= 8
                    i+=1
                index = (y*bytes_per_line) + i
                framebuf.buf[index] &= ~(1 << byte_pos)
                framebuf.buf[index] |= (val << byte_pos)
            y += 1
            height -= 1

class FrameBuffer:
    """FrameBuffer object.

    :param buf: An object with a buffer protocol which must be large enough to contain every
                pixel defined by the width, height and format of the FrameBuffer.
    :param width: The width of the FrameBuffer in pixel
    :param height: The height of the FrameBuffer in pixel
    :param buf_format: Specifies the type of pixel used in the FrameBuffer; permissible values
                        are listed under Constants below. These set the number of bits used to
                        encode a color value and the layout of these bits in ``buf``. Where a
                        color value c is passed to a method, c is  a small integer with an encoding
                        that is dependent on the format of the FrameBuffer.
    :param stride: The number of pixels between each horizontal line of pixels in the
                   FrameBuffer. This defaults to ``width`` but may need adjustments when
                   implementing a FrameBuffer within another larger FrameBuffer or screen. The
                   ``buf`` size must accommodate an increased step size.

    """

    def __init__(self, buf, width, height, stride=None):
        # pylint: disable=too-many-arguments
        self.buf = buf
        self.width = width
        self.height = height
        self.stride = stride
        self._font = None
        if self.stride is None:
            self.stride = width
        self.format = PDEPDFormat()
        self._rotation = 0

    @property
    def rotation(self):
        """The rotation setting of the display, can be one of (0, 1, 2, 3)"""
        return self._rotation

    @rotation.setter
    def rotation(self, val):
        if not val in (0, 1, 2, 3):
            raise RuntimeError("Bad rotation setting")
        self._rotation = val

    def fill(self, color):
        """Fill the entire FrameBuffer with the specified color."""
        self.format.fill(self, color)

    def fill_rect(self, x, y, width, height, color):
        """Draw a rectangle at the given location, size and color. The ``fill_rect`` method draws
        both the outline and interior."""
        # pylint: disable=too-many-arguments, too-many-boolean-expressions
        self.rect(x, y, width, height, color, fill=True)

    def pixel(self, x, y, color=None):
        """If ``color`` is not given, get the color value of the specified pixel. If ``color`` is
        given, set the specified pixel to the given color."""
        if self.rotation == 1:
            x, y = y, x
            x = self.width - x - 1
        if self.rotation == 2:
            x = self.width - x - 1
            y = self.height - y - 1
        if self.rotation == 3:
            x, y = y, x
            y = self.height - y - 1

        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        if color is None:
            return self.format.get_pixel(self, x, y)
        self.format.set_pixel(self, x, y, color)
        return None

    def hline(self, x, y, width, color):
        """Draw a horizontal line up to a given length."""
        self.rect(x, y, width, 1, color, fill=True)

    def vline(self, x, y, height, color):
        """Draw a vertical line up to a given length."""
        self.rect(x, y, 1, height, color, fill=True)
    def circle(self, center_x, center_y, radius, color):

        """Draw a circle at the given midpoint location, radius and color.
        The ```circle``` method draws only a 1 pixel outline."""
        x = radius - 1
        y = 0
        d_x = 1
        d_y = 1
        err = d_x - (radius << 1)
        while x >= y:
            self.pixel(center_x + x, center_y + y, color)
            self.pixel(center_x + y, center_y + x, color)
            self.pixel(center_x - y, center_y + x, color)
            self.pixel(center_x - x, center_y + y, color)
            self.pixel(center_x - x, center_y - y, color)
            self.pixel(center_x - y, center_y - x, color)
            self.pixel(center_x + y, center_y - x, color)
            self.pixel(center_x + x, center_y - y, color)
            if err <= 0:
                y += 1
                err += d_y
                d_y += 2
            if err > 0:
                x -= 1
                d_x += 2
                err += d_x - (radius << 1)

    def rect(self, x, y, width, height, color, *, fill=False):
        """Draw a rectangle at the given location, size and color. The ```rect``` method draws only
        a 1 pixel outline."""
        # pylint: disable=too-many-arguments
        if self.rotation == 1:
            x, y = y, x
            width, height = height, width
            x = self.width - x - width
        if self.rotation == 2:
            x = self.width - x - width
            y = self.height - y - height
        if self.rotation == 3:
            x, y = y, x
            width, height = height, width
            y = self.height - y - height

        # pylint: disable=too-many-boolean-expressions
        if (
            width < 1
            or height < 1
            or (x + width) <= 0
            or (y + height) <= 0
            or y >= self.height
            or x >= self.width
        ):
            return
        x_end = min(self.width - 1, x + width - 1)
        y_end = min(self.height - 1, y + height - 1)
        x = max(x, 0)
        y = max(y, 0)
        if fill:
            self.format.fill_rect(self, x, y, x_end - x + 1, y_end - y + 1, color)
        else:
            self.format.fill_rect(self, x, y, x_end - x + 1, 1, color)
            self.format.fill_rect(self, x, y, 1, y_end - y + 1, color)
            self.format.fill_rect(self, x, y_end, x_end - x + 1, 1, color)
            self.format.fill_rect(self, x_end, y, 1, y_end - y + 1, color)

    def line(self, x_0, y_0, x_1, y_1, color):
        # pylint: disable=too-many-arguments
        """Bresenham's line algorithm"""
        d_x = abs(x_1 - x_0)
        d_y = abs(y_1 - y_0)
        x, y = x_0, y_0
        s_x = -1 if x_0 > x_1 else 1
        s_y = -1 if y_0 > y_1 else 1
        if d_x > d_y:
            err = d_x / 2.0
            while x != x_1:
                self.pixel(x, y, color)
                err -= d_y
                if err < 0:
                    y += s_y
                    err += d_x
                x += s_x
        else:
            err = d_y / 2.0
            while y != y_1:
                self.pixel(x, y, color)
                err -= d_x
                if err < 0:
                    x += s_x
                    err += d_y
                y += s_y
        self.pixel(x, y, color)

    def blit(self):
        """blit is not yet implemented"""
        raise NotImplementedError()

    def scroll(self, delta_x, delta_y):
        """shifts framebuf in x and y direction"""
        if delta_x < 0:
            shift_x = 0
            xend = self.width + delta_x
            dt_x = 1
            x_rect = xend
        else:
            shift_x = self.width - 1
            xend = delta_x - 1
            dt_x = -1
            x_rect = 0
        if delta_y < 0:
            y = 0
            yend = self.height + delta_y
            dt_y = 1
            y_rect = yend
        else:
            y = self.height - 1
            yend = delta_y - 1
            dt_y = -1
            y_rect = 0
        while y != yend:
            x = shift_x
            while x != xend:
                self.format.set_pixel(
                    self, x, y, self.format.get_pixel(self, x - delta_x, y - delta_y)
                )
                x += dt_x
            y += dt_y

        self.fill_rect(x_rect, 0, abs(delta_x), self.height, 0)
        self.fill_rect(0, y_rect, self.width, abs(delta_y), 0)

    # pylint: disable=too-many-arguments
    def text(self, string, x, y, color, *, font_name="font/font5x8.bin", size=1):
        """Place text on the screen in variables sizes. Breaks on \n to next line.

        Does not break on line going off screen.
        """
        # determine our effective width/height, taking rotation into account
        frame_width = self.width
        frame_height = self.height
        if self.rotation in (1, 3):
            frame_width, frame_height = frame_height, frame_width

        for chunk in string.split("\n"):
            if not self._font or self._font.font_name != font_name:
                # load the font!
                self._font = BitmapFont(font_name)
            width = self._font.font_width
            height = self._font.font_height
            for i, char in enumerate(chunk):
                char_x = x + (i * (width + 1)) * size
                if (
                    char_x + (width * size) > 0
                    and char_x < frame_width
                    and y + (height * size) > 0
                    and y < frame_height
                ):
                    self._font.draw_char(char, char_x, y, self, color, size=size)
            y += height * size


# MicroPython basic bitmap font renderer.
# Author: Tony DiCola
# License: MIT License (https://opensource.org/licenses/MIT)
class BitmapFont:
    """A helper class to read binary font tiles and 'seek' through them as a
    file to display in a framebuffer. We use file access so we dont waste 1KB
    of RAM on a font!"""

    def __init__(self, font_name="font5x8.bin"):
        # Specify the drawing area width and height, and the pixel function to
        # call when drawing pixels (should take an x and y param at least).
        # Optionally specify font_name to override the font file to use (default
        # is font5x8.bin).  The font format is a binary file with the following
        # format:
        # - 1 unsigned byte: font character width in pixels
        # - 1 unsigned byte: font character height in pixels
        # - x bytes: font data, in ASCII order covering all 255 characters.
        #            Each character should have a byte for each pixel column of
        #            data (i.e. a 5x8 font has 5 bytes per character).
        self.font_name = font_name

        # Open the font file and grab the character width and height values.
        # Note that only fonts up to 8 pixels tall are currently supported.
        try:
            self._font = open(  # pylint: disable=consider-using-with
                self.font_name, "rb"
            )
            self.font_width, self.font_height = struct.unpack("BB", self._font.read(2))
            # simple font file validation check based on expected file size
            if 2 + 256 * self.font_width != os.stat(font_name)[6]:
                raise RuntimeError("Invalid font file: " + font_name)
        except OSError:
            print("Could not find font file", font_name)
            raise
        except OverflowError:
            # os.stat can throw this on boards without long int support
            # just hope the font file is valid and press on
            pass

    def deinit(self):
        """Close the font file as cleanup."""
        self._font.close()

    def __enter__(self):
        """Initialize/open the font file"""
        self.__init__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """cleanup on exit"""
        self.deinit()

    def draw_char(
        self, char, x, y, framebuffer, color, size=1
    ):  # pylint: disable=too-many-arguments
        """Draw one character at position (x,y) to a framebuffer in a given color"""
        size = max(size, 1)
        # Don't draw the character if it will be clipped off the visible area.
        # if x < -self.font_width or x >= framebuffer.width or \
        #   y < -self.font_height or y >= framebuffer.height:
        #    return
        # Go through each column of the character.
        for char_x in range(self.font_width):
            # Grab the byte for the current column of font data.
            self._font.seek(2 + (ord(char) * self.font_width) + char_x)
            try:
                line = struct.unpack("B", self._font.read(1))[0]
            except RuntimeError:
                continue  # maybe character isnt there? go to next
            # Go through each row in the column byte.
            for char_y in range(self.font_height):
                # Draw a pixel for each bit that's flipped on.
                if (line >> char_y) & 0x1:
                    framebuffer.fill_rect(
                        x + char_x * size, y + char_y * size, size, size, color
                    )

    def width(self, text):
        """Return the pixel width of the specified text message."""
        return len(text) * (self.font_width + 1)

class EPD(FrameBuffer):
    """FrameBuffer object for Pervasive Displays Epaper Module

    :param spi: SPI bus used to communicate with the EPD"""
    def __init__(self, spi) -> None:
        self.driver = EPD_DRIVER(spi)
        super().__init__(bytearray(b'\x00' * 2400), self.driver.get_width(), self.driver.get_height(), stride=None)

    def set_frametime_by_temp(self, tmpr: int) -> None:
        """Set approximate time of for display update via ambient temperature"""
        self.driver.set_frametime_by_temp(tmpr)

    def enable_fast_mode(self) -> None:
        """Enable an optional fast mode, may cause 'strangeness' with display"""
        self.driver.enable_fast_mode()

    def disable_fast_mode(self) -> None:
        """Disable optional fast mode"""
        self.driver.disable_fast_mode()

    def update(self) -> None:
        """Draw frame, may cause ghosting if used too frequently"""
        self.driver.update_image(self.buf)

    def update_partial(self, line_nums: range) -> None:
        """Update part of a frame, due to limitations of the display it must be a set of horizontal lines"""
        self.driver.update_image_partial(self.buf, line_nums)

    def draw(self) -> None:
        """Draw a frame, takes longer due to full EPD refresh"""
        self.driver.change_image(self.buf)

    def image(self, img_path: str) -> None:
        """Draw an bitmap image, must be 1 bit color"""
        import adafruit_imageload
        from displayio import Bitmap, Palette

        self.format.fill(self, 0)
        bmp, pal = adafruit_imageload.load(img_path, bitmap=Bitmap, palette=Palette)

        bpl = self.driver.get_bytes_per_line()
        for y in range(min(self.driver.get_height(), bmp.height)):
            i = -1
            for x in range(min(self.driver.get_width(), bmp.width)):
                if not bmp[x,y]:
                    self.format.set_pixel(self, x, y, 1)

    def pretty_print_buffer(self) -> None:
        """Prints what the buffer will look like in ascii text"""

        print(f"+{'-' * self.driver.get_width()}+")
        acc = [" "] * self.driver.get_width()
        for y in range(self.driver.get_height()):
            for x in range(self.driver.get_width()):
                acc[x] = "█" if self.format.get_pixel(self, x, y) else " "
            print(f"|{''.join(acc)}|")
            acc[:] = [" "] * self.driver.get_width()
        print(f"+{'-' * self.driver.get_width()}+")


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