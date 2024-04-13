import supervisor
import time
import badge.screens
from apps.schedule.schedule import ScheduleApp
import secrets
import badge.neopixels

supervisor.runtime.autoreload = False
badge.neopixels.neopixels_off()

try:
    sched = ScheduleApp(badge.screens.LCD, badge.screens.EPD, secrets.WIFI_NETWORK, secrets.WIFI_PASS, secrets.HOST_ADDRESS+'badge/schedule', secrets.UNIQUE_ID)
    sched.run()
except AttributeError:
    e = AttributeError("Secrets file is missing required information\nPlease visit:\n\nbadger.becomingahacker.com /recovery")
    badge.screens.epd_print_exception(e)
    badge.screens.EPD.draw()
    time.sleep(60)
except Exception as e:
    badge.screens.epd_print_exception(e)
    badge.screens.EPD.draw()
    time.sleep(60)

supervisor.reload()