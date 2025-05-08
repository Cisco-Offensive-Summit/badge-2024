import adafruit_miniqr
import board
import displayio
import pwmio
import secrets
import os
from .log import log
from .wifi import WIFI

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

###############################################################################

def download_file(file:str, wifi:WIFI) -> bool:
    body = {
        'uniqueID' : secrets.UNIQUE_ID,
        "file": file
    }
    rsp = wifi.requests(method="GET",url=wifi.host + "badge/download", json=body, stream=True)               
    if rsp.status_code < 400:
        file = '/' + file  
        ensure_dirs_exist(file)
        with open(file, 'wb') as f:
            for chunk in rsp.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.sync()
        
        return True
    else:
        log('Error: unable to download file')
        log('Returned: ' + str(rsp.status_code))
      
        return False

###############################################################################

def ensure_dirs_exist(path):
    parts = path.strip("/").split("/")[:-1]
    current_path = ""
    for part in parts:
        current_path = current_path + "/" + part if current_path else part
        try:
            os.mkdir(current_path)
        except OSError:
            pass  # Directory exists