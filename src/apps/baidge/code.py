import supervisor
import badge.screens
from apps.baidge.baidge import BaidgeApp

supervisor.runtime.autoreload = False
try:
    import secrets
    import apps.baidge.ai_secrets as ai_secrets
    baidge = BaidgeApp(badge.screens.LCD, badge.screens.EPD, secrets.WIFI_NETWORK, secrets.WIFI_PASS, ai_secrets.OPENAI_KEY, ai_secrets.PERPLEXITY_KEY, ai_secrets.AUTOMATION_URL)
    baidge.setup()
    baidge.run()
except Exception as e:
    badge.screens.epd_print_exception(e)

supervisor.reload()