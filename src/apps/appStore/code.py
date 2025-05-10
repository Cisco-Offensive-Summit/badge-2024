import asyncio
import microcontroller
import os
import random
import secrets
import badge.events as evt


from adafruit_display_text.label import Label
from badge.log import log
from badge.buttons import all_tasks
from badge.buttons import any_button_downup
from badge.constants import BB_HEIGHT
from badge.constants import BB_WIDTH
from badge.constants import SITE_BLUE
from badge.screens import LCD
from badge.screens import EPD
from badge.screens import center_text_x_plane
from badge.screens import center_text_y_plane
from badge.screens import clear_screen
from badge.screens import epd_print_exception
from badge.screens import round_button
from badge.screens import wrap_message
from badge.utils import download_file
from badge.wifi import WIFI
from displayio import Bitmap
from displayio import Group
from displayio import Palette
from displayio import TileGrid
from terminalio import FONT


wifi = WIFI()
LIST_SCREEN_BUTTONS = ['S4-EXIT','S5-Down','S6-Up','S7-Sel']
DET_SCREEN_BUTTONS = ['S4-Back','S5-Del','S6-    ','S7-Inst']

# AppStore class handles fetching, displaying, installing, and deleting apps
class AppStore:
    def __init__(self, wifi):
        self._page = None
        self.LCD = LCD
        self.EPD = EPD
        self.app_list = []
        self.current_index = 0
        self.screen = Group()

        self.wifi = wifi
        self.page = 'list'  # default screen is app list
        self.details_options = ["Install", "Delete", "Info", "Back"]
        self.details_index = 0

    # Property getter/setter for page transitions
    @property
    def page(self) -> str:
        return self._page

    @page.setter
    def page(self, p) -> None:
        if self._page != p:
            self._page = p
            if self._page == 'list':
                self.draw_list_EPD_screen()
            elif self._page == 'details':
                self.draw_app_EPD_screen()
            else:
                raise ValueError(f"Unknown value for page {self._page}")

    # Draw the menu based on the current page
    def draw_menu(self) -> None:
        clear_screen(self.LCD)
        if self.page == 'list':
            if not self.app_list:
                msg = "No apps found."
            else:
                msg = self.app_list[self.current_index]['appName']

            # Create banner UI
            banner = Group()
            banner_height = 15
            background = Bitmap(128, banner_height, 1)
            background_palette = Palette(1)
            background_palette[0] = SITE_BLUE
            background_tile_grid = TileGrid(background, pixel_shader=background_palette)
            os_lb = center_text_x_plane(LCD, "** OS 25 **", y=banner_height//2)
            banner.append(background_tile_grid)
            banner.append(os_lb)

            # Create button for app name
            app_lb = center_text_y_plane(LCD, center_text_x_plane(LCD, wrap_message(LCD, msg, scale=1)))
            color = rrhc(20)
            app_btn = round_button(app_lb, app_lb.x, app_lb.y, 10, color=color, fill=None ,stroke=3)

            self.LCD.root_group.append(banner)
            self.LCD.root_group.append(app_btn)

        else:  # 'details' page
            self.draw_msg(self.app_list[self.current_index]['info'])

    # Helper to show a message on the LCD screen
    def draw_msg(self, msg:str) -> None:
        clear_screen(self.LCD)

        banner = Group()
        banner_height = 15
        background = Bitmap(128, banner_height, 1)
        background_palette = Palette(1)
        background_palette[0] = SITE_BLUE
        background_tile_grid = TileGrid(background, pixel_shader=background_palette)
        os_lb = center_text_x_plane(LCD, "** OS 25 **", y=banner_height//2)
        banner.append(background_tile_grid)
        banner.append(os_lb)

        app_lb = center_text_y_plane(LCD, center_text_x_plane(LCD, wrap_message(LCD, msg, scale=1)))

        self.LCD.root_group.append(banner)
        self.LCD.root_group.append(app_lb)

    # Fetch list of apps from server
    def fetch_apps(self):
        self.app_list = self.request_app_list()
        self.current_index = 0
        self.draw_menu()

    # Coroutine to handle button presses
    async def handle_buttons(self):
        while True:
            btn = await any_button_downup()
            if self.page == "list":
                if btn == evt.BTN_A_DOWNUP:
                    self.draw_msg("Exiting")
                    microcontroller.reset()
                elif btn == evt.BTN_B_DOWNUP:
                    self.current_index = (self.current_index - 1) % len(self.app_list)
                elif btn == evt.BTN_C_DOWNUP:
                    self.current_index = (self.current_index + 1) % len(self.app_list)
                elif btn == evt.BTN_D_DOWNUP:
                    self.draw_msg("Gathering Details")
                    self.page = "details"

            elif self.page == "details":
                if btn == evt.BTN_A_DOWNUP:
                    self.draw_msg("Back to list")
                    self.page = "list"
                elif btn == evt.BTN_B_DOWNUP:
                    self.draw_msg("Deleting app")
                    try:
                        self.delete_selected_app()
                        self.page = "list"
                    except OSError as e:
                        log(f'Delete failed: App {self.app_list[self.current_index]['appName']} not found')
                elif btn == evt.BTN_C_DOWNUP:
                    pass
                elif btn == evt.BTN_D_DOWNUP:
                    log(f"Installing app {self.app_list[self.current_index]['appName']}")
                    self.draw_msg(f"Installing app {self.app_list[self.current_index]['appName']}")
                    self.install_selected_app()
                    self.page = "list"

            self.draw_menu()

    # Install the selected app
    def install_selected_app(self):
        app = self.app_list[self.current_index]
        files = self.get_app_files(app["appName"])
        self.download_app(files)

    # Request app list from server
    def request_app_list(self):
        if wifi.connect_wifi():
            url = wifi.host + 'badge/list_apps'
            method = 'GET'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            body = {
                'uniqueID': secrets.UNIQUE_ID
            }
            try:
                rsp = wifi.requests(method=method, url=url, json=body, headers=headers)
                body = rsp.json()
            except (OSError, RuntimeError, ValueError) as e:
                log("General connection failure:", e)
            return body['apps']
        else:
            log("Couldn't connect to wifi")

    # Request files for a selected app
    def get_app_files(self, app_name:str):
        if wifi.connect_wifi():
            url = wifi.host + 'badge/get_app'
            method = 'GET'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            body = {
                'app_name' : app_name,
                'uniqueID' : secrets.UNIQUE_ID
            }
            try:
                rsp = wifi.requests(method=method, url=url, json=body, headers=headers)
                body = rsp.json()
            except (OSError, RuntimeError, ValueError) as e:
                log("General connection failure:", e)
            return body['files']
        else:
            log("Couldn't connect to wifi")

    # Download app files
    def download_app(self, download_files:list):
        for file in download_files:
            if not download_file(file, wifi):
                log(f"Download failed {file}")
                return False
        return True

    # Delete selected app from local storage
    def delete_selected_app(self, full_path=None):
        if not full_path:
            path = "/apps/" + self.app_list[self.current_index]["folderName"]
        else:
            path = full_path
            
        for entry in os.listdir(path):
            full_path = path + "/" + entry
            if os.stat(full_path)[0] & 0x4000:  # Directory
                self.delete_selected_app(full_path)
            else:
                os.remove(full_path)
        os.rmdir(path)

    # Draw the EPD list screen
    def draw_list_EPD_screen(self):
        clear_screen(self.EPD)
        self.create_button_row(LIST_SCREEN_BUTTONS)
        pt_lb = Label(font=FONT, text="** Select an App **")
        center_text_x_plane(self.EPD, pt_lb)
        self.EPD.root_group.append(pt_lb)
        self.EPD.refresh()

    # Draw EPD screen for app details
    def draw_app_EPD_screen(self):
        clear_screen(self.EPD)
        self.create_button_row(DET_SCREEN_BUTTONS)
        page_title = f"** {self.app_list[self.current_index]['appName']} **"
        pt_lb = wrap_message(self.EPD, message=page_title)
        center_text_x_plane(self.EPD, pt_lb)
        self.EPD.root_group.append(pt_lb)
        self.EPD.refresh()

    # Draw a row of round buttons at the bottom of the screen
    def create_button_row(self, btns:list):
        radius = 5
        splash = Group()

        lb_0 = Label(font=FONT, text=btns[0])
        lb_1 = Label(font=FONT, text=btns[1])
        lb_2 = Label(font=FONT, text=btns[2])
        lb_3 = Label(font=FONT, text=btns[3])

        x_1 = 2 + radius
        y_1 = self.EPD.height - 2 - radius - (lb_1.bounding_box[BB_HEIGHT]//2)
        lb_2_x = self.EPD.width - 2 - radius - (lb_2.bounding_box[BB_WIDTH])
        lb_3_x = self.EPD.width - 2 - radius - (lb_3.bounding_box[BB_WIDTH])
        y_2 = self.EPD.height - 4 - radius*3 - ((lb_1.bounding_box[BB_HEIGHT]//2)*3)

        splash.append(round_button(lb_1, x_1, y_1, radius))
        splash.append(round_button(lb_2, lb_2_x, y_1, radius))
        splash.append(round_button(lb_0, x_1, y_2, radius))
        splash.append(round_button(lb_3, lb_3_x, y_2, radius))

        self.EPD.root_group.append(splash)

    # Run the AppStore interface and event loop
    async def run(self):
        button_tasks = all_tasks()
        evt_tasks = evt.start_tasks()
        self.fetch_apps()
        await self.handle_buttons()

# Return a random readable hex color (not too dark)
def random_readable_hex_color(min_brightness=100):
    r = random.randint(min_brightness, 255)
    g = random.randint(min_brightness, 255)
    b = random.randint(min_brightness, 255)
    return (r << 16) | (g << 8) | b

rrhc = random_readable_hex_color
store = None

# Entry point for async execution
async def main(wifi:WIFI):
    global store
    store = AppStore(wifi)
    await store.run()

# Run the main event loop
try:
    asyncio.run(main(wifi))
except Exception as e:
    epd_print_exception(e)
