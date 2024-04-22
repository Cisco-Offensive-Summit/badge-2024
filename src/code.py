import supervisor
import badge.launcher

supervisor.runtime.autoreload = False

# Comment out this to run your code at launch, or create an app in the 'apps/' directory!
badge.launcher.run()