import asyncio
import random
import time

import collections
import espnow
import espidf
import wifi

import displayio
import badge.buttons
import board
import supervisor
import terminalio
from terminalio import FONT
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_display_text.label import Label
from adafruit_display_text import label, wrap_text_to_pixels
from adafruit_led_animation.color import RED
from badge.screens import EPD, epd_print_exception, LCD, clear_screen
from badge.screens import round_button
from badge.screens import center_text_x_plane
# from badge.screens import epd_center_text
from badge.events import ANY_BTN_PRESSED, ANY_BTN_RELEASED, on
from badge.log import log
from badge.neopixels import NP as PIXELS
from badge.neopixels import neopixels_off, set_neopixel, neopixel_reinit
from displayio import Group
from badge.constants import BB_HEIGHT
from badge.constants import BB_WIDTH

EPD_DISP_H = EPD.height
EPD_DISP_W = EPD.width
LCD_DISP_H = LCD.height
LCD_DISP_W = LCD.width

character_set = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

@on(badge.events.BTN_A_PRESSED)
def on_a_pressed(e):
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(badge.events.BTN_B_PRESSED)
def on_b_pressed(e):
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(badge.events.BTN_C_PRESSED)
def on_c_pressed(e):
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(badge.events.BTN_D_PRESSED)
def on_d_pressed(e):
    set_neopixels(0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00)

@on(badge.events.BTN_A_RELEASED)
def on_a_released(e):
    neopixels_off()

@on(badge.events.BTN_B_RELEASED)
def on_b_released(e):
    neopixels_off()

@on(badge.events.BTN_C_RELEASED)
def on_c_released(e):
    neopixels_off()

@on(badge.events.BTN_D_RELEASED)
def on_d_released(e):
    neopixels_off()

MaxMessageLength = 20
class Messenger:
    def __init__(self):
        print("Creating Messenger")
        self.message_log = list()
        self.message_log.append("Messages")


        wifi.radio.start_ap(" ", "", channel=1, max_connections=0)
        wifi.radio.stop_ap()
        # wifi.radio.enabled = False
        self.e = espnow.ESPNow()
        self.e.phy_rate = 0
        #peer = espnow.Peer(mac=b'\xa0\x85\xe3\xe7\x9c\xb8') # Dummy Peer
        peer = espnow.Peer(mac=b'\xa0\x85\xe3\xe7\xfc\xc8') # 
        self.e.peers.append(peer)
        peer = espnow.Peer(mac=b'\xa0\x85\xe3\xe7\xef\xc0') # 
        self.e.peers.append(peer)
        self.e.send("register")


        # Begin setup Display
        self.group = displayio.Group()
        self.messages_group = displayio.Group()
        self.group.append(self.messages_group)
        self.edit_group = displayio.Group()
        self.group.append(self.edit_group)
        # badge.screens.LCD.show(self.group)


        self.message_area = label.Label(terminalio.FONT, text='\n'.join(wrap_text_to_pixels('\n'.join(self.message_log), 126, terminalio.FONT)))
        self.message_area.anchor_point = (0,0)
        self.message_area.anchored_position = (2, 0)
        self.messages_group.append(self.message_area)

        self.edit_area = label.Label(terminalio.FONT, text='\n'.join(wrap_text_to_pixels("Editor", 126, terminalio.FONT)))
        self.edit_area.anchor_point = (0,0)
        self.edit_area.anchored_position = (3, 100)
        self.edit_group.append(self.edit_area)

        self.char_index = 0
        self.message = [0 for _ in range(MaxMessageLength)]        

        LCD.root_group = self.group
        LCD.refresh()


    def buildMessage(self):
        msg = ''.join([character_set[self.message[x]] for x in range(MaxMessageLength)])
        self.edit_area.text = msg
        return msg

    def welcome_screen(self):
        title1 = "Welcome to"
        title2 = "MESSENGER!"
        subtitle1 = "Type a message"
        subtitle2 = "Send to all badges"
        subtitle3 = "PRESS ANY BUTTON"
        subtitle4 = "TO START"


        welcome = Group()
        clear_screen(EPD)
        # self.background()
        T1 = center_text_x_plane(EPD, title1, y=5, scale=1)
        T2 = center_text_x_plane(EPD, title2, 20, scale=2)
        M1 = center_text_x_plane(EPD, subtitle1, 40)
        M2 = center_text_x_plane(EPD, subtitle2, 50)
        M3 = center_text_x_plane(EPD, subtitle3, 75)
        M4 = center_text_x_plane(EPD, subtitle4, 85)
        welcome.append(T1)
        welcome.append(T2)
        welcome.append(M1)
        welcome.append(M2)
        welcome.append(M3)
        welcome.append(M4)
        # EPD.draw()
        EPD.root_group = welcome
        EPD.refresh()

    def regular_screen(self):
        clear_screen(EPD)
        title1 = "MESSENGER"
        subtitle1 = "Challenge:"
        subtitle2 = "Send messages to"
        subtitle3 = "only some recipients"

        # self.background()
        T1 = center_text_x_plane(EPD, title1, y=10, scale=2)
        # epd_center_text(title2, 20, scale=2)
        M1 = center_text_x_plane(EPD, subtitle1, 25)
        M2 = center_text_x_plane(EPD, subtitle2, 35)
        M3 = center_text_x_plane(EPD, subtitle3, 45)

        instruction = Group()
        instruction.append(T1)
        instruction.append(M1)
        instruction.append(M2)
        instruction.append(M3)

        scale = 1
        button_rad = 5
        B1 = "L"
        B2 = "R"
        B3 = "Char"
        B4 = "Send"
        B1_lb = Label(font=FONT,text=B1)
        B2_lb = Label(font=FONT,text=B2)
        B3_lb = Label(font=FONT,text=B3)
        B4_lb = Label(font=FONT,text=B4)
        B1_x = 5 + button_rad
        B1_y = EPD.height - button_rad - ((B1_lb.bounding_box[BB_HEIGHT]*scale)//2)
        B2_x = EPD.width//4 #+ B2_lb.bounding_box[BB_WIDTH]
        B2_y = EPD.height - button_rad - ((B2_lb.bounding_box[BB_HEIGHT]*scale)//2)
        B3_x = EPD.width//2 #+ B2_lb.bounding_box[BB_WIDTH]
        B3_y = EPD.height - button_rad - ((B3_lb.bounding_box[BB_HEIGHT]*scale)//2)
        B4_x = EPD.width - B4_lb.bounding_box[BB_WIDTH] - button_rad
        B4_y = EPD.height - button_rad - ((B4_lb.bounding_box[BB_HEIGHT]*scale)//2)
        instruction.append(round_button(B1_lb, B1_x, B1_y, 5))
        instruction.append(round_button(B2_lb, B2_x, B2_y, 5))
        instruction.append(round_button(B3_lb, B3_x, B3_y, 5))
        instruction.append(round_button(B4_lb, B4_x, B4_y, 5))
        EPD.root_group = instruction
        EPD.refresh()

        # EPD.draw()

    def checkForMessages(self):

        packets = list()
        await asyncio.sleep(1)
        if self.e:
            packet = self.e.read()
            if packet == None:
                return
            peer = espnow.Peer(mac=packet.mac)
            try:
                self.e.peers.append(peer)
            except espidf.IDFError as err:
                print(err)
            print(packet.msg.decode(), [hex(i) for i in packet.mac], packet.rssi, packet.time )
            self.message_log.append(packet.msg.decode())
            while len(self.message_log) > 6:
                print("Longer than 6, deleting message", self.message_log[0])
                del self.message_log[0]

            self.message_area.text = '\n'.join(self.message_log) #.append("\n" + packet)
        LCD.refresh()

    async def handleButtons(self):
        print("Handling Buttons")
        while True:
            await ANY_BTN_PRESSED.wait()
            b_pressed = ANY_BTN_PRESSED.data["name"]
            await ANY_BTN_RELEASED.wait()
            b_released = ANY_BTN_PRESSED.data["name"]
            if b_pressed != b_released:
                return
            button = b_pressed 
            print("Got button", button, "In handleButtons()")
            if button == "A":
                self.char_index = self.char_index-1
            if button == "B":
                self.char_index = self.char_index+1
            if button == "C":
                self.message[self.char_index] = self.message[self.char_index] + 1
            if button == "D":
                print(self.buildMessage())
                self.e.send(self.buildMessage())
                while len(self.message_log) > 5:
                    del self.message_log[0]
                self.message_log.append(self.buildMessage())
                self.message_area.text = '\n'.join(self.message_log)
            self.buildMessage()
            LCD.refresh()


    async def receve(self):
        

        print("Entering a loop")
        while True:
            await asyncio.sleep(1)
            if self.e:
                packet = self.e.read()
                peer = espnow.Peer(mac=packet.mac)
                try:
                    self.e.peers.append(peer)
                except espidf.IDFError as err:
                    print(err)
                print(packet.msg.decode(), [hex(i) for i in packet.mac], packet.rssi, packet.time )

                self.message_log.append(packet.msg.decode())
                while len(self.message_log) > 6:
                    print("Longer than 6, deleting message", self.message_log[0])
                    del self.message_log[0]

                self.message_area.text = '\n'.join(self.message_log) #.append("\n" + packet)
            LCD.refresh()

async def main():
    print("Starting Messenger Application")
    messenger_app = Messenger()
    neopixels_off()
    _ = badge.buttons.start_tasks(interval=0.001)
    messenger_app.welcome_screen()
    # await ANY_BTN_RELEASED.wait()
    keep_playing = True
    neopixels_off()
    # Wait for keypress
    await ANY_BTN_PRESSED.wait()
    button_pressed = ANY_BTN_PRESSED.data["name"]
    print("Got button", button_pressed)
    await ANY_BTN_RELEASED.wait()
    # stop_msecs = supervisor.ticks_ms()
    messenger_app.regular_screen()
    # elapsed = None
    # asyncio.run(messenger_app.receve())
    # asyncio.run(messenger_app.handleButtons())
    R1 = asyncio.create_task(messenger_app.receve())
    B1 = asyncio.create_task(messenger_app.handleButtons())
    await asyncio.gather(R1, B1)
    # messenger_app.handleButtons()
    # while keep_playing:
    #     keep_playing = await messenger_app.play()
    #     print(f"main. keep_playing={keep_playing}")
    print("main.reloading")
    time.sleep(1)
    supervisor.reload()


try:
    # main()
    print([hex(i) for i in wifi.radio.mac_address])
    asyncio.run(main())
    # asyncio.run(buttons())
except Exception as e:
    epd_print_exception(e)