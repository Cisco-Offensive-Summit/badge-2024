import os, asyncio, supervisor, time
from displayio import Group
import terminalio
from adafruit_display_text import label, wrap_text_to_pixels
from badge.fileops import is_file
from badge.screens import LCD, EPD, epd_round_button, epd_center_text, epd_wrap_message
from badge.neopixels import set_neopixels, neopixels_off
import badge.buttons
from badge.events import on
import badge.events as evt

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
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(evt.BTN_C_RELEASED)
def on_c_released(e):
    neopixels_off()

@on(evt.BTN_D_PRESSED)
def on_c_pressed(e):
    set_neopixels(0xFF0000, 0xFF0000, 0xFF0000, 0xFF0000)

@on(evt.BTN_D_RELEASED)
def on_c_released(e):
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
    EPD.fill(0)
    epd_center_text("PrintBMP", 2, scale=3)
    epd_center_text("Select an bmp from the '/img'", 40)
    epd_center_text("directory to display.", 50)

    radius = 5
    epd_round_button("Up", 5 + radius, EPD.height - 5 - radius - EPD._font.font_height, radius)
    epd_round_button("Down", 5 + radius + 40, EPD.height - 5 - radius - EPD._font.font_height, radius)
    epd_round_button("Select", 5 + radius + 93, EPD.height - 5 - radius - EPD._font.font_height, radius)
    epd_round_button("Exit", EPD.width - 5 - radius - EPD._font.width("Exit"), EPD.height - 5 - radius - EPD._font.font_height, radius)

def draw_bmp(file_name: str):
    EPD.fill(0)
    EPD.image(f'{IMG_DIR}/{file_name}')

def lcd_welcome(bmp_list: list):
    text_areas = []
    group = Group()
    for i, f in enumerate(bmp_list):
        l = label.Label(terminalio.FONT)
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
        LCD.show(group)
        set_selection(bmp_list, 0)
        EPD.draw()

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
                draw_bmp(bmp_list[file_acc].text)
                EPD.draw()
            elif e == evt.BTN_D_DOWNUP:
                exit_app = True
                break
            else:
                print("Unknown Button")
    
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
    print(f"{e}")
except Exception as e:
    badge.screens.epd_print_exception(e)
    badge.screens.EPD.draw()
    time.sleep(60)

supervisor.reload()