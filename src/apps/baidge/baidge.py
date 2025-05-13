import board
import keypad
import displayio
import terminalio
import wifi
import adafruit_connection_manager
import adafruit_requests
import audiobusio
import digitalio
import time
import random
import adafruit_requests
from badge.constants import *
import array
import audiocore
from badge.neopixels import NP
from time import sleep
from apps.baidge.badgemic import BadgeMic
from badge.screens import EPD
from badge.screens import round_button
from adafruit_display_text.label import Label
from displayio import Bitmap
from displayio import Group
from displayio import Palette
from displayio import TileGrid
from terminalio import FONT


url_transcription = "https://api.openai.com/v1/audio/transcriptions"
url_openai = "https://api.openai.com/v1/chat/completions"
url_perplexity = "https://api.perplexity.ai/chat/completions"
url_speech = "https://api.openai.com/v1/audio/speech"

def background():
    group = Group()
    background = Bitmap(EPD.width, EPD.height, 1)
    palette1 = Palette(1)
    palette1[0] = BLACK
    tile_grid1 = TileGrid(background, pixel_shader=palette1)
    group.append(tile_grid1)
    EPD.root_group = group

def text():
    pass

def labels():
    radius = 5
    splash = Group()
    label1 = Label (font=FONT, text="S4 - OpenAI")
    label2 = Label (font=FONT, text="S5 - Perplexity")
    label3 = Label (font=FONT, text="S6 - Automation")
    label4 = Label (font=FONT, text="S7 - Read back")
    splash.append(round_button(label1, 7, 12, radius))
    splash.append(round_button(label2, 7, 33, radius))
    splash.append(round_button(label3, 7, 55, radius))
    splash.append(round_button(label4, 7, 77, radius))
    EPD.root_group.append(splash)

def draw():
    EPD.refresh()

class BaidgeApp:
    def __init__(self, lcd: ST7735R, epd: EPD, ssid: str, wifipass: str, openai_key: str, perplexity_key: str, automation_url: str):
        self.lcd = lcd
        self.epd = epd
        self.ssid = ssid
        self.wifipass = wifipass
        self.openai_key = openai_key
        self.perplexity_key = perplexity_key
        self.automation_url = automation_url
        self.button_state = [0,0,0,0]
        self_active_button = -1
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)
    
    def __del__(self):
        self.buttons.deinit()
    
    def get_button(self,number):
        if number not in [0,1,2,3]:
            return False
        number = 3 - number
        event = self.buttons.events.get()
        while event:
            self.button_state[event.key_number] = True if event.pressed else False
            event = self.buttons.events.get()
        return self.button_state[number]
    
    def lights(self, stage):
        if stage==0:
            NP.fill(OFF)
            NP.show()
        if stage==1:
            NP[0] = RED
            NP.show()
        if stage==2:
            NP[0] = GREEN
            NP[1] = YELLOW
            NP.show()
        if stage==3:
            NP[0] = GREEN
            NP[1] = GREEN
            NP[2] = YELLOW
            NP.show()
        if stage==4:
            NP[0] = GREEN
            NP[1] = GREEN
            NP[2] = GREEN
            NP[3] = YELLOW
            NP.show()
        if stage==5:
            NP[0] = GREEN
            NP[1] = GREEN
            NP[2] = GREEN
            NP[3] = BLUE
            NP.show()
        if stage==6:
            NP[0] = GREEN
            NP[1] = GREEN
            NP[2] = GREEN
            NP[3] = GREEN
            NP.show()
    
    def whisper(self, quiet=True):
        self.lights(1)
        if not quiet: self.logterm.write("\r\n.")
        samples = self.microphone.record(1)
        for i in range(1,16):
            if self.get_button(self.active_button):
                if not quiet: self.logterm.write(".")
                samples += self.microphone.record(1)
            else:
                break
        self.lights(2)
        wav_bytes = self.microphone.wave(samples)
        boundary = '----WebKitFormBoundary' + str(int(time.time())) + str(random.randint(1000, 9999))
        form_data = bytearray()
        form_data.extend(('--' + boundary + '\r\n').encode())
        form_data.extend(('Content-Disposition: form-data; name="model"\r\n\r\n').encode())
        form_data.extend(("whisper-1" + '\r\n').encode())
        form_data.extend(('--' + boundary + '\r\n').encode())
        form_data.extend(('Content-Disposition: form-data; name="response_format"\r\n\r\n').encode())
        form_data.extend(("verbose_json" + '\r\n').encode())
        form_data.extend(('--' + boundary + '\r\n').encode())
        form_data.extend(('Content-Disposition: form-data; name="language"\r\n\r\n').encode())
        form_data.extend(("en" + '\r\n').encode())
        form_data.extend(('--' + boundary + '\r\n').encode())
        form_data.extend(('Content-Disposition: form-data; name="file"; filename="file.wav"\r\n').encode())
        form_data.extend(('Content-Type: application/octet-stream\r\n\r\n').encode())
        form_data.extend(wav_bytes)
        form_data.extend(('\r\n--' + boundary + '--\r\n').encode())
        headers = {"content-type": f"multipart/form-data; boundary={boundary}", "Authorization": f"Bearer {self.openai_key}", "Content-Length": str(len(form_data))}
        response = self.requests.post(url_transcription, data=form_data, headers=headers)
        self.lights(3)
        return response.json()['text']
    
    def speak(self, text, quiet=True):
        self.lights(4)
        if not quiet: self.logterm.write("\r\n")
        headers = {"content-type": "application/json", "Authorization": f"Bearer {self.openai_key}"}
        data = {
            "model": "gpt-4o-mini-tts",
            "input": text,
            "voice": "echo",
            "response_format": "pcm"
        }
        response = self.requests.post(url_speech, json=data, headers=headers)
        self.lights(5)
        if not quiet: self.logterm.write(".")
        if len(response.content)%2 > 0:
            # unlikely event of getting even bytes in the file
            response.content.pop(len(response.content)-1)
        if not quiet: self.logterm.write(".")
        wave = array.array("H", [0] * (len(response.content)//2))
        if not quiet: self.logterm.write(".")
        for i in range(0, len(response.content), 2):
            x = response.content[i] + 256*response.content[i+1]
            if x < 32768:
                wave[i//2] = x + 32768
            else:
                wave[i//2] = x - 32768
            value = wave[i//2]
            # if value<32768:
            #     delta = 32768-value
            #     delta *= 2
            #     wave[i//2] = 32768 - delta
            # else:
            #     delta = value-32768
            #     delta *= 2
            #     wave[i//2] = 32768 + delta
        if not quiet: self.logterm.write(".")
        sine_wave_sample = audiocore.RawSample(wave, sample_rate=24000)
        if not quiet: self.logterm.write(".")
        self.lights(6)
        self.speaker.play(sine_wave_sample, loop=True)
        sleep(len(wave)/24000)
        if not quiet: self.logterm.write(".")
        self.speaker.stop()
    
    def setup(self):
        background()
        text()
        labels()
        draw()
        I2S_BCLK = board.GPIO40
        I2S_WS = board.GPIO46
        I2S_DATA = board.GPIO39
        self.speaker = audiobusio.I2SOut(I2S_BCLK, I2S_WS, I2S_DATA)
        self.microphone = BadgeMic()
        splash = displayio.Group()
        fontx, fonty = terminalio.FONT.get_bounding_box()
        term_palette = displayio.Palette(2)
        term_palette[0] = 0x000000
        term_palette[1] = 0xffffff
        logbox = displayio.TileGrid(terminalio.FONT.bitmap,
            x=0,
            y=0,
            width=128 // fontx,
            height=128 // fonty,
            tile_width=fontx,
            tile_height=fonty,
            pixel_shader=term_palette)
        splash.append(logbox)
        self.logterm = terminalio.Terminal(logbox, terminalio.FONT)
        self.lcd.root_group = splash
        self.buttons.events.clear()

    def run(self):
        self.logterm.write(f"Connecting to {self.ssid}...")
        wifi.radio.connect(self.ssid, self.wifipass)
        self.logterm.write("Connected!\r\n")
        self.logterm.write("---------------------")
        pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
        self.requests = adafruit_requests.Session(pool, ssl_context)
        self.loop()
    
    def loop(self):
        while True:
            if self.get_button(0):
                self.active_button = 0
                self.run_openai(True)
            elif self.get_button(1):
                self.active_button = 1
                self.run_perplexity(True)
            elif self.get_button(2):
                self.active_button = 2
                self.run_automation(True)
            elif self.get_button(3):
                self.active_button = 3
                self.show_text(True)
            else:
                continue
            self.lights(0)
    
    def run_openai(self, speak):
        self.logterm.write("\r\n"*10)
        self.logterm.write("OpenAI\r\n---------------------")
        text = self.whisper()
        self.logterm.write("\r\n")
        self.logterm.write(text)
        headers = {"content-type": "application/json", "Authorization": f"Bearer {self.openai_key}"}
        data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You respond briefly. Answer user's question in maximum 2 sentences. Don't use too many words. Be precise and concise."},
                {"role": "user", "content": text}
            ]
        }
        response = self.requests.post(url_openai, json=data, headers=headers)
        response_text = response.json()['choices'][0]['message']['content']
        self.logterm.write(f"\r\n---\r\n{response_text}")
        if speak:
            self.speak(response_text)

    def run_perplexity(self, speak):
        self.logterm.write("\r\n"*10)
        self.logterm.write("Perplexity\r\n---------------------")
        text = self.whisper()
        self.logterm.write("\r\n")
        self.logterm.write(text)
        headers = {"content-type": "application/json", "Authorization": f"Bearer {self.perplexity_key}"}
        data = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You respond briefly. Answer user's question in ONE SENTENCE, maximum 50 words. Be precise and concise. The less words you use, the better. DO NOT include citations."},
                {"role": "user", "content": text}
            ],
            "max_tokens": 80,
            "temperature": 0.2,
            "return_images": False,
            "stream": False
        }
        response = self.requests.post(url_perplexity, json=data, headers=headers)
        response_text = response.json()['choices'][0]['message']['content']
        self.logterm.write(f"\r\n---\r\n{response_text}")
        if speak:
            self.speak(response_text)

    def run_automation(self, speak):
        self.logterm.write("\r\n"*10)
        self.logterm.write("N8N automation\r\n---------------------")
        text = self.whisper()
        self.logterm.write("\r\n")
        self.logterm.write(text)
        url = self.automation_url
        headers = {"content-type": "application/json"}
        data = {"message": text}
        response = self.requests.post(url, json=data, headers=headers)
        response_text = response.json()['output']
        self.logterm.write(f"\r\n---\r\n{response_text}")
        if speak:
            self.speak(response_text)
    
    def show_text(self, speak):
        self.logterm.write("\r\n"*10)
        self.logterm.write("Transcription\r\n---------------------")
        text = self.whisper()
        self.logterm.write("\r\n")
        self.logterm.write(text)
        if speak:
            self.speak(text)
