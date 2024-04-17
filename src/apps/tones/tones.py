import board, random, time, keypad, math
import displayio, digitalio, terminalio
from adafruit_display_text import label
# for wavetable visualizer
from cedargrove_wavebuilder import WaveBuilder, WaveShape
from cedargrove_waveviz import WaveViz
# for I2S DAC to function
import synthio, audiocore, audiobusio

class TonesApp:
    def __init__(self, lcd: ST7735R, epd: EPD):
        self.lcd = lcd
        self.epd = epd
        self.buttons = keypad.Keys((
            board.BTN1,
            board.BTN2,
            board.BTN3,
            board.BTN4,
        ), value_when_pressed=False)
        self.dac_state = 0

    def __del__(self):
        self.buttons.deinit()

    def setup(self):
        pass

    def run(self):

        self.epd.image("img/tones.bmp")
        self.epd.text("Waveform", 5, 78, 1)
        self.epd.text("S4", 14, 87, 1)
        self.epd.text("Up", 80, 78, 1)
        self.epd.text("S5", 80, 87, 1)
        self.epd.text("Down", 120, 78, 1)
        self.epd.text("S6", 124, 87, 1)
        self.epd.text("Play", 173, 78, 1)
        self.epd.text("S7", 178, 87, 1)
        self.epd.draw()

        while self._init_screen():
            self._play_tones()

    def _init_screen(self):

        cont_label = label.Label(terminalio.FONT, text="Press S7 to continue")
        cont_label.anchor_point = (0.5, 0.5)
        cont_label.anchored_position = (64, 16)

        dac_label = label.Label(terminalio.FONT, text="Press S6 to toggle\n  DAC output:")
        dac_label.anchor_point = (0.5, 0.5)
        dac_label.anchored_position = (64, 56)

        if self.dac_state == 0:
            lt = "DAC output is OFF"
            lc = 0xFFFF00
        else:
            lt = "DAC output is ON"
            lc = 0x00FF00

        dac_status = label.Label(terminalio.FONT, text=lt)
        dac_status.anchor_point = (0.5, 0.5)
        dac_status.anchored_position = (64, 75)
        dac_status.color = lc

        exit_label = label.Label(terminalio.FONT, text="Press S4 to exit")
        exit_label.anchor_point = (0.5, 0.5)
        exit_label.anchored_position = (64, 112)

        root = displayio.Group()
        root.append(cont_label)
        root.append(dac_label)
        root.append(dac_status)
        root.append(exit_label)
        self.lcd.show(root)

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

    def _play_tones(self):
        TONES       = [["C4",60,262],["D4",62,294],["E4",64,330],["F4",65,349],["G4",67,392],["A4",69,440],["B4",71,494],["C5",72,523]]
        NOTE        = 0
        MIDI        = 1
        FREQ        = 2
        WAVEFORMS   = ["sine", "square", "triangle", "saw", "supersaw"]
        MINTONE     = 0
        MAXTONE     = 7
        TONE        = 5
        MINWAVE     = 0
        MAXWAVE     = 4
        WAVE        = 0
        
        # set up the I2S board
        i2s_bck_pin = board.GPIO44 # BCK pin
        i2s_lck_pin = board.GPIO4 # LCK pin
        i2s_dat_pin = board.GPIO43 # DIN pin
        audio = audiobusio.I2SOut(bit_clock=i2s_bck_pin, word_select=i2s_lck_pin, data=i2s_dat_pin)
        
        
        # Define wave table parameters
        WAVE_TABLE_LENGTH = 512  # The wave table length in samples
        SAMPLE_MAXIMUM = 32700  # The maximum value of a sample



        palette = displayio.Palette(3)
        palette[0] = 0x000000
        palette[1] = 0x22aa00
        palette[2] = 0xbb00ee
        bg_palette = displayio.Palette(2)
        bg_palette[0] = 0x888888
        bg_palette[1] = 0x000000


        waveform_label_area = label.Label(terminalio.FONT, text ="Waveform:")
        waveform_label_area.anchor_point = (0.0,1.0)
        waveform_label_area.anchored_position = (2, 13)
        waveform_label_area.color = 0x00FFFFFF

        waveform_area = label.Label(terminalio.FONT, text =f"{WAVEFORMS[WAVE]}")
        waveform_area.anchor_point = (1.0,1.0)
        waveform_area.anchored_position = (115, 13)
        waveform_area.color = 0xFFFF00

        note_label_area = label.Label(terminalio.FONT, text="Note (Hz):")
        note_label_area.anchor_point = (0.0, 0.0)
        note_label_area.anchored_position = (2, 115)
        note_label_area.color = 0x00FFFFFF

        note_area = label.Label(terminalio.FONT, text=f"{TONES[TONE][NOTE]} ({TONES[TONE][FREQ]})")
        note_area.anchor_point = (1.0, 0.0)
        note_area.anchored_position = (126, 115)
        note_area.color = 0x38EDF9

        ###########  example wave shape that is displayed as a splash screen ###########
        # Define the Harmonica wave shape, overtone ratio, and amplitude
        tone = [
            (WaveShape.Sine, 1.00, 0.10),
            (WaveShape.Sine, 2.00, 0.48),
            (WaveShape.Sine, 3.00, 0.28),
            (WaveShape.Sine, 4.00, 0.02),
            (WaveShape.Sine, 5.00, 0.12),
        ]

        # Create the wave table (wave.wave_table)
        wave = WaveBuilder(
            oscillators=tone,
            table_length=WAVE_TABLE_LENGTH,
            sample_max=SAMPLE_MAXIMUM,
            lambda_factor=1.0,
            loop_smoothing=True,
            debug=False,
        )

        # Create a synthio.Envelope object
        env = synthio.Envelope(
            attack_time=0.05,
            attack_level=1.0,
            decay_time=0.1,
            release_time=0.1,
            sustain_level=0.5,
        )

        graph = WaveViz(wave.wave_table, x=0, y=13, width=128,
                        height=101, plot_color=palette[2], back_color=bg_palette[1],
                        auto_scale=False)
        waveform = displayio.Group(scale=1)
        waveform.append(graph)
        bg_bitmap = displayio.Bitmap(8, 8, 2)
        background = displayio.Group(scale=16)
        background.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0))

        root = displayio.Group()
        root.append(background)
        root.append(waveform_label_area)
        root.append(waveform_area)
        root.append(note_label_area)
        root.append(note_area)
        root.append(waveform)
        self.lcd.show(root)

        while True:
#            # set up DAC if enabled
#            if (self.dac_state == 1):
#                try:
#                    i2c = board.I2C()
#                    dac = adafruit_ad569x.Adafruit_AD569x(i2c)
#                except:
#                    self.dac_state = 0
#                    print("turning DAC off")

            event = self.buttons.events.get()
            if event and event.pressed:
                if event.key_number == 0:
                    # calculate the amplitude offset
                    offset = (TONES[TONE][FREQ] / 10000)
                    waveform.pop()              # clear display
                    if WAVE == 0:               # sine wave
                        # Define the Harmonica wave shape, overtone ratio, and amplitude
                        tone = [
                            (WaveShape.Sine, 1.00, (0.82 + offset)),
                        ]
                        # Create the wave table (wave.wave_table)
                        wave = WaveBuilder(
                            oscillators=tone,
                            table_length=WAVE_TABLE_LENGTH,
                            sample_max=SAMPLE_MAXIMUM,
                            lambda_factor=1.0,
                            loop_smoothing=True,
                            debug=False,
                        )
                        # Display new waveform
                        graph = WaveViz(wave.wave_table, x=0, y=13,
                                        width=128, height=101, plot_color=palette[2],
                                        back_color=bg_palette[1], auto_scale=False)
                        waveform.append(graph)

                        if (self.dac_state == 1):
                            ### play note
                            with open(f"apps/tones/notes/sine_{TONES[TONE][NOTE]}.wav", "rb") as f:
                                wav = audiocore.WaveFile(f)
                                audio.play(wav)
                                while audio.playing:
                                    pass
                        else:
                            pass

                    if WAVE == 1:               # square wave
                        tone = [
                            (WaveShape.Square, 1.00, (0.82 + offset)),
                        ]
                        # Create the wave table (wave.wave_table)
                        wave = WaveBuilder(
                            oscillators=tone,
                            table_length=WAVE_TABLE_LENGTH,
                            sample_max=SAMPLE_MAXIMUM,
                            lambda_factor=1.0,
                            loop_smoothing=True,
                            debug=False,
                        )
                        # Display new waveform
                        graph = WaveViz(wave.wave_table, x=0, y=13,
                                        width=128, height=101, plot_color=palette[2],
                                        back_color=bg_palette[1], auto_scale=False)
                        waveform.append(graph)

                        if (self.dac_state == 1):
                            ### play note
                            with open(f"apps/tones/notes/square_{TONES[TONE][NOTE]}.wav", "rb") as f:
                                wav = audiocore.WaveFile(f)
                                audio.play(wav)
                                while audio.playing:
                                    pass                                
                        else:
                            pass


                    if WAVE == 2:               # triangle wave
                        tone = [
                            (WaveShape.Triangle, 1.00, (0.82 + offset)),
                        ]
                        # Create the wave table (wave.wave_table)
                        wave = WaveBuilder(
                            oscillators=tone,
                            table_length=WAVE_TABLE_LENGTH,
                            sample_max=SAMPLE_MAXIMUM,
                            lambda_factor=1.0,
                            loop_smoothing=True,
                            debug=False,
                        )
                        # Display new waveform
                        graph = WaveViz(wave.wave_table, x=0, y=13,
                                        width=128, height=101, plot_color=palette[2],
                                        back_color=bg_palette[1], auto_scale=False)
                        waveform.append(graph)

                        if (self.dac_state == 1):
                            ### play note
                            with open(f"apps/tones/notes/triangle_{TONES[TONE][NOTE]}.wav", "rb") as f:
                                wav = audiocore.WaveFile(f)
                                audio.play(wav)
                                while audio.playing:
                                    pass
                        else:
                            pass


                    if WAVE == 3:               # saw wave
                        tone = [
                            (WaveShape.Saw, 1.00, (0.82 + offset)),
                        ]
                        # Create the wave table (wave.wave_table)
                        wave = WaveBuilder(
                            oscillators=tone,
                            table_length=WAVE_TABLE_LENGTH,
                            sample_max=SAMPLE_MAXIMUM,
                            lambda_factor=1.0,
                            loop_smoothing=True,
                            debug=False,
                        )
                        # Display new waveform
                        graph = WaveViz(wave.wave_table, x=0, y=13,
                                        width=128, height=101, plot_color=palette[2],
                                        back_color=bg_palette[1], auto_scale=False)
                        waveform.append(graph)

                        if (self.dac_state == 1):
                            ### play note
                            with open(f"apps/tones/notes/saw_{TONES[TONE][NOTE]}.wav", "rb") as f:
                                wav = audiocore.WaveFile(f)
                                audio.play(wav)
                                while audio.playing:
                                    pass
                        else:
                            pass


                    if WAVE == 4:               # supersaw wave
                        tone = [
                            (WaveShape.Saw, 1.00, (0.30 + offset)),
                            (WaveShape.Saw, 2.00, (0.23 + offset)),
                            (WaveShape.Saw, 3.00, (0.27 + offset)),
                        ]
                        # Create the wave table (wave.wave_table)
                        wave = WaveBuilder(
                            oscillators=tone,
                            table_length=WAVE_TABLE_LENGTH,
                            sample_max=SAMPLE_MAXIMUM,
                            lambda_factor=1.0,
                            loop_smoothing=True,
                            debug=False,
                        )
                        # Display new waveform
                        graph = WaveViz(wave.wave_table, x=0, y=13,
                                        width=128, height=101, plot_color=palette[2],
                                        back_color=bg_palette[1])
                        waveform.append(graph)

                        if (self.dac_state == 1):
                            ### play note
                            with open(f"apps/tones/notes/supersaw_{TONES[TONE][NOTE]}.wav", "rb") as f:
                                wav = audiocore.WaveFile(f)
                                audio.play(wav)
                                while audio.playing:
                                    pass
                        else:
                            pass


                if event.key_number == 1:
                    if (TONE > MINTONE):
                        TONE = TONE - 1
                    else:
                        TONE = MAXTONE
                    note_area.text = f"{TONES[TONE][NOTE]} ({TONES[TONE][FREQ]})"
                if event.key_number == 2:
                    if (TONE < MAXTONE):
                        TONE = TONE + 1
                    else:
                        TONE = MINTONE
                    note_area.text = f"{TONES[TONE][NOTE]} ({TONES[TONE][FREQ]})"
                if event.key_number == 3:
                    if (WAVE < MAXWAVE):
                        WAVE = WAVE + 1
                    else:
                        WAVE = MINWAVE
                    waveform_area.text = f"{WAVEFORMS[WAVE]}"
                else:
                    pass
