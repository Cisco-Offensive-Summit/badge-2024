import wifi

from .log import log

CONNECT_WIFI = True


def connect_wifi():
    global CONNECT_WIFI
    try:
        from secrets import WIFI_NETWORK, WIFI_PASS
    except ImportError:
        log("Could not import secrets. skipping wifi setup.")
        CONNECT_WIFI = False

    if CONNECT_WIFI:
        ssid = WIFI_NETWORK
        password = WIFI_PASS

        try:
            wifi.radio.connect(ssid, password)
        except ConnectionError as exc:
            print(f"Wifi Connection error...{repr(exc)}")

    if wifi.radio.ipv4_address:
        log(f"Connected. ssid={ssid} ip={wifi.radio.ipv4_address}")

