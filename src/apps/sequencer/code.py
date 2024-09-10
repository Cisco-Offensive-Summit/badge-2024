from microcontroller import reset
import supervisor
import badge.screens
from apps.sequencer.sequencer import SequencerApp

supervisor.runtime.autoreload = False
tones = SequencerApp(badge.screens.LCD, badge.screens.EPD)
tones.run()

reset()

