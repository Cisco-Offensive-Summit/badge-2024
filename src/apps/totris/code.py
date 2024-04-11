from supervisor import reload
import badge.screens
from apps.totris.totris import TotrisApp

tot = TotrisApp(badge.screens.LCD, badge.screens.EPD)
tot.run()

reload()