import adafruit_requests as requests
import alarm
import board
import displayio
import json
import microcontroller
import secrets
import socketpool
import ssl
import supervisor
import terminalio
import wifi
from adafruit_display_text.label import Label
from sys import exit
from time import sleep
from badge.constants import *
from badge.neopixels import NP
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import clear_screen
from badge.screens import wrap_message
from badge.screens import set_background
from badge.screens import center_text_x_plane
from badge.screens import center_label_y_plane

supervisor.runtime.autoreload = False
###############################################################################
FONT = terminalio.FONT
EPD_H = EPD.height
EPD_W = EPD.width
LCD_H = LCD.height
LCD_W = LCD.width
splash = None
###############################################################################
SSID = secrets.WIFI_NETWORK
WIFI_PASSWORD = secrets.WIFI_PASS
session = None
###############################################################################
HOST = secrets.HOST_ADDRESS
HELLO_API = 'badge/hello'
URL = HOST + HELLO_API
METHOD = 'GET'
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
JSON = {
    'uniqueID' : secrets.UNIQUE_ID
}
hello_json = None
###############################################################################
L1 = Label(font=FONT,text="Connecting to WIFI",color=WHITE)
L1.y = L1.height // 2
L2 = Label(font=FONT,text="Creating session pool", color=WHITE)
L2.y = L2.height + (L2.height // 2)
L3 = Label(font=FONT,text="Requesting new code", color=WHITE)
L3.y = (L3.height * 2) + (L3.height // 2)
L4 = Label(font=FONT,text="S4 GET TAG", padding_top=2,padding_bottom=2,
  padding_right=2,padding_left=2, color=BLACK, background_color=YELLOW,
  label_direction = "TTB")
L4.y = 0
L4.x = 2
L5 = Label(font=FONT,text="S7   EXIT", padding_top=2,padding_bottom=2,
  padding_left=2, padding_right=2, color=BLACK, background_color=YELLOW,
  label_direction = "TTB")
L5.y = 2
L5.x = LCD.width - (L5.width +2) * 2
###############################################################################
# This sets pin S4 as the button that will wake the badge from deep sleep
S4_pin_alarm = alarm.pin.PinAlarm(pin=board.BTN4, value=False, pull=True)
S7_pin_alarm = alarm.pin.PinAlarm(pin=board.BTN1, value=False, pull=True)

###############################################################################

def connect_screen_splash():

  splash = displayio.Group()
  LCD.root_group = splash

  return splash

###############################################################################

def request_data(hello_json):
  global session

  clear_screen(LCD)
  splash = LCD.root_group
  NP[0] = GREEN
  NP.show()
  splash.append(L1)

  # connecting to the network
  wifi.radio.connect(SSID, WIFI_PASSWORD)
  NP[1] = GREEN
  NP.show()
  splash.append(L2)
  sleep(0.5)

  # Creating a socket pool and using that to create a session                                                                                         
  pool = socketpool.SocketPool(wifi.radio)
  if not session:
    session = requests.Session(pool, ssl.create_default_context())
  NP[2] = GREEN
  NP.show()
  splash.append(L3)
  sleep(0.5)

  # Attempting to get the name tag
  # Attempting to get a registration code
  if 'size' in hello_json.keys():
    JSON['size'] = hello_json['size']
  rsp = session.request(method=METHOD,url=URL,json=JSON,headers=HEADERS)
  # If the request was a sucsess, extract info
  if rsp.status_code == 200:
    NP[3] = GREEN
    sleep(0.5)
    NP.fill(OFF)
    rsp_body_json = rsp.json()
    rsp.close()

  # else the request failed, print error code, flash red lights and exit.
  else:
    status_code = rsp.status_code
    message = rsp.json()['message']
    epd_print_error(f'Error {status_code}: \n{message}')
    for i in range(3):
      NP.fill(RED)
      sleep(0.25)
      NP.fill(OFF)
      sleep(0.25)
    rsp.close()
    exit()

  return rsp_body_json

###############################################################################

def build_name_tag(hello_json):

  color = hello_json['color']
  bg_color = hello_json['background_color']
  name = hello_json['name']
  scale = hello_json['scale']

  set_background(EPD, bg_color)
  tag = center_text_x_plane(EPD,name,scale=scale,color=color)
  center_label_y_plane(EPD, tag)
  EPD.root_group.append(tag)
  EPD.refresh()

###############################################################################

def epd_print_error(message):

  set_background(EPD, BLACK)
  lb = wrap_message(EPD, message)
  EPD.root_group.append(lb)
  EPD.refresh()
  
###############################################################################

def read_json_file():
  # try to load any saved hello screen info.
  try:
    with open('hello.json', 'r') as j:
      hello_json = json.load(j)
  # if that file doesn't exist then just set the value to none.
  except OSError as e:
    hello_json = None

  return hello_json

###############################################################################

def set_default_background():
  hello = dict()
  hello['name']='nobody'
  hello['color']=0xffffff
  hello['background_color']=0x0
  hello['scale']=3
  build_name_tag(hello)

###############################################################################

def set_lcd_button_labels():
  splash = LCD.root_group

  splash.append(L4)
  splash.append(L5)

###############################################################################

def main():
  global splash

  # try to load any saved hello screen info.
  hello_json = read_json_file()

  # Create a root group for the LCD screen
  splash = connect_screen_splash()

  set_lcd_button_labels()

  # if there is saved hello screen info, load that.
  if hello_json:
    clear_screen(EPD)
    build_name_tag(hello_json)

  else:
    set_default_background()

  while True:
    triggered_alarm = alarm.light_sleep_until_alarms(S4_pin_alarm, S7_pin_alarm)
    if triggered_alarm.pin == S7_pin_alarm.pin:
      microcontroller.reset()
    hello_json = request_data(hello_json)
    with open('hello.json', 'w') as j:
      json.dump(hello_json, j)

    clear_screen(EPD)
    clear_screen(LCD)
    set_lcd_button_labels()
    build_name_tag(hello_json)
    triggered_alarm = alarm.light_sleep_until_alarms(S4_pin_alarm, S7_pin_alarm)


if __name__ == "__main__":
  main()
