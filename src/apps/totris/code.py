import supervisor
import badge.screens
from apps.totris.totris import TotrisApp

supervisor.runtime.autoreload = False
try:
    tot = TotrisApp(badge.screens.LCD, badge.screens.EPD)
    tot.run()
except Exception as e:
    badge.screens.epd_print_exception(e)

supervisor.reload()