import board, time, keypad
import displayio, digitalio, terminalio
from microcontroller import nvm
from adafruit_display_text import label, wrap_text_to_pixels

from pdepd import EPD
from adafruit_st7735r import ST7735R
from utils import wrap_text_to_epd

class LCDTitle:
    def __init__(self):
        self.WRAP_WIDTH = 124
        self.group = displayio.Group()
        
        self.title_area = label.Label(terminalio.FONT)
        self.title_area.anchor_point = (0,0)
        self.title_area.anchored_position = (4, 16)

        # Title Scrolling behavior
        self.title_lines = 0
        self.title_wait = 200
        self.title_wait_acc = 0

        self.track_area = label.Label(terminalio.FONT)
        self.track_area.anchor_point = (0,0)
        self.track_area.anchored_position = (1,0)
        
        self.time_area = label.Label(terminalio.FONT)
        self.time_area.anchor_point = (0,0)
        self.time_area.anchored_position = (1, 0)
        self.time_area.background_color = 0xaaaaaa
        self.time_area.color = 0x111111

        self.group.append(self.title_area)
        self.group.append(self.time_area)
        self.group.append(self.track_area)


    def __del__(self) -> None:
        pass

    def get_group(self):
        return self.group

    def set_data(self, title: str, track: str, meta: int):
        wrapped_title = wrap_text_to_pixels(title, self.WRAP_WIDTH, terminalio.FONT)
        self.title_lines = len(wrapped_title)
        self.title_area.y = 16
        self.title_wait_acc = 0
        self.title_area.text = "\n".join(wrapped_title)

        month = f"{meta>>15:02d}"
        day = f"{(meta & 0x7fff)>>10:02d}"
        hour = f"{8+(((meta & 0x3ff)>>4)//4):02d}"
        minute = f"{(((meta & 0x3ff)>>4)%4)*15:02d}"

        date_text = f"         {month}-{day} {hour}:{minute} "

        if "Main" in track:
            self.track_area.background_color = 0x0000FF
            self.track_area.text = "Main"
        elif "Hardware" in track:
            self.track_area.background_color = 0xFF0000
            self.track_area.text = "Hardware"
        else:
            self.track_area.background_color = 0x00FF00
            self.track_area.color = 0x111111
            self.track_area.text = "?????"

        self.time_area.text = date_text

    def update(self):
        if self.title_lines > 7:
            if self.title_wait_acc > self.title_wait:
                ny = self.title_area.anchored_position[1] - 1
                self.title_area.anchored_position = (4, ny)
            elif self.title_wait_acc == 0:
                self.title_area.anchored_position = (4, 16)
            
            self.title_wait_acc += 1

            if self.title_area.anchored_position[1] <= ((self.title_lines - 7) * - 10) + 16 and self.title_wait_acc > 0:
                self.title_wait_acc = -1 * self.title_wait

class EPDDescription:
    def __init__(self):
        self.x = 2
        self.y = 10
        self.description_lines = []
        self.description_position = 0
        self.MAX_LINES = 10

    def set_data(self, epd: EPD, description: str):
        self.description_lines = wrap_text_to_epd(description, display_length=200-self.x)
        self.description_position = 0

        epd.fill(0)
        epd.fill_rect(0, 0, 200, 9, 1)
        epd.text("Up | Down   <Info>   Back | Exit", 1, 1, 0)
        epd.text('\n'.join(self.description_lines[self.description_position:self.MAX_LINES]), self.x, self.y, 1)

    def update(self, epd: EPD, scroll_up: bool) -> bool:
        if len(self.description_lines) < 10:
            return False
        
        np = 0

        # Scroll direction up
        if scroll_up:
            # Already at top
            if self.description_position == 0:
                return False
            np = max(0, self.description_position - self.MAX_LINES)
        # Scroll direction Down
        else:
            # Already at bottom
            if self.description_position + self.MAX_LINES >= len(self.description_lines):
                return False
            np = min(len(self.description_lines)-self.MAX_LINES, self.description_position + self.MAX_LINES)
        
        self.description_position = np

        epd.fill_rect(self.x, self.y, 200, 96 - self.y, 0)
        epd.text('\n'.join(self.description_lines[self.description_position:self.description_position+self.MAX_LINES]), self.x, self.y, 1)
        return True
        

class ScheduleApp:
    def __init__(self, lcd: ST7735R, epd: EPD):
        self.lcd = lcd
        self.epd = epd
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)

    def __del__(self) -> None:
        pass

    # Main entry
    def run(self):
        import adafruit_fakerequests
        schedule_json = adafruit_fakerequests.Fake_Requests("/old_sched.json").json()
        title = LCDTitle()
        desc = EPDDescription()
        
        title.set_data(schedule_json["tracks"][0]["talks"][1]["title"], schedule_json["tracks"][0]["name"], schedule_json["tracks"][0]["talks"][1]["meta"])
        self.lcd.show(title.get_group())

        desc.set_data(self.epd, schedule_json["tracks"][0]["talks"][1]["desc"])
        self.epd.draw()

        self.buttons.events.clear()
        while True:
            time.sleep(0.025)
            title.update()
            event = self.buttons.events.get()
            if event:
                if event.key_number == 3:
                    if desc.update(self.epd, True):
                        self.epd.draw()
                elif event.key_number == 2:
                    if desc.update(self.epd, False):
                        self.epd.draw()
                elif event.key_number == 0:
                    break


def test_app():
    import adafruit_fakerequests
    from utils import init_screens

    lcd, epd = init_screens()

    schedule_json = adafruit_fakerequests.Fake_Requests("/old_sched.json").json()