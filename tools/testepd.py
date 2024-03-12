import adafruit_imageload, io
import board, displayio, busio
from displayio import FourWire
import pdepd
import time
from supervisor import ticks_ms
from math import floor

def test():
	
	displayio.release_displays()
	d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
	
	epd = pdepd.EPD_DRIVER(d_spi)
	
	bmp, pal = adafruit_imageload.load('/img/epd_logo.bmp', bitmap=displayio.Bitmap, palette=displayio.Palette)
	
	bpl = epd.get_bytes_per_line()
	pixels = bytearray(b'\x00' * 2400)
	pixels_alt = bytearray(b'\x00' * 2400)
	for y in range(96):
	    for x in range(bpl):
	        for z in range(8):
	            val = 0
	            if bmp[(y*bmp.width)+(x*8)+z] == 0:
	                val = 1
	            pixels[(y*bpl)+x] |= (val << z)
	            if y > 82:
	                if val == 0:
	                    val = 1
	                else:
	                    val = 0
	            pixels_alt[(y*bpl)+x] |= (val << z)
	
	print("Full image redraw, slow mode")
	t1 = ticks_ms()
	epd.change_image(pixels)
	t2 = ticks_ms()
	print("Update time = {}ms\n\n".format(t2-t1))
	
	epd.enable_fast_mode()
	print("Full image redraw, fast mode")
	t1 = ticks_ms()
	epd.change_image(pixels)
	t2 = ticks_ms()
	print("Update time = {}ms\n\n".format(t2-t1))
	epd.disable_fast_mode()
	
	alt = False
	acc = []
	print("Update image timing test. Full image. No fast mode.")
	for _ in range(10):
	    if alt:
	        print('\tregular')
	        t1 = ticks_ms()
	        epd.update_image(pixels)
	        t2 = ticks_ms()
	        print("\tUpdate time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = False
	    else:
	        print('\talt')
	        t1 = ticks_ms()
	        epd.update_image(pixels_alt)
	        t2 = ticks_ms()
	        print("\tUpdate time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = True
	    time.sleep(0.01)
	
	s = 0
	for i in acc:
	    s += i
	
	print("Average time = {}ms\n\n".format(floor(s/len(acc))))


	alt = False
	acc = []
	print("Update image timing test. Full image. Fast mode.")
	epd.enable_fast_mode()
	for _ in range(10):
	    if alt:
	        print('\tregular')
	        t1 = ticks_ms()
	        epd.update_image(pixels)
	        t2 = ticks_ms()
	        print("\tUpdate time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = False
	    else:
	        print('\talt')
	        t1 = ticks_ms()
	        epd.update_image(pixels_alt)
	        t2 = ticks_ms()
	        print("\tUpdate time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = True
	    time.sleep(0.01)
	epd.disable_fast_mode()
	
	s = 0
	for i in acc:
	    s += i
	
	print("Average time = {}ms\n\n".format(floor(s/len(acc))))

	
	alt = False
	acc = []
	epd.enable_fast_mode()
	print("Update image timing test. Partial image .")
	for _ in range(10):
	    if alt:
	        print('\tregular')
	        t1 = ticks_ms()
	        epd.update_image_partial(pixels, range(83,96))
	        t2 = ticks_ms()
	        print("\tUpdate_time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = False
	    else:
	        print('\talt')
	        t1 = ticks_ms()
	        epd.update_image_partial(pixels_alt, range(83,96))
	        t2 = ticks_ms()
	        print("\tUpdate_time = {}ms".format(t2-t1))
	        acc.append(t2-t1)
	        alt = True
	    time.sleep(0.01)
	
	epd.disable_fast_mode()
	
	s = 0
	for i in acc:
	    s += i
	
	print("Average time = {}ms\n\n".format(floor(s/len(acc))))