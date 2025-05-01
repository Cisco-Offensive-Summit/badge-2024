import adafruit_requests as requests
import alarm
import board
import displayio
import microcontroller
import neopixel
import secrets
import socketpool
import ssl
import supervisor
import terminalio
#import wifi
from adafruit_display_text import wrap_text_to_lines
from adafruit_display_text.label import Label
from time import sleep
from badge.constants import *
from badge.neopixels import NP
from badge.screens import *
from badge.utils import gen_qr_code
from badge.wifi import WIFI
from badge.constants import BB_HEIGHT


w = WIFI()

supervisor.runtime.autoreload = False
###############################################################################
FONT = terminalio.FONT
EPD_H = EPD.height
EPD_W = EPD.width
LCD_H = LCD.height
LCD_W = LCD.width
splash = None
###############################################################################
#SSID = secrets.WIFI_NETWORK
#WIFI_PASSWORD = secrets.WIFI_PASS
###############################################################################
HOST = secrets.HOST_ADDRESS
REGISTRATION_API = 'badge/request_code'                                                                                                               
URL = HOST + REGISTRATION_API
METHOD = 'POST'
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
JSON = {
    'uniqueID' : secrets.UNIQUE_ID
}
###############################################################################
L1 = Label(font=FONT,text="Connecting to WIFI",color=WHITE)
L1.y = L1.height // 2
L2 = Label(font=FONT,text="Creating session pool", color=WHITE)
L2.y = L2.height + (L2.height // 2)
L3 = Label(font=FONT,text="Requesting new code", color=WHITE)
L3.y = (L3.height * 2) + (L3.height // 2)
###############################################################################
# This sets pin D11 as the button that will wake the badge from deep sleep
S4_pin_alarm = alarm.pin.PinAlarm(pin=board.BTN4, value=False, pull=True)
NP[0] = GREEN
NP.show()
splash = displayio.Group()
LCD.root_group = splash
splash.append(L1)

# connecting to the network
#wifi.radio.connect(SSID, WIFI_PASSWORD)
w.connect_wifi()
NP[1] = GREEN
NP.show()
splash.append(L2)
sleep(0.5)

# Creating a socket pool and using that to create a session                                                                                           
#pool = socketpool.SocketPool(wifi.radio)
#session = requests.Session(pool, ssl.create_default_context())
NP[2] = GREEN
NP.show()
splash.append(L3)
sleep(0.5)

# Attempting to get a registration code
#rsp = session.request(method=METHOD,url=URL,json=JSON,headers=HEADERS)
rsp = w.requests(method=METHOD,url=URL,json=JSON,headers=HEADERS)
clear_screen(LCD)
print(URL)
print(JSON)
print(rsp.status_code)

# If the request was a sucsess, extract info
if rsp.status_code == 200:
  code = rsp.json()['code']
  register_address = HOST + rsp.json()['address']
  message = rsp.json()['message']
  NP[3] = GREEN
  sleep(0.5)
  NP.fill(OFF)

# else the request failed, print error code, flash red lights and exit.
else:
  status_code = rsp.status_code
  message = rsp.json()['message']
  err = f'Error {status_code}: {message}'
  wrapped_err = "\n".join(wrap_text_to_lines(err, 19))
  err_label = Label(FONT, text=wrapped_err)
  err_label.x = 5
  err_label.y = 5
  clear_screen(LCD)
  splash.append(err_label)
  print(err)
  for i in range(3):
    NP.fill(RED)
    sleep(0.25)
    NP.fill(OFF)
    sleep(0.25)

  sleep(5)
  microcontroller.reset()

rsp.close()

full_code_url = register_address + '?code=' + code
# Create and display the QRCode
gen_qr_code(full_code_url, LCD)
# Create the label for the exit button
btn_text = "S4 = Exit"
btn_lbl = Label(font=terminalio.FONT,text=btn_text)
radius = 5
x = 2 + radius
y = EPD.height - 2 - radius - (btn_lbl.bounding_box[BB_HEIGHT]//2)
splash = round_button(btn_lbl, x, y, radius)
splash.append(center_text_y_plane(EPD, center_text_x_plane(EPD, code, scale=3)))
clear_screen(EPD)
EPD.root_group.append(splash)
EPD.refresh()



# text_width = EPD._font.width(btn_text)
# font_height = EPD._font.font_height
# EPD.fill(0)
# EPD.fill_rect(0, EPD_H - font_height - 10, text_width + 10, font_height + 10, 1)
# EPD.text(btn_text, 5, EPD_H - font_height - 5, 0)
# # Print the Register URL to the e-ink display
# EPD.text("If you can't scan the QR code,:",0,0,1)
# EPD.text("visit the badge website at:",0,font_height +2,1)
# EPD.text("badger.becomingahacker.com",0,(font_height +2)*2,1)
# EPD.text("and click the link 'Register'",0,(font_height +2)*3, 1)
# EPD.text("to use the code '" + code + "' to ",0,(font_height +2)*4, 1)
# EPD.text("create a new account.",0,(font_height +2)*5, 1)
# EPD.draw()


triggered_alarm = alarm.light_sleep_until_alarms(S4_pin_alarm)
if triggered_alarm.pin == S4_pin_alarm.pin:
  microcontroller.reset()
