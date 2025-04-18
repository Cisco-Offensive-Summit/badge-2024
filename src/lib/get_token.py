import adafruit_requests as requests
import binascii
import socketpool
import ssl
import supervisor
import wifi
from badge.constants import *
from badge.neopixels import NP
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
    flash_red(1)
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
      flash_red(5)
      return False
  # else the request failed, print error code, flash red lights and exit.
  else:
    status_code = rsp.status_code
    message = rsp.json()['message']
    flash_red(3)
    rsp.close()
    return False


