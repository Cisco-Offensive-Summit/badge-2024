import array,board,time,keypad,math
import displayio,terminalio
from displayio import Group
from displayio import TileGrid
from adafruit_display_text import label
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import center_text_x_plane
from badge.screens import clear_screen
from badge.screens import round_button
from badge.ziplist import ziplist

# for I2S DAC to function
import synthio,audiocore,audiobusio
from audiocore import RawSample
try:
    from audioio import AudioOut
except ImportError:
    try:
        from audiopwmio import PWMAudioOut as AudioOut
    except ImportError:
        pass  # not always supported by every board!
# for step sequencer lights
from badge.neopixels import set_neopixels
from badge.colors import CYAN,MAGENTA,OFF
from badge.log import log
COLORDIFF = MAGENTA - CYAN

class SequencerApp:
    def __init__(self,lcd: LCD,epd: EPD):
        self.lcd = lcd
        self.epd = epd
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ),value_when_pressed=False)
        self.dac_state = 0

    def __del__(self):
        self.buttons.deinit()

    def setup(self):
        pass

    def run(self):

        self._init_epd()

        while self._init_screen():
            self._play_sequences()

    def _init_epd(self):
        # B1 = "S4 Next"
        # B2 = "S7 Run"
        # SUMMIT = "Offensive Summit"
        # HEADER = "Select An App"
        scale = 1
        # button_rad = 5
        splash = Group()

        # SUMMIT_lb = center_text_x_plane(EPD, SUMMIT)
        # HEADER_lb = center_text_x_plane(EPD, HEADER, scale=scale)
        # HEADER_lb.y = (EPD.height //2) - ((HEADER_lb.bounding_box[BB_HEIGHT] * scale) // 2)

        # B1_lb = Label(font=FONT,text=B1)
        # B1_x = button_rad
        # B1_y = EPD.height - button_rad - ((B1_lb.bounding_box[BB_HEIGHT]*scale)//2)

        # B2_lb = Label(font=FONT,text=B2)
        # B2_x = EPD.width - button_rad - B2_lb.bounding_box[BB_WIDTH]
        # B2_y = EPD.height - button_rad - ((B2_lb.bounding_box[BB_HEIGHT]*scale)//2)
        bitmap = displayio.OnDiskBitmap(open("apps/sequencer/sequencer.bmp", "rb"))
        image = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

        clear_screen(EPD)
        splash.append(image) # shows the image
        # splash.append(SUMMIT_lb)
        # splash.append(HEADER_lb)
        # splash.append(round_button(B1_lb, B1_x, B1_y, 5))
        # splash.append(round_button(B2_lb, B2_x, B2_y, 5))
        EPD.root_group = splash
        EPD.refresh()

    def _init_screen(self):

        cont_label = label.Label(terminalio.FONT,text="Press S7 to continue")
        cont_label.anchor_point = (0.5,0.5)
        cont_label.anchored_position = (64,16)

        dac_label = label.Label(terminalio.FONT,text="Press S6 to toggle\n  DAC output:")
        dac_label.anchor_point = (0.5,0.5)
        dac_label.anchored_position = (64,56)

        if self.dac_state == 0:
            lt = "DAC output is OFF"
            lc = 0xFFFF00
        else:
            lt = "DAC output is ON"
            lc = 0x00FF00

        dac_status = label.Label(terminalio.FONT,text=lt)
        dac_status.anchor_point = (0.5,0.5)
        dac_status.anchored_position = (64,75)
        dac_status.color = lc

        exit_label = label.Label(terminalio.FONT,text="Press S4 to exit")
        exit_label.anchor_point = (0.5,0.5)
        exit_label.anchored_position = (64,112)

        root = displayio.Group()
        root.append(cont_label)
        root.append(dac_label)
        root.append(dac_status)
        root.append(exit_label)
        self.lcd.root_group = root

        self.buttons.events.clear()
        while True:
            event = self.buttons.events.get()
            if event and event.pressed:
                if event.key_number == 0:
                    return True
                if event.key_number == 1:
                    if self.dac_state == 0:
                        self.dac_state = 1
                        dac_status.color = 0x00FF00
                        dac_status.text = "DAC output is ON"
                    else:
                        self.dac_state = 0
                        dac_status.color = 0xFFFF00
                        dac_status.text = "DAC output is OFF"

                if event.key_number == 3:
                    return False
                else:
                    pass

    def _play_sequences(self):
        INDEX       = 0
        TONES       = [[0,"C4",60,262],[1,"D4",62,294],[2,"E4",64,330],[3,"F4",65,349],[4,"G4",67,392],[5,"A4",69,440],[6,"B4",71,494],[7,"C5",72,523],[8,None,None,None]]
        NOTE        = 1
        MIDI        = 2
        FREQ        = 3
        MINTONE     = 0
        MAXTONE     = 8
        TONE        = 5
        WAVES       = [[0,"sine"],[1,"square"],[2,"triangle"],[3,"saw"],[4,"supersaw"]]
        WAVEFORM    = 1
        MINWAVE     = 0
        MAXWAVE     = 3
        WAVE        = 0
        # sequencer variables
        MENUKEY     = ["init","seq","steps","step"]
        MENUS       = {0:["tempo+","tempo-","seq","play"],1:["steps+","steps-","steps","init"],2:["next"," prev","step","seq"],3:["note+","wave+",None,"steps"]}
        MINMENU     = 0
        MAXMENU     = 3
        MENU        = 0
        # steps: STEP:[WAVES[WAVE][index,waveform],TONES[TONE][index,note,midi,frequency]]
        STEPS       = {0:[WAVES[0],TONES[0]],1:[WAVES[0],TONES[8]],2:[WAVES[0],TONES[2]],3:[WAVES[0],TONES[8]],4:[WAVES[0],TONES[4]],5:[WAVES[0],TONES[8]],6:[WAVES[0],TONES[8]],7:[WAVES[0],TONES[3]],8:[WAVES[0],TONES[2]],9:[WAVES[0],TONES[1]],10:[WAVES[0],TONES[0]],11:[WAVES[0],TONES[1]],12:[WAVES[0],TONES[0]],13:[WAVES[0],TONES[2]],14:[WAVES[0],TONES[4]],15:[WAVES[0],TONES[2]]}
        MINSTEPS    = 0
        MAXSTEPS    = 15
        STEP        = 0
        NUMSTEPS    = 15
        # tempo from 60 to 160 bpm already calculated in ms
        TEMPOS       = [[60,1000],[70,857],[80,750],[90,667],[100,600],[110,545],[120,500],[130,462],[140,462],[150,400],[160,375]]
        MINTEMPO    = 0
        MAXTEMPO    = 10
        TEMPO       = 6
        # set up the I2S board
        # LCK -- TP4 -- board.GPIO4 -- STEMMA SDA
        # DIN -- TXD  -- board.GPIO43 (P1 connector TXD)
        # BCK -- RXD  -- board.GPIO44 (P1 connector RXD)
        # 3.3V -- V+  -- P1 connector V+ (or power module V+)
        # GND -- GND  -- P1 connector GND (or power modules GND)
        i2s_bck_pin = board.GPIO40 # BCK pin
        i2s_lck_pin = board.GPIO46 # LCK pin
        i2s_dat_pin = board.GPIO39 # DIN pin
        i2s = audiobusio.I2SOut(bit_clock=i2s_bck_pin,word_select=i2s_lck_pin,data=i2s_dat_pin)


        # Define wave table parameters
        WAVE_TABLE_LENGTH = 512  # The wave table length in samples
        SAMPLE_MAXIMUM = 32700  # The maximum value of a sample

        # define the red splash screen
        color_bitmap = displayio.Bitmap(128,128,1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x3453FF
        error_splash = displayio.TileGrid(color_bitmap,pixel_shader=color_palette,x=0,y=0)

        # define the green play button
        color_bitmap = displayio.Bitmap(128,128,1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0x00FF00
        play_splash = displayio.TileGrid(color_bitmap,pixel_shader=color_palette,x=0,y=0)
        play_label = label.Label(terminalio.FONT, text="-->")
        play_label.anchor_point = (0.5,0.5)
        play_label.anchored_position = (32,32)
        play_label.color = 0x000000
        play_screen = displayio.Group(scale=2)
        play_screen.append(play_splash)
        play_screen.append(play_label)


        palette = displayio.Palette(3)
        palette[0] = 0x000000
        palette[1] = 0x22aa00
        palette[2] = 0xbb00ee
        bg_palette = displayio.Palette(2)
        bg_palette[0] = 0x888888
        bg_palette[1] = 0x000000


        # bottom line area for menu
        button_labels = displayio.Group(scale=1)
        button_3 = label.Label(terminalio.FONT,text=f"{MENUS[MENU][3]}")
        button_3.anchor_point = (0.0,0.0)
        button_3.anchored_position = (0,100)
        button_3.color = 0x00FF00
        button_labels.append(button_3)
        button_2 = label.Label(terminalio.FONT,text=f"{MENUS[MENU][2]}")
        button_2.anchor_point = (0.0,0.0)
        button_2.anchored_position = (10,115)
        button_2.color = 0x00FFFFFF
        button_labels.append(button_2)
        button_1 = label.Label(terminalio.FONT,text=f"{MENUS[MENU][1]}")
        button_1.anchor_point = (0.0,0.0)
        button_1.anchored_position = (45,115)
        button_1.color = 0x38EDF9
        button_labels.append(button_1)
        button_0 = label.Label(terminalio.FONT,text=f"{MENUS[MENU][0]}")
        button_0.anchor_point = (1.0,0.0)
        button_0.anchored_position = (128,115)
        button_0.color = 0x38EDF9
        button_labels.append(button_0)
        # main screen area
        main_area = displayio.Group(scale=2)
        tempo_label = label.Label(terminalio.FONT, text=f"{TEMPOS[TEMPO][0]}bpm")
        tempo_label.anchor_point = (0.5,0.0)
        tempo_label.anchored_position = (32,20)
        tempo_label.color = 0xFFFFFF
        sequence_label = label.Label(terminalio.FONT, text=f"{NUMSTEPS} step(s)")
        sequence_label.anchor_point = (0.5,0.0)
        sequence_label.anchored_position = (32,20)
        sequence_label.color = 0xFFFFFF
        step_label = label.Label(terminalio.FONT, text=f"step {STEP+1}/{NUMSTEPS}")
        step_label.anchor_point = (0.5,0.0)
        step_label.anchored_position = (32,20)
        step_label.color = 0xFFFFFF
        wavetone_label = label.Label(terminalio.FONT, text=f"{WAVES[WAVE][1]} | {TONES[TONE][1]}")
        wavetone_label.anchor_point = (0.5,0.0)
        wavetone_label.anchored_position = (32,20)
        wavetone_label.color = 0xFFFFFF
        main_area.append(tempo_label)
        labels_index = [tempo_label,sequence_label,step_label,wavetone_label]
        root = displayio.Group()
        root.append(button_labels)
        root.append(main_area)
        self.lcd.root_group = root

        while True:
            event = self.buttons.events.get()
            if event and event.pressed:
                if event.key_number == 0:
                    if MENU == 0:
                        if TEMPO == (MAXTEMPO):
                            log(f"maximum tempo of {TEMPOS[TEMPO][0]}bpm reached")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            TEMPO = TEMPO + 1
                            log(f"increasing tempo to {TEMPOS[TEMPO][0]}bpm")
                            tempo_label.text=f"{TEMPOS[TEMPO][0]}bpm"
                    elif MENU == 1:
                        if NUMSTEPS == (MAXSTEPS+1):
                            log(f"maximum sequence length of {NUMSTEPS} steps reached")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            NUMSTEPS = NUMSTEPS + 1
                            log(f"increasing sequence length to {NUMSTEPS} steps")
                            sequence_label.text=f"{NUMSTEPS} step(s)"
                    elif MENU == 2:
                        if STEP == (NUMSTEPS-1):
                            log(f"you're at the last step (#{STEP+1})")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            STEP = STEP + 1
                            log(f"going to next step (#{STEP+1})")
                            step_label.text=f"step {STEP+1}/{NUMSTEPS}"
                    elif MENU == 3:
                        # steps: STEP:[WAVES[WAVE][index,waveform],TONES[TONE][index,note,midi,frequency]]
                        current_tone = STEPS[STEP][1][0]
                        if (current_tone < MAXTONE):
                            STEPS[STEP][1] = TONES[current_tone + 1]
                        else:
                            STEPS[STEP][1] = TONES[MINTONE]
                        wavetone_label.text=f"{STEPS[STEP][0][1]}|{STEPS[STEP][1][1]}"
                        log(f"going from a {TONES[current_tone][1]} to a {STEPS[STEP][1][1]}")
                    else:
                        log("you shouldn't be here")
                        pass

                if event.key_number == 1:
                    if MENU == 0:
                        if TEMPO == MINTEMPO:
                            log(f"minimum tempo of {TEMPOS[TEMPO][0]}bpm reached")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            TEMPO = TEMPO - 1
                            log(f"decreasing tempo to {TEMPOS[TEMPO][0]}bpm")
                            tempo_label.text=f"{TEMPOS[TEMPO][0]}bpm"
                    elif MENU == 1:
                        if NUMSTEPS == (MINSTEPS+1):
                            log(f"minimum sequence length of {NUMSTEPS} steps reached")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            NUMSTEPS = NUMSTEPS - 1
                            log(f"decreasing sequence length to {NUMSTEPS} steps")
                            sequence_label.text=f"{NUMSTEPS} step(s)"
                    elif MENU == 2:
                        if STEP == (MINSTEPS):
                            log(f"you're at the first step (#{STEP+1})")
                            root.append(error_splash)
                            time.sleep(0.05)
                            root.pop()
                        else:
                            STEP = STEP - 1
                            log(f"going to previous step (#{STEP+1})")
                            step_label.text=f"step {STEP+1}/{NUMSTEPS}"
                    elif MENU == 3:
                        # steps: STEP:[WAVES[WAVE][index,waveform],TONES[TONE][index,note,midi,frequency]]
                        current_wave = STEPS[STEP][0][0]
                        if (current_wave < MAXWAVE):
                            STEPS[STEP][0] = WAVES[current_wave + 1]
                        else:
                            STEPS[STEP][0] = WAVES[MINWAVE]
                        log(f"changing from a {WAVES[current_wave][1]} wave to a {STEPS[STEP][0][1]} wave")
                        wavetone_label.text=f"{STEPS[STEP][0][1]}|{STEPS[STEP][1][1]}"
                    else:
                        log("you shouldn't be here")
                        pass

                if event.key_number == 2:
                    if (MENU < MAXMENU):
                        MENU = MENU + 1
                        log(f"now in the {MENUKEY[MENU]} menu")
                        # change labels
                        button_3.text=f"{MENUS[MENU][3]}"
                        if MENU == 0:
                            button_3.color = 0x00FF00
                        else:
                            button_3.color = 0xFF0000
                        button_2.text=f"{MENUS[MENU][2]}"
                        button_1.text=f"{MENUS[MENU][1]}"
                        button_0.text=f"{MENUS[MENU][0]}"
                        # main screen switcher
                        main_area.pop()
                        tempo_label.text=f"{TEMPOS[TEMPO][0]}bpm"
                        sequence_label.text=f"{NUMSTEPS} step(s)"
                        step_label.text=f"step {STEP+1}/{NUMSTEPS}"
                        wavetone_label.text=f"{STEPS[STEP][0][1]}|{STEPS[STEP][1][1]}"
                        main_area.append(labels_index[MENU])
                    else:
                        log("unable to step into next menu")

                if event.key_number == 3:
                    if (MENU > MINMENU):
                        MENU = MENU - 1
                        log(f"now in the {MENUKEY[MENU]} menu")
                        # change menu labels
                        button_3.text=f"{MENUS[MENU][3]}"
                        if MENU == 0:
                            button_3.color = 0x00FF00
                        else:
                            button_3.color = 0xFF0000
                        button_2.text=f"{MENUS[MENU][2]}"
                        button_1.text=f"{MENUS[MENU][1]}"
                        button_0.text=f"{MENUS[MENU][0]}"
                        # main screen switcher
                        main_area.pop()
                        tempo_label.text=f"{TEMPOS[TEMPO][0]}bpm"
                        sequence_label.text=f"{NUMSTEPS} step(s)"
                        step_label.text=f"step {STEP+1}/{NUMSTEPS}"
                        wavetone_label.text=f"{STEPS[STEP][0][1]}|{STEPS[STEP][1][1]}"
                        main_area.append(labels_index[MENU])
                    else:
                        log(f"playing sequence with a {TEMPOS[TEMPO][0]}bpm tempo")
                        root.append(play_screen)
                        ### play note
                        for i in range(NUMSTEPS):
                            # steps: STEP:[WAVES[WAVE][index,waveform],TONES[TONE][index,note,midi,frequency]]
                            w = STEPS[i][0][1]
                            t = STEPS[i][1][3]
                            #set neopixels for each step into the range between CYAN and RED
                            if i == 0:
                                COLOR = CYAN
                            elif i == (NUMSTEPS-1):
                                COLOR = MAGENTA
                            else:
                                COLOR = int((COLORDIFF/NUMSTEPS)*(i+1))
                            if i%4 == 0:
                                set_neopixels(COLOR,OFF,OFF,OFF)
                            elif i%4 == 1:
                                set_neopixels(OFF,COLOR,OFF,OFF)
                            elif i%4 == 2:
                                set_neopixels(OFF,OFF,COLOR,OFF)
                            else:
                                set_neopixels(OFF,OFF,OFF,COLOR)
                            if STEPS[i][1][1] == None:
                                log(f"step {STEP+1} is an empty step")
                                time.sleep(TEMPOS[TEMPO][1]/1000)
                            else:
                                # Generate one period of sine wave.
                                tone_volume_sine   = 0.5  # Increase this to increase the volume of the tone.
                                tone_volume_square = 0.1
                                tone_volume_saw    = 0.7
                                tone_volume_tri    = 0.5
                                #tone_volume_ssaw   = 0.2
                                length = 8000 // t
                                wave2play = array.array("H",[0] * length)
                                for j in range(length):
                                    # change waves calculated for sine,square,triangle,and sawtooth
                                    # square(t) = sgn(sin(2πt))
                                    # sawtooth(t) = t - floor(t + 1/2)
                                    # triangle(t) = abs(sawtooth(t))
                                    period = j / length
                                    sine_wave = math.sin(math.pi * 2 * j / length)
                                    if w == "sine":
                                        wave2play[j] = int((1 + sine_wave) * tone_volume_sine * (2 ** 15 - 1))
                                    elif w == "square":
                                        if sine_wave > 0:
                                            square_wave = 1
                                        elif sine_wave == 0:
                                            square_wave = 0
                                        else:
                                            square_wave = -1
                                        wave2play[j] = int((1 + square_wave) * tone_volume_square * (2 ** 15 - 1))
                                    else:
                                        trisaw_wave = (period) - math.floor(period + 1/2)
                                        tone_volume = tone_volume_saw
                                        #if w == "supersaw":
                                        #    trisaw_wave_0 = ((j-100)/length) - math.floor(((j-100)/length) + 1/2)
                                        #    trisaw_wave_2 = ((j+100)/length) - math.floor(((j+100)/length) + 1/2)
                                        #    trisaw_wave = (trisaw_wave_0 + trisaw_wave + trisaw_wave_2) / 3
                                        #    tone_volume = tone_volume_ssaw
                                        if w == "triangle":
                                            trisaw_wave = math.fabs(trisaw_wave)
                                            tone_volume = tone_volume_tri
                                        wave2play[j] = int((1 + trisaw_wave) * tone_volume * (2 ** 15 - 1))

                                wave2play_sample = RawSample(wave2play)
                                if (self.dac_state == 1):
                                    i2s.play(wave2play_sample,loop=True)
                                    time.sleep(TEMPOS[TEMPO][1]/1000)
                                    i2s.stop()
                                else:
                                    time.sleep(TEMPOS[TEMPO][1]/1000)
                        root.pop()
                        set_neopixels(OFF,OFF,OFF,OFF)
