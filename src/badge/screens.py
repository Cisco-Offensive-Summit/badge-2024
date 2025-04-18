import board
import busio
import aurora_epaper
import framebufferio
from adafruit_st7735r import ST7735R
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text.label import Label
from displayio import Bitmap
from displayio import FourWire
from displayio import Group
from displayio import Palette
from displayio import release_displays
from displayio import TileGrid
from terminalio import FONT
from traceback import format_exception, print_exception

from badge.constants import BLACK
from badge.constants import WHITE
from badge.constants import BB_WIDTH
from badge.constants import BB_HEIGHT
from badge.constants import EPD_WIDTH
from badge.constants import EPD_HEIGHT
from badge.constants import LCD_WIDTH
from badge.constants import LCD_HEIGHT

LCD = None
EPD = None

###############################################################################
# This function will initialize both the EPD screen as well as the LCD screen.
#   The dimensions for both screens must be in the config.py file. This allows 
#   for these screens to be swapped out for different size screens and the code 
#   all still work.
#
def _init_screens():
    global LCD
    global EPD

    release_displays()

    d_spi = busio.SPI(board.EINK_CLKS, board.EINK_MOSI, board.EINK_MISO)
    lcd_fw = FourWire(d_spi, command=board.TFT_DC, chip_select=board.TFT_CS, 
      reset=board.TFT_RST, baudrate=20000000)
    LCD = ST7735R(lcd_fw, width=LCD_WIDTH, height=LCD_HEIGHT, colstart=2, 
      rowstart=1, rotation=270)

    framebuf = aurora_epaper.AuroraMemoryFramebuffer(d_spi, board.EINK_CS, 
      board.EINK_RST, board.EINK_BUSY, board.EINK_DISCHARGE, EPD_WIDTH, EPD_HEIGHT)
    framebuf.free_bus = False

    EPD = framebufferio.FramebufferDisplay(framebuf, auto_refresh=False)

    return LCD, EPD

###############################################################################
# While it is just a easy and clean to do this manually, this function allows
#   for other users to understand what is happening when reading code in the 
#   apps.
#
def clear_screen(screen):
        screen.root_group = Group()

###############################################################################
# Returns a adafruit_display_text.label.Label with the text wrapped
#
# screen: The badge screen object either LCD or EPD. Used to gather dimensions
# message: This is the text that will be wrapped
# font: This is a font object from the fontio class. Default is terminalio.FONT
# x: This is the starting x location
# y: This is the starting y location.
# scale: This is the scaling of the font.
#
def wrap_message(screen, message, font=FONT, x=0, y=None, scale=1):
  
  check_width = ""
  will_fit = ""
  lb = Label(font=font, text=message, scale=scale)
  if not y:
    lb.y = (lb.bounding_box[BB_HEIGHT]*scale)//2
  else:
    lb.y = y
  lb.x = x
  words = message.split(" ")
  check_width = words[0]
  will_fit = check_width

  for word in words[1:]:
    check_width += " " + word
    lb.text = check_width
    if not (lb.bounding_box[BB_WIDTH]*scale) > screen.width:
      will_fit += " " + word
    else:
      will_fit += "\n" + word
      check_width = will_fit

  lb.text = will_fit
  return lb
  
###############################################################################
# This function returns Group that contains the text that it is passed inside 
#   of a rounded rectangle.  This group, once returned, would then need to be 
#   appended to either the LCD screen root group or the EPD screen root group
#
# label: The button will be built around this label. Must be of type 
#        adafruit_display_text.label.Label
# x: The left edge of the text (not of the button)
# y: The center of the text on the y plane
# fill: Hex encoded color that can fill the button. None means translucent
# stroke: The thickness of the button line.
# EXAMPLE:
#   lb = Label(font=FONT,text="s4 next")
#   splash = round_button(lb, 10, 15, 5)
#   LCD.root_group = splash
#
def round_button(label:Label, x, y, rad, color=WHITE, fill=None ,stroke=1):
  scale = label.scale
  label.color = color
  label.x = x
  label.y = y
  t_height = label.bounding_box[BB_HEIGHT] * scale
  t_width = label.bounding_box[BB_WIDTH] * scale
  total_width = t_width + (rad * 2)
  total_height = t_height + (rad * 2)
  rect_x = x - rad
  rect_y = y - ((t_height//2) + rad)
  
  rect = RoundRect(x=rect_x, y=rect_y, width=total_width, height=total_height, 
         r=rad, fill=fill, outline=color, stroke=stroke)

  splash = Group()
  splash.append(rect)
  splash.append(label)
  return splash

###############################################################################
# This function simply will print exceptions to the EPD screen.
#
def epd_print_exception(e:Exception):
  print_exception(e)
  lb = wrap_message(EPD,format_exception(e, limit=2)[0])
  EPD.root_group = lb
  EPD.refresh()

###############################################################################
# This function will return a basic Label object with the X set such that the
#   text will be centered in the screen that is passed to the function. Optionally 
#   the Y can also be passed to this function and it will be set also.  If left 
#   empty the Y will need to be set after the Label is returned.
#
# screen: The screen object. Must be either LCD or EPD
# text: The text to be centered on the screen
# y: The starting Y position for the text
# scale: This is the scaling of the font.
# color: 24 bit color. Either hex or int
#
def center_text_x_plane(screen, text_or_label, y=None, scale=1, color=WHITE):
    # If the input is a string, create a new Label
  if isinstance(text_or_label, str):
    lb = Label(font=FONT, text=text_or_label, scale=scale, color=color)
  elif isinstance(text_or_label, Label):
    lb = text_or_label
    # Ensure we respect the passed-in scale only if this is a new label
    scale = lb.scale
  else:
      raise TypeError("text_or_label must be a string or a Label object")

  # Set x position to center
  lb.x = (screen.width // 2) - ((lb.bounding_box[BB_WIDTH] * scale) // 2)
  if y:
    lb.y = y
  else:
    lb.y = (lb.bounding_box[BB_HEIGHT] * scale) //2

  return lb

###############################################################################
# This function will return a basic Label object with the Y set such that the
#   text will be centered in the screen that is passed to the function. Optionally 
#   the X can also be passed to this function and it will be set also.  If left 
#   empty the X will need to be set after the Label is returned.
#   of the screen
#
# screen: The screen object. Must be either LCD or EPD
# text: The text to be centered on the screen
# x: The starting X position for the text
# scale: This is the scaling of the font.
# color: 24 bit color. Either hex or int
#
def center_text_y_plane(screen, text_or_label, x=None, scale=1, color=WHITE):
  # If the input is a string, create a new Label
  if isinstance(text_or_label, str):
    lb = Label(font=FONT, text=text_or_label, scale=scale, color=color)
  elif isinstance(text_or_label, Label):
    lb = text_or_label
    # Use the scale of the existing label
    scale = lb.scale
  else:
    raise TypeError("text_or_label must be a string or a Label object")

  # Calculate glyph height using the font's bounding box
  glyph_height = lb._font.get_bounding_box()[1] * scale

  # Center vertically on the screen
  lb.y = (glyph_height // 2) + (screen.height // 2) - ((lb.bounding_box[BB_HEIGHT] * scale) // 2)

  # Set x position if provided
  if x is not None:
    lb.x = x

  return lb

###############################################################################
# This function will take a label that it is passed and set the Y starting point
#   for the text relative to the size of the screen. The scale for the text must
#   be set prior to calling this function.                                                                                                                
#
# screen: The screen object. Must be either LCD or EPD
# lb: label containing the text and scale.
#
def center_label_x_plane(screen, lb):
  lb.x = (screen.width // 2) - ((lb.bounding_box[BB_WIDTH] * lb.scale) // 2)

###############################################################################
# This function will take a label that it is passed and set the Y starting point
#   for the text relative to the size of the screen. The scale for the text must
#   be set prior to calling this function.
#
# screen: The screen object. Must be either LCD or EPD
# lb: label containing the text and scale.
#
def center_label_y_plane(screen, lb):
  glyph_height = lb._font.get_bounding_box()[1]*lb.scale
  lb.y = (glyph_height //2) + (screen.height // 2) - (lb.bounding_box[BB_HEIGHT]*lb.scale // 2)

###############################################################################
# This function will set the background color of the screen that is passed to 
#   it. This must be call first before anything else is added to the screen. If
#   not then the background color will overwrite anyother groups set for that 
#   screen.  You should note that the LCD screen will draw the color automaticly,
#   while the EPD screen will need EPD.refresh() to draw the screen.
#
# screen: Screen to set a backround color on. Either LCD or EPD
# color: 24 bit color. Either hex or int
def set_background(screen, color):
  group = Group()
  background = Bitmap(screen.width, screen.height, 1)
  palette1 = Palette(1)
  palette1[0] = color                                                                                                                                     
  tile_grid1 = TileGrid(background, pixel_shader=palette1)
  group.append(tile_grid1)
  screen.root_group = group

###############################################################################

if not (LCD and EPD):
  LCD, EPD = _init_screens()
