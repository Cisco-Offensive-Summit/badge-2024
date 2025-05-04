import adafruit_miniqr
import board
import displayio
import pwmio
from badge.log import log

def bitmap_QR(matrix):
    # monochome (2 color) palette
    BORDER_PIXELS = 2

    # bitmap the size of the screen, monochrome (2 colors)
    bitmap = displayio.Bitmap(
        matrix.width + 2 * BORDER_PIXELS, matrix.height + 2 * BORDER_PIXELS, 2
    )
    # raster the QR code
    for y in range(matrix.height):  # each scanline in the height
        for x in range(matrix.width):
            if matrix[x, y]:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 1
            else:
                bitmap[x + BORDER_PIXELS, y + BORDER_PIXELS] = 0
    return bitmap

###############################################################################

def gen_qr_code(data, screen):
    qr = adafruit_miniqr.QRCode(qr_type=4, error_correct=adafruit_miniqr.L)
    qr.add_data(data.encode('utf-8'))
    qr.make()
    
    qr_bitmap = bitmap_QR(qr.matrix)
    # We'll draw with a classic black/white palette
    palette = displayio.Palette(2)
    palette[0] = 0xFFFFFF
    palette[1] = 0x000000
    # we'll scale the QR code as big as the display can handle
    scale = min(
        screen.width // qr_bitmap.width, screen.height // qr_bitmap.height
    )
    # then center it!
    pos_x = int(((screen.width / scale) - qr_bitmap.width) / 2)
    pos_y = int(((screen.height / scale) - qr_bitmap.height) / 2)
    qr_img = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=pos_x, y=pos_y)

    splash = displayio.Group(scale=scale)
    splash.append(qr_img)
    screen.root_group = splash

###############################################################################

def list_pwm_pins():
  for pin_name in dir(board):
      pin = getattr(board, pin_name)
      try:
          p = pwmio.PWMOut(pin)
          p.deinit()
          log("PWM on:", pin_name)
      except ValueError:
          log("No PWM on:", pin_name)
      except RuntimeError:
          log("Timers in use:", pin_name)
      except TypeError:
          pass
