from microcontroller import reset
import supervisor
import badge.screens
from apps.tones.tones import TonesApp

supervisor.runtime.autoreload = False
tones = TonesApp(badge.screens.LCD, badge.screens.EPD)
tones.run()

reset()

