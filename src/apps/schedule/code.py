import supervisor
import microcontroller
import time
from badge.screens import EPD, LCD, epd_print_exception
from apps.schedule.schedule import ScheduleApp
import badge.neopixels

supervisor.runtime.autoreload = False
badge.neopixels.neopixels_off()

try:
    import secrets
    sched = ScheduleApp(LCD, EPD, secrets.WIFI_NETWORK, secrets.WIFI_PASS, secrets.HOST_ADDRESS, secrets.UNIQUE_ID)
    sched.run()
except ImportError:
    e = AttributeError("Secrets file is missing. Please visit:\nbadger.becomingahacker.com /recovery")
    epd_print_exception(e)
    time.sleep(60)
except Exception as e:
    epd_print_exception(e)
    time.sleep(60)

microcontroller.reset()
