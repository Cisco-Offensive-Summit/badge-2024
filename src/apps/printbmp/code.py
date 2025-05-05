import os, asyncio, supervisor, time
from displayio import Group, TileGrid, Bitmap, Palette
import terminalio
from adafruit_display_text.label import Label
import adafruit_imageload
from badge.fileops import is_file
from badge.screens import LCD, EPD, round_button, center_text_x_plane, wrap_message, clear_screen, epd_print_exception
from badge.neopixels import set_neopixels, neopixels_off
import badge.buttons
from badge.events import on
import badge.events as evt
from badge.constants import EPD_SMALL, BB_HEIGHT, BB_WIDTH
from badge.log import log

IMG_DIR = '/img'

class Exit(Exception):
    def __init__(self, message):
        self.message = message          
        super().__init__(message)
    def __str__(self):
        return self.message

#--- indicators when button press
@on(evt.BTN_C_PRESSED)
def on_c_pressed(e):
    set_neopixels(0xFF0000, 0xFF0000, 0xFF0000, 0xFF0000)

@on(evt.BTN_C_RELEASED)
def on_c_released(e):
    neopixels_off()

@on(evt.BTN_D_PRESSED)
def on_d_pressed(e):
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(evt.BTN_D_RELEASED)
def on_d_released(e):
    neopixels_off()

def get_img_list():
    img_list = []

    for inode in os.listdir(IMG_DIR):
        file_path = f"{IMG_DIR}/{inode}"
        if is_file(file_path):
            split = file_path.rsplit('.', 1)
            if len(split) < 2:
                continue
            if split[1] == "bmp":
                img_list.append(f"{inode}")

    return img_list

def epd_welcome():
    clear_screen(EPD)
    root = Group()

    if EPD_SMALL:
        text_group = Group()
        text_group.append(center_text_x_plane(EPD, "PrintBMP", scale=2))
        text_group.append(center_text_x_plane(EPD, "Select a bmp", y=28))
        text_group.append(center_text_x_plane(EPD, "from '/img'", y=38))
        text_group.append(center_text_x_plane(EPD, "bmp dim: 128x96x1", y=58))

        buttons_group = Group()
        radius = 3
        offset = 1
        up_l = Label(font=terminalio.FONT, text="UP ")
        down_l = Label(font=terminalio.FONT, text="DWN")
        exit_l = Label(font=terminalio.FONT, text="EXT")
        sel_l = Label(font=terminalio.FONT, text="SEL")

        def get_button_y(lbl):
            return EPD.height - radius - (lbl.bounding_box[BB_HEIGHT]//2) - offset
        
        buttons_group.append(round_button(up_l, radius + offset, get_button_y(up_l), radius))
        buttons_group.append(round_button(down_l, radius + offset + 34, get_button_y(down_l), radius))
        buttons_group.append(round_button(exit_l, radius + offset + 68, get_button_y(exit_l), radius))
        buttons_group.append(round_button(sel_l, radius + offset + 102, get_button_y(sel_l), radius))

        root.append(text_group)
        root.append(buttons_group)
    else:
        text_group = Group()
        text_group.append(center_text_x_plane(EPD, "PrintBMP", y=13, scale=3))
        text_group.append(center_text_x_plane(EPD, "Select an bmp from the '/img'", y=36))
        text_group.append(center_text_x_plane(EPD, "directory to display.", y=46))
        text_group.append(center_text_x_plane(EPD, "bmp dimensions: 200x96x1", y=63))

        buttons_group = Group()
        radius = 5
        offset = 1
        up_l = Label(font=terminalio.FONT, text="  UP  ")
        down_l = Label(font=terminalio.FONT, text=" Down ")
        exit_l = Label(font=terminalio.FONT, text=" Exit ")
        sel_l = Label(font=terminalio.FONT, text="Select")

        def get_button_y(lbl):
            return EPD.height - radius - (lbl.bounding_box[BB_HEIGHT]//2) - offset

        buttons_group.append(round_button(up_l, radius + offset, get_button_y(up_l), radius))
        buttons_group.append(round_button(down_l, radius + offset + 51, get_button_y(down_l), radius))
        buttons_group.append(round_button(exit_l, radius + offset + 102, get_button_y(exit_l), radius))
        buttons_group.append(round_button(sel_l, radius + offset + 153, get_button_y(sel_l), radius))
    
        root.append(text_group)
        root.append(buttons_group)

    EPD.root_group = root
    EPD.refresh()


def draw_bmp(file_name: str):
    clear_screen(EPD)
    root = Group()
    bmp, palette = adafruit_imageload.load(f"{IMG_DIR}/{file_name}", bitmap=Bitmap, palette=Palette)
    # Invert colors hack
    palette[0] = 0xFFFFFF
    palette[1] = 0x000000
    root.append(TileGrid(bmp, pixel_shader=palette))
    EPD.root_group = root
    EPD.refresh()
    

def lcd_welcome(bmp_list: list):
    text_areas = []
    group = Group()
    for i, f in enumerate(bmp_list):
        l = Label(terminalio.FONT)
        l.anchor_point = (0,0)
        l.anchored_position = (1,i*16)
        l.text = f
        group.append(l)
        text_areas.append(l)
    
    return group, text_areas

def set_selection(bmp_list: list, index: int):
    for i in bmp_list:
        i.background_color = 0x000000
        i.color = 0xFFFFFF
    
    bmp_list[index].background_color = 0xaaaaaa
    bmp_list[index].color = 0x111111

def scroll(bmp_list: list, up: bool):
    if up:
        for i in bmp_list:
            i.y -= 16
    else:
        for i in bmp_list:
            i.y += 16


async def main_loop():
    exit_app = False
    while not exit_app:
        epd_welcome()
        group, bmp_list = lcd_welcome(get_img_list())
        LCD.root_group = group
        set_selection(bmp_list, 0)

        loc_acc = 0
        file_acc = 0
        while True:
            e = await badge.buttons.any_button_downup()
            if e == evt.BTN_A_DOWNUP:
                if loc_acc == 0 and file_acc > 0:
                    scroll(bmp_list, False)
                loc_acc = 0 if loc_acc == 0 else loc_acc - 1
                file_acc = 0 if file_acc == 0 else file_acc - 1
                set_selection(bmp_list, file_acc)
            elif e == evt.BTN_B_DOWNUP:
                if loc_acc == 7 and file_acc < len(bmp_list) -1:
                    scroll(bmp_list, True)
                loc_acc = 7 if loc_acc == 7 else loc_acc + 1
                file_acc = len(bmp_list) - 1 if file_acc == len(bmp_list) - 1 else file_acc + 1
                set_selection(bmp_list, file_acc)
            elif e == evt.BTN_C_DOWNUP:
                exit_app = True
                break
            elif e == evt.BTN_D_DOWNUP:
                draw_bmp(bmp_list[file_acc].text)
            else:
                log("Unknown Button")
    
    raise Exit("Goodbye!")


async def main():
    neopixels_off()
    button_tasks = badge.buttons.all_tasks(interval=0.1)
    evt_tasks = evt.start_tasks()
    mainloop_task = asyncio.create_task(main_loop())
    all_tasks = [ mainloop_task ] + button_tasks + evt_tasks
    await asyncio.gather(*all_tasks)

supervisor.runtime.autoreload = False
try:
    asyncio.run(main())
except Exit as e:
    log(f"{e}")
except Exception as e:
    epd_print_exception(e)
    time.sleep(60)

supervisor.reload()