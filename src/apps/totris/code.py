import supervisor
import badge.screens
from apps.totris.totris import TotrisApp

supervisor.runtime.autoreload = False
tot = TotrisApp(badge.screens.LCD, badge.screens.EPD)
tot.run()

supervisor.reload()