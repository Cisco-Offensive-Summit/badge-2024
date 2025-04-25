# Imports for WiFi handling, HTTP requests, socket handling, screen rendering, and fonts
import adafruit_requests
import socketpool
import wifi
from adafruit_display_text.label import Label
from displayio import Group
from terminalio import FONT

# Custom modules for UI and logging
from badge.screens import LCD
from badge.screens import clear_screen
from badge.screens import center_text_y_plane
from badge.screens import center_text_x_plane
from badge.screens import wrap_message
from sys import exit
from .log import log

# Load secrets or fail early
try:
    from secrets import WIFI_NETWORK, WIFI_PASS, HOST_ADDRESS
except ImportError:
    log("Could not import secrets. skipping wifi setup.")
    exit()

# Custom exceptions for different failure scenarios
class WifiSSIDException(Exception): pass
class WifiPasswordException(Exception): pass
class WifiSessionException(Exception): pass

class WIFI:
    """Class to manage WiFi connection, session pool, and screen feedback."""
    def __init__(self, ssid=WIFI_NETWORK, passw=WIFI_PASS, host=HOST_ADDRESS, update=True) -> None:
        self.ssid = ssid                  # SSID of the network
        self.passw = passw                # Password of the network
        self.ipv4 = None                  # Store IPv4 once connected
        self.requests = None              # Will hold the requests.Session
        self.pool = None                  # Will hold the socketpool
        self.host = host                  # Destination host to connect to
        self._mac = wifi.radio.mac_address
        self._save_screen = None          # For screen restoration
        self._update = update             # Whether to display status messages

    def _start_session_pool(self):
        """Creates a socket pool and a new requests session."""
        try:
            if self._update:
                self._update_status("Creating new SocketPool")
            self.pool = socketpool.SocketPool(wifi.radio)
            self.get_new_session()
        except Exception as e:
            raise WifiSessionException(e)

    def _update_status(self, message:str) -> None:
        """Updates the screen with a status message."""
        if self._save_screen == None:
            self._save_screen = LCD.root_group

        lb = center_text_x_plane(LCD, wrap_message(LCD, message))
        clear_screen(LCD)
        LCD.root_group.append(lb)


    def _restore_screen(self) -> None:
        """Restores the screen to its previous state."""
        if self._save_screen != None:
            LCD.root_group = self._save_screen
            self._save_screen = None


    def connect_wifi(self) -> bool:
        """Attempts to connect to WiFi and start a session."""
        if not self.is_connected():
            if self._update:
                self._update_status("Connecting to Wifi")
            for _ in range(3):
                try:
                    wifi.radio.connect(self.ssid, self.passw)
                    if wifi.radio.connected:
                        break
                except ConnectionError as exc:
                    print(f"Wifi Connection error...{repr(exc)}")

        if wifi.radio.ipv4_address:
            log(f"Connected. ssid={self.ssid} ip={wifi.radio.ipv4_address}")
            self.ipv4 = wifi.radio.ipv4_address

            try:
                self._start_session_pool()
            except WifiSessionException as e:
                log(e)
                return False

            self._restore_screen()
            return True

        else:
            return False
        

    def disconnect_wifi(self) -> bool:
        """Disconnects the WiFi and disables the radio."""
        wifi.radio.enabled = False
        return wifi.radio.enabled

    def is_connected(self) -> bool:
        """Returns True if the radio is connected to WiFi."""
        return wifi.radio.connected

    def get_new_session(self) -> None:
        """Closes existing session and creates a new one."""
        try: 
            self.close_session()
            if self._update:
                self._update_status("Getting new requests session")
            # Create a requests object
            self.requests = adafruit_requests.Session(self.pool)
        except Exception as e:
            raise WifiSessionException(e)


    def close_session(self):
        """Close and delete the existing session, if any."""
        try:
            self.requests.close()
        except Exception:
            pass
        finally:
            # Always remove the reference
            del self.requests

    @property
    def mac(self) -> str:
        """Returns the MAC address as a human-readable string."""
        return ':'.join(f'{b:02X}' for b in self._mac)

    @property
    def ssid(self) -> str:
        """
        """
        return self._ssid

    @ssid.setter
    def ssid(self, ssid) -> None:
        """
        """
        if (len(ssid) > 0) and (isinstance(ssid,str)):
            self._ssid = ssid
            return
        
        if len(ssid) < 1:
            raise WifiSSIDException("WIFI_NETWORK is EMPTY")

        elif not isinstance(ssid,str):
            raise WifiSSIDException("WIFI ssid not of type \"str\"")

        else:
            raise WifiSSIDException("Unknown issues with wifi ssid")

    @property
    def passw(self) -> str:
        """
        """
        return self._passw

    @passw.setter
    def passw(self, passw) -> None:
        """
        """
        if (len(passw) > 0) and (isinstance(passw,str)):
            self._passw = passw
            return
        
        if len(passw) < 1:
            raise WifiPasswordException("WIFI_NETWORK is EMPTY")

        elif not isinstance(passw,str):
            raise WifiPasswordException("WIFI passw not of type \"str\"")

        else:
            raise WifiPasswordException("Unknown issues with wifi passw")

