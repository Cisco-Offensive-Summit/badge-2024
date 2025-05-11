import supervisor
supervisor.runtime.autoreload = False
from apps.totris.totris import Totris

try:
    Totris().run()
except Exception as e:
    badge.screens.epd_print_exception(e)

supervisor.reload()