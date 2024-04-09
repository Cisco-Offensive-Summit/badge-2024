import adafruit_requests as requests
import binascii
import socketpool
import ssl
import supervisor
import wifi
from badge.colors import *
from badge.neopixels import NP
from badge.screens import EPD, epd_wrap_message
from secrets import HOST_ADDRESS as HOST
from secrets import WIFI_NETWORK as SSID
from secrets import WIFI_PASS
from time import sleep


supervisor.runtime.autoreload = False
MAC_ADDRESS = binascii.hexlify(wifi.radio.mac_address).decode('utf-8')

TOKEN_API = 'badge/gen_token'
URL = HOST + TOKEN_API
METHOD = 'POST'
HEADERS = {                                                                                                                                           
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
JSON = {
    'mac_address' : MAC_ADDRESS
}

###############################################################################

def flash_red(count):
  for i in range(count):
    NP.fill(RED)
    sleep(0.25)
    NP.fill(OFF)
    sleep(0.25)

  NP.fill(RED)
  return

###############################################################################

def epd_error_message(message,count):

  flash_red(count)
  EPD.fill(0)
  EPD.text(epd_wrap_message(message),0,0,1,size=1)
  EPD.draw()
  return

###############################################################################

def connect_wifi():
  if wifi.radio.connected:
    return True
      
  # Try a few times
  for i in range(5):
    try:
      wifi.radio.connect(SSID, WIFI_PASS)
      return True
    except:
      None
      
  return False

###############################################################################

def get_token():
  NP[0] = GREEN
  NP.show()
  sleep(0.5)

  if not connect_wifi():
    epd_error_message("Could not connect to the wifi network.",1)
    return False

  NP[1] = GREEN
  NP.show()
  sleep(0.5)
  pool = socketpool.SocketPool(wifi.radio)
  session = requests.Session(pool, ssl.create_default_context())
  NP[2] = GREEN
  NP.show()
  sleep(0.5)
  rsp = session.request(method=METHOD,url=URL,json=JSON,headers=HEADERS)

  if rsp.status_code == 200:
    NP[3] = GREEN                                                                                                                                     
    sleep(0.5)
    NP.fill(OFF)
    rsp_body_json = rsp.json()
    rsp.close()
    try:
      with open("/secrets.py", "a") as fp:
        fp.write('\nUNIQUE_ID = \'' + rsp_body_json["uniqueID"] + '\'\n')
        fp.flush()
        return True

    except OSError as e:  # Typically when the filesystem isn't 
      epd_error_message("Drive not in a writable state", 5)
      return False
  # else the request failed, print error code, flash red lights and exit.
  else:
    status_code = rsp.status_code
    message = rsp.json()['message']
    epd_error_message(f'Error {status_code}: \n{message}',3 )
    rsp.close()
    return False


