import wifi

from .log import log

CONNECT_WIFI = False

def connect_wifi() -> bool:
    global CONNECT_WIFI
    try:
        from secrets import WIFI_NETWORK, WIFI_PASS
    except ImportError:
        log("Could not import secrets. skipping wifi setup.")
        return False

    if not CONNECT_WIFI:
        ssid = WIFI_NETWORK
        password = WIFI_PASS

        for _ in range(3):
            try:
                wifi.radio.connect(ssid, password)
                if wifi.radio.connected:
                    break
            except ConnectionError as exc:
                print(f"Wifi Connection error...{repr(exc)}")

    if wifi.radio.ipv4_address:
        log(f"Connected. ssid={ssid} ip={wifi.radio.ipv4_address}")
        CONNECT_WIFI = True
        return True
    else:
        CONNECT_WIFI = False
        return False