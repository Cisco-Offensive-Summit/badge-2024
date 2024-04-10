import asyncio
import board
from digitalio import DigitalInOut
from digitalio import Direction
from digitalio import Pull

from .events import (  # ALL_BTNS_SETTLED,;
    ANY_BTN_DOWNUP,
    ANY_BTN_PRESSED,
    ANY_BTN_RELEASED,
    BTN_A_DOWNUP,
    BTN_A_PRESSED,
    BTN_A_RELEASED,
    BTN_B_DOWNUP,
    BTN_B_PRESSED,
    BTN_B_RELEASED,
    BTN_C_DOWNUP,
    BTN_C_PRESSED,
    BTN_C_RELEASED,
    BTN_D_DOWNUP,
    BTN_D_PRESSED,
    BTN_D_RELEASED,
    any_event,
    event_sequence,
)

class Button:
    def __init__(self, name, press_event, release_event, getstate_func):
        self.name = name
        self.getstate_func = getstate_func
        self.current_state = getstate_func()
        self.unpressed_state = self.current_state
        self.press_event = press_event
        self.release_event = release_event

    def __repr__(self):
        return f"Button({self.name})"

    def _produce_events(self):
        new = self.getstate_func()

        # Didn't change, it's unpressed, so do nothing
        if new == self.current_state:
            return None

        # Changed to unpressed, trigger release event
        if new == self.unpressed_state:
            self.release_event.fire()
            ANY_BTN_RELEASED.fire(data={"name" : self.name})
        #  Changed to pressed, trigger pressed event
        else:
            self.press_event.fire()
            ANY_BTN_PRESSED.fire(data={"name" : self.name})
        # Update current state
        self.current_state = new

    async def run(self, interval=0.0):
        while True:
            self._produce_events()
            await asyncio.sleep(interval)  # human speed


button_pins = [board.BTN1, board.BTN2, board.BTN3, board.BTN4]
buttons = []
if hasattr(board, "BOOT"):
    button_pins.append(board.BOOT)

for pin in button_pins:
    switch = DigitalInOut(pin)
    switch.direction = Direction.INPUT
    switch.pull = Pull.UP
    buttons.append(switch)

def a_pressed():
    return not buttons[3].value


def b_pressed():
    return not buttons[2].value


def c_pressed():
    return not buttons[1].value


def d_pressed():
    return not buttons[0].value


BTN_A = Button("A", BTN_A_PRESSED, BTN_A_RELEASED, a_pressed)
BTN_B = Button("B", BTN_B_PRESSED, BTN_B_RELEASED, b_pressed)
BTN_C = Button("C", BTN_C_PRESSED, BTN_C_RELEASED, c_pressed)
BTN_D = Button("D", BTN_D_PRESSED, BTN_D_RELEASED, d_pressed)

BUTTONS = [BTN_A, BTN_B, BTN_C, BTN_D]


def start_tasks(interval=0.0):
    t = [asyncio.create_task(b.run(interval)) for b in BUTTONS]
    return t


def get_tasks(interval=0.0):
    t = [ b.run(interval) for b in BUTTONS ]
    return t 

# These fire when the same button gets pressed and released
def get_downup_tasks(interval=0.0):

    # _f is a coro
    async def _loop(_f, *args, **kwargs):
        while True:
            output = await _f(*args, **kwargs)

    downup_single_buttons = [
        _loop(event_sequence,[BTN_A_PRESSED, BTN_A_RELEASED], BTN_A_DOWNUP),
        _loop(event_sequence,[BTN_B_PRESSED, BTN_B_RELEASED], BTN_B_DOWNUP),
        _loop(event_sequence,[BTN_C_PRESSED, BTN_C_RELEASED], BTN_C_DOWNUP),
        _loop(event_sequence,[BTN_D_PRESSED, BTN_D_RELEASED], BTN_D_DOWNUP)
    ]
    
    downup_any_button = _loop(any_event,
        [ BTN_A_DOWNUP, BTN_B_DOWNUP, BTN_C_DOWNUP, BTN_D_DOWNUP ],
        ANY_BTN_DOWNUP
    )

    return downup_single_buttons + [ downup_any_button]


def start_downup_tasks(interval=0.0):
    t = [ asyncio.create_task(t) for t in get_downup_tasks(interval) ]
    return t

# await this to get the next button pressed
async def any_button_downup():
    await ANY_BTN_DOWNUP.wait()
    return ANY_BTN_DOWNUP.data.get("event", None)

def all_tasks(interval=0.0):
    return start_tasks() + start_downup_tasks()
