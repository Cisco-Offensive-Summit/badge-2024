import supervisor
import time
import badge.screens
from apps.schedule.schedule import ScheduleApp
import secrets

supervisor.runtime.autoreload = False
sched = ScheduleApp(badge.screens.LCD, badge.screens.EPD, secrets.WIFI_NETWORK, secrets.WIFI_PASS, secrets.HOST_ADDRESS+'badge/schedule', secrets.UNIQUE_ID)
try:
    sched.run()
except:
    time.sleep(15)

supervisor.reload()