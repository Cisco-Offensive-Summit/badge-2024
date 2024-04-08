import board, time, keypad
import displayio, digitalio, terminalio
from microcontroller import nvm
from adafruit_display_text import label, wrap_text_to_pixels
from adafruit_display_text.scrolling_label import ScrollingLabel

from pdepd import EPD
from adafruit_st7735r import ST7735R
from utils import wrap_text_to_epd

def meta_date(meta: int) -> str:
    month = f"{meta>>15:02d}"
    day = f"{(meta & 0x7fff)>>10:02d}"
    hour = f"{8+(((meta & 0x3ff)>>4)//4):02d}"
    minute = f"{(((meta & 0x3ff)>>4)%4)*15:02d}"

    return f"{month}-{day} {hour}:{minute}"


class InputAck:
    def __init__(self):
        self.group = displayio.Group()
        
        self.inputack_area = label.Label(terminalio.FONT, text="Input Recieved")
        self.inputack_area.anchor_point = (0.5,0.5)
        self.inputack_area.anchored_position = (64, 64)
        self.inputack_area.color = 0x111111
        self.inputack_area.background_color = 0x00FF00
        
        self.group.append(self.inputack_area)

    def get_group(self):
        return self.group

class LCDTalksList:
    def __init__(self, talks):
        self.talks = talks
        self.talk_index = 0
        self.selection_index = 0

        self.group = displayio.Group()
        
        self.track_area = label.Label(terminalio.FONT)
        self.track_area.anchor_point = (0,0)
        self.track_area.anchored_position = (1,0)
        
        self.time_area = label.Label(terminalio.FONT)
        self.time_area.anchor_point = (0,0)
        self.time_area.anchored_position = (1, 0)
        self.time_area.background_color = 0xaaaaaa
        self.time_area.color = 0x111111

        self.selection_area = []
        self.selection_area_group = displayio.Group()
        for i in range(0,7):
            scroll = ScrollingLabel(terminalio.FONT, text="Placeholder", max_characters=20, animate_time=0.5)
            scroll.anchor_point = (0, 0)
            scroll.anchored_position = (2, 16*(i+1))
            scroll.color = 0xFFFFFF
            scroll.background_color = 0x000000
            if i < len(talks):
                scroll.text = talks[i]['title']
                scroll.full_text = talks[i]['title']
            self.selection_area.append(scroll)
            self.selection_area_group.append(scroll)
    
        self._set_selection(0)

        self.group.append(self.selection_area_group)
        self.group.append(self.time_area)
        self.group.append(self.track_area)

    def get_group(self):
        return self.group

    def _set_selection(self, new_selection:int):
        self.selection_area[self.selection_index].color = 0xFFFFFF
        self.selection_area[self.selection_index].background_color = 0x000000

        self.selection_area[new_selection].color = 0x111111
        self.selection_area[new_selection].background_color = 0xaaaaaa

        self.selection_index = new_selection

        track = self.talks[self.talk_index]["track"]
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

        self.time_area.text = f"         {meta_date(self.talks[self.talk_index]["meta"])} "

    def _scroll_text(self, scroll_up: bool):
        if scroll_up:
            for i in range(6,0,-1):
                self.selection_area[i].text = self.selection_area[i-1].text
                self.selection_area[i].full_text = self.selection_area[i-1].full_text
            self.selection_area[0].text = self.talks[self.talk_index]["title"]
            self.selection_area[0].full_text = self.talks[self.talk_index]["title"]
        else:
            for i in range(1,7):
                self.selection_area[i-1].text = self.selection_area[i].text
                self.selection_area[i-1].full_text = self.selection_area[i].full_text
            self.selection_area[6].text = self.talks[self.talk_index]["title"]
            self.selection_area[6].full_text = self.talks[self.talk_index]["title"]


    def update(self):
        self.selection_area[self.selection_index].update()

    def input(self, scroll_up: bool):
        if scroll_up:
            # Already at top
            if self.talk_index == 0:
                return
            self.talk_index -= 1
            if self.selection_index == 0:
                self._scroll_text(scroll_up)
            self._set_selection(0 if self.selection_index - 1 < 0 else self.selection_index - 1)
        else:
            # Already at bottom
            if self.talk_index == len(self.talks)-1:
                return
            self.talk_index += 1
            if self.selection_index == 6:
                self._scroll_text(scroll_up)
            self._set_selection(6 if self.selection_index + 1 > 6 else self.selection_index + 1)

    def get_talk(self):
        return self.talks[self.talk_index]

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

    def get_group(self):
        return self.group

    def set_data(self, title: str, track: str, meta: int):
        wrapped_title = wrap_text_to_pixels(title, self.WRAP_WIDTH, terminalio.FONT)
        self.title_lines = len(wrapped_title)
        self.title_area.y = 16
        self.title_wait_acc = 0
        self.title_area.text = "\n".join(wrapped_title)
        date_text = f"         {meta_date(meta)} "

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

            if self.title_area.anchored_position[1] <= ((self.title_lines - 7) * -12) + 16 and self.title_wait_acc > 0:
                self.title_wait_acc = -1 * self.title_wait

class EPDTalks:
    def __init__(self):
        pass
    
    def set_data(self, epd: EPD):
        epd.fill(0)
        epd.fill_rect(0, 0, 200, 9, 1)
        epd.text("Up | Down  <Talks>  Select | Exit", 1, 1, 0)

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

    def input(self, epd: EPD, scroll_up: bool) -> bool:
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

    # Get schedule from server
    def _get_schedule(self, url: str):
        # TODO: implement non local schedule
        import adafruit_fakerequests
        return adafruit_fakerequests.Fake_Requests("/old_sched.json").json()

    # Sort schedule
    def _get_schedule_list(self, json: str):
        acc = []
        for track in json["tracks"]:
            for talk in track['talks']:
                talk["track"] = track["name"]
                acc.append(talk)
        
        acc.sort(key=lambda d: d['meta'])
        return acc

    # Main entry
    def run(self):
        schedule_json = self._get_schedule("/old_sched.json")
        sorted_schedule = self._get_schedule_list(schedule_json)
        
        main_group = displayio.Group()
        self.lcd.show(main_group)

        # Classes
        select = LCDTalksList(sorted_schedule)
        epdsplash = EPDTalks()

        title = LCDTitle()
        desc = EPDDescription()
        
        input_ack = InputAck()
        input_ack_group = input_ack.get_group()

        main_group.append(select.get_group())
        epdsplash.set_data(self.epd)
        self.epd.draw()

        self.buttons.events.clear()
        while True:
            time.sleep(0.025)
            select.update()
            event = self.buttons.events.get()
            if event and event.pressed:
                # BTN1 Exit
                if event.key_number == 0:
                    return

                # BTN2 Select
                elif event.key_number == 1:
                    talk = select.get_talk()
                    title.set_data(talk["title"], talk["track"], talk["meta"])
                    main_group.pop()
                    main_group.append(title.get_group())
                    desc.set_data(self.epd, talk["desc"])
                    self.epd.draw()
                    self.buttons.events.clear()
                    while True:
                        title.update()
                        time.sleep(0.025)

                        subevent = self.buttons.events.get()
                        if subevent and subevent.pressed:
                            main_group.append(input_ack_group)
                            time.sleep(0.5)
                            main_group.pop()

                            # BTN1 Exit
                            if subevent.key_number == 0:
                                return
                            # BTN2 Back
                            elif subevent.key_number == 1:
                                main_group.pop()
                                main_group.append(select.get_group())
                                epdsplash.set_data(self.epd)
                                self.epd.draw()
                                break
                            # BTN3 Down
                            elif subevent.key_number == 2:
                                if desc.input(self.epd, False):
                                    self.epd.draw()
                            # BTN4 Up
                            elif subevent.key_number == 3:
                                if desc.input(self.epd, True):
                                    self.epd.draw()
                            
                            self.buttons.events.clear()

                # BTN3 Down
                elif event.key_number == 2:
                    select.input(False)

                # BTN4 Up
                elif event.key_number == 3:
                    select.input(True)

                self.buttons.events.clear()


def test_app():
    import adafruit_fakerequests
    from utils import init_screens

    lcd, epd = init_screens()

    sched = ScheduleApp(lcd, epd)
    sched.run()