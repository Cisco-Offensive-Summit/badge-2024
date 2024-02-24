import storage, board, digitalio, microcontroller, os
import updater, secrets

BTN1 = digitalio.DigitalInOut(board.BTN1)
BTN1.direction = digitalio.Direction.INPUT
BTN1.pull = digitalio.Pull.UP

BTN2 = digitalio.DigitalInOut(board.BTN2)
BTN2.direction = digitalio.Direction.INPUT
BTN2.pull = digitalio.Pull.UP

# Hold BTN1 and BTN2 during reboot to update
if not BTN1.value and not BTN2.value:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=False)
    #OTA = updater.Updater(secrets.WIFI_NETWORK, secrets.WIFI_PASS, secrets.GH_REPO, secrets.GH_SRC_FOLDER, debug=True)
    #try:
    #    special_files = OTA.run()
    #    for tup in special_files:
    #        os.rename(tup[0], tup[1])
    #except Exception as e:
    #    print("OTA failed: {}".format(e))
    #microcontroller.reset()

# Uncomment to for updater testing
#storage.remount("/", readonly=False, disable_concurrent_write_protection=False)