import storage, board, digitalio, microcontroller, sys
import updater

BTN1 = digitalio.DigitalInOut(board.BTN1)
BTN1.direction = digitalio.Direction.INPUT
BTN1.pull = digitalio.Pull.UP

BTN2 = digitalio.DigitalInOut(board.BTN2)
BTN2.direction = digitalio.Direction.INPUT
BTN2.pull = digitalio.Pull.UP

# Hold BTN1 and BTN2 during reboot to update
if not BTN1.value and not BTN2.value:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=False)
    with open("updater_out.txt", "w") as sys.stdout:
        updater.run(debug=True)
    microcontroller.reset()

# Uncomment to for updater testing
#storage.remount("/", readonly=False, disable_concurrent_write_protection=False)