import board
import busio
import displayio
from traceback import format_exception, print_exception
try:
    from FourWire import fourwire
except ImportError:
    from displayio import FourWire
from adafruit_st7735r import ST7735R
from pdepd import EPD as EPD_Class
from pdepd import BitmapFont

LCD = None
EPD = None

###############################################################################

def _init_screens():
    global LCD
    global EPD

    displayio.release_displays()
    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, reset=board.TFT_RST, baudrate=20000000)
    LCD = ST7735R(lcd_fw, width=128, height=128, colstart=2, rowstart=1, rotation=270)
    EPD = EPD_Class(d_spi)
    EPD._font = BitmapFont("font/font5x8.bin")

    return LCD, EPD

###############################################################################

def clear_lcd_screen(splash):
    for i in range(len(splash)):
        splash.pop()

###############################################################################

def clear_epd_screen():
  EPD.fill(0)

###############################################################################

def epd_wrap_message(message):
  lim = (EPD.width // (EPD._font.font_width + 1))  - 1

  new_msg = []
  for s in message.split("\n"):
    if s == "":
      new_msg += '\n'
    w=0 
    l = []
    for d in s.split():
      if w + len(d) + 1 <= lim:
        l.append(d)
        w += len(d) + 1 
      else:
        new_msg.append(" ".join(l))
        l = [d] 
        w = len(d)
    if (len(l)):
      new_msg.append(" ".join(l))

  return '\n'.join(new_msg)

###############################################################################

def epd_round_button(text, x, y, rad, color=1, scale=1):
  t_height = EPD._font.font_height * scale
  t_width = EPD._font.width(text) * scale
  total_width = t_width + (rad * 2)
  total_height = t_height + (rad * 2)
  
  EPD.circle(x,y,rad,color)
  EPD.circle(x,y+t_height,rad,color)
  EPD.circle(x+t_width,y,rad,color)
  EPD.circle(x+t_width,y+t_height,rad,color)
  EPD.rect(x,y-rad,t_width,total_height,not color,fill=True)
  EPD.rect(x-rad,y,total_width,t_height,not color,fill=True)
  EPD.vline(x-rad,y,t_height,color)
  EPD.vline(x+t_width+rad,y,t_height,color)
  EPD.hline(x,y-rad,t_width,color)
  EPD.hline(x,y+t_height+rad,t_width,color)
  EPD.text(text,x,y,color,size=scale)

###############################################################################

def epd_print_exception(e:Exception):
  print_exception(e)
  fmt = epd_wrap_message(format_exception(e, limit=2)[0])
  EPD.fill(0)
  EPD.text(fmt, 2, 2, 1)

###############################################################################

def epd_center_text(txt, y, scale=1, color=1):
    EPD.text(txt, (EPD.width - (EPD._font.width(txt) * scale)) // 2, y, color, size=scale)

###############################################################################
if not (LCD and EPD):
  LCD, EPD = _init_screens()
