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

class AppStore:
    def __init__(self, wifi):
        self._page = None
        self.LCD = LCD
        self.EPD = EPD
        self.app_list = []
        self.current_index = 0
        self.screen = Group()

        self.wifi = wifi
        self.page = 'list'
        self.details_options = ["Install", "Delete", "Info", "Back"]
        self.details_index = 0

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

    def draw_menu(self) -> None:
        clear_screen(self.LCD)
        if self.page == 'list':
            if not self.app_list:
                msg = "No apps found."
            else:
                msg = self.app_list[self.current_index]['appName']

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
            color = rrhc(20)
            app_btn = round_button(app_lb, app_lb.x, app_lb.y, 10, color=color, fill=None ,stroke=3)

            self.LCD.root_group.append(banner)
            self.LCD.root_group.append(app_btn)

        else: #self.page == 'details'
            self.draw_msg(self.app_list[self.current_index]['info'])            

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

    def fetch_apps(self):
        print("Fetching app list...")
        self.app_list = self.request_app_list()
        self.current_index = 0
        self.draw_menu()


    async def handle_buttons(self):
        while True:
            btn = await any_button_downup()
            if self.page == "list":

                # Exit store
                if btn == evt.BTN_A_DOWNUP:
                    log("Exit")
                    self.draw_msg("Exiting")
                    microcontroller.reset()

                # Go dwon an app
                elif btn == evt.BTN_B_DOWNUP:
                    log("Scroll Down")
                    self.current_index = (self.current_index - 1) % len(self.app_list)

                # Go up an app
                elif btn == evt.BTN_C_DOWNUP:
                    log("Scroll Up")
                    self.current_index = (self.current_index + 1) % len(self.app_list)

                # Select
                elif btn == evt.BTN_D_DOWNUP:
                    log("Select")
                    self.draw_msg("Gathering Details")
                    self.page = "details"
                

            elif self.page == "details":
                log("Page = details")

                # back
                if btn == evt.BTN_A_DOWNUP:
                    log("Back to list")
                    self.draw_msg("Back to list")
                    self.page = "list"

                # Delete app
                elif btn == evt.BTN_B_DOWNUP:
                    log("Delete app")
                    self.draw_msg("Deleting app")
                    try:
                        self.delete_selected_app()
                        self.page = "list"
                    except OSError as e:
                        log(f'Delete failed: App {self.app_list[self.current_index]['appName']} not found')
                    
                # Get details
                elif btn == evt.BTN_C_DOWNUP:
                    log("Does Nothing")

                # install
                elif btn == evt.BTN_D_DOWNUP:
                    log(f"Installing app {self.app_list[self.current_index]['appName']}")
                    self.draw_msg(f"Installing app {self.app_list[self.current_index]['appName']}")
                    self.install_selected_app()
                    self.page = "list"

            self.draw_menu()


    def install_selected_app(self):
        app = self.app_list[self.current_index]
        print(f"Installing {app["appName"]}...")
        files = self.get_app_files(app["appName"])
        self.download_app(files)
        print(f"{app["appName"]} installed.")

    def request_app_list(self):
        if wifi.connect_wifi():
            GET_APP_LIST = 'badge/list_apps'
            url = wifi.host + GET_APP_LIST
            method = 'GET'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            body = {
                'uniqueID' : secrets.UNIQUE_ID
            }
            try:
                rsp = wifi.requests(method=method, url=url, json=body, headers=headers)
                body = rsp.json()
            except (OSError, RuntimeError, ValueError) as e:
                print("General connection failure:", e)
            return body['apps']

        # Couldn't connect wifi
        else:
            log("Couldn't connect to wifi")


    def get_app_files(self, app_name:str):
        if wifi.connect_wifi():
            GET_APP = 'badge/get_app'
            url = wifi.host + GET_APP
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
                print("General connection failure:", e)
            return body['files']

        # Couldn't connect wifi
        else:
            log("Couldn't connect to wifi")

    def download_app(self, download_files:list):
        log(download_files)
        for file in download_files:
            log(file)
            if not download_file(file, wifi):
                log(f"Download failed {file}")
                return False
        
        return True

    def delete_selected_app(self, full_path=None):
        if not full_path:
            path = "/apps/" + self.app_list[self.current_index]["folderName"]
        else:
            path = full_path
        print(path)
        
        for entry in os.listdir(path):
            full_path = path + "/" + entry
            if os.stat(full_path)[0] & 0x4000:  # Directory flag
                self.delete_selected_app(full_path)
            else:
                os.remove(full_path)
        os.rmdir(path)

    def draw_list_EPD_screen(self):
        clear_screen(self.EPD)
        self.create_button_row(LIST_SCREEN_BUTTONS)
        page_title = "** Select an App **"
        pt_lb = Label(font=FONT, text=page_title)
        center_text_x_plane(self.EPD, pt_lb)
        self.EPD.root_group.append(pt_lb)
        self.EPD.refresh()
        log('draw_list_EPD_screen')

    def draw_app_EPD_screen(self):
        clear_screen(self.EPD)
        self.create_button_row(DET_SCREEN_BUTTONS)
        page_title = f"** {self.app_list[self.current_index]['appName']} **"
        pt_lb = wrap_message(self.EPD, message=page_title)
        center_text_x_plane(self.EPD, pt_lb)
        self.EPD.root_group.append(pt_lb)
        self.EPD.refresh()
        log("draw_app_EPD_screen")

    def print_app_details(self):
        log('print_app_details')
        pass

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


    async def run(self):
        button_tasks = all_tasks()
        evt_tasks = evt.start_tasks()
        self.fetch_apps()
        log("Apps Fetched")
        await self.handle_buttons()

def random_readable_hex_color(min_brightness=100):
    """Return a random color in 0xRRGGBB format, avoiding very dark colors."""
    r = random.randint(min_brightness, 255)
    g = random.randint(min_brightness, 255)
    b = random.randint(min_brightness, 255)
    return (r << 16) | (g << 8) | b

rrhc = random_readable_hex_color
store = None

async def main(wifi:WIFI):
    global store
    store = AppStore(wifi)
    await store.run()

try:
    asyncio.run(main(wifi))
except Exception as e:
    epd_print_exception(e)

# This should be called from the main badge entrypoint
# asyncio.run(main())
##################################################################################################
##################################################################################################
##################################################################################################
