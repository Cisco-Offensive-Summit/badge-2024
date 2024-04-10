"""Event thing to run callbacks in asyncio loop"""
import asyncio

from .log import dbg, log

_COROS = list()
DEBUG = False

def start_tasks():
    return [asyncio.create_task(t) for t in _COROS]


def on(evt):
    """Decorator that takes an event as an argument. This is a convenience
    decorator. It creates a coroutine from the input function, then adds it
    to the TASKS module global, which is used in the asyncio run loop.
    The task is a wrapper around the input function that simply waits for
    the event given as an argument to the decorator.
    Callbacks should take a single argument, the event. Events may have
    extra data added to them, which will be available in the callback.
    """
    global _COROS

    def outer(func):
        async def _task():
            while True:
                await evt.wait()
                DEBUG and dbg("on-event", evt)
                ret = func(evt)
                DEBUG and dbg("on-event", evt, "ret=", ret)

        _COROS.append(_task())

        return func  # return original function here instead of wrapped one

    return outer


class Event:
    """A lightweight wrapper around an asyncio.event . Event producers
    call fire(), and user of the above decorator use @on(<event>) to set up
    for use as  task in the asyncio loop. When the event is fired, all the
    tasks that have awaited the event will be called with the event as the
    argument. Each callback should see the same event instance since these
    are module level globals.
    """

    def __init__(self, name, **kwargs):
        self._name = name
        self._event = asyncio.Event()
        self._kwargs = kwargs
        self.data = dict()

    def fire(self, data=None):
        DEBUG and dbg("fire",repr(self),repr(data))
        if data is None:
            self.data = dict()
        self.data = data
        self._event.set()
        self._event.clear()

    def __repr__(self):
        return f"<{self._name}>"

    async def wait(self):
        # XXX: add timeout
        return await self._event.wait()

# Wait on a list of events, then fire output event
async def event_sequence(input_events:list[Event], output_event:Event):
    for evt in input_events:
        await evt.wait()
    output_event.fire()

# Wait on a group of Events and output one event with the trigger
async def any_event(input_events:list[Event], output_event:Event = None):
    trigger_evt = None
    group_evt = asyncio.Event()
    async def _wt(in_evt):
        nonlocal trigger_evt
        await in_evt.wait()
        trigger_evt = in_evt
        group_evt.set()
    tasks = [asyncio.create_task(_wt(in_evt)) for in_evt in input_events]
    try:
        await group_evt.wait()
    finally:
        group_evt.clear()
        for task in tasks:
            task.cancel()
    if output_event:
        output_event.fire(data = { "event" : trigger_evt})
    return trigger_evt


BTN_A_PRESSED = Event("btn-a-pressed")
BTN_A_RELEASED = Event("btn-a-released")
BTN_B_PRESSED = Event("btn-b-pressed")
BTN_B_RELEASED = Event("btn-b-released")
BTN_C_PRESSED = Event("btn-c-pressed")
BTN_C_RELEASED = Event("btn-c-released")
BTN_D_PRESSED = Event("btn-d-pressed")
BTN_D_RELEASED = Event("btn-d-released")
ANY_BTN_PRESSED = Event("any-button-pressed")
ANY_BTN_RELEASED = Event("any-button-released")
ALL_BTNS_SETTLED = Event("all-buttons-settled")
DISPLAY_ROTATED = Event("display-rotated")
WIFI_CONNECTED = Event("wifi-connected")
WIFI_DISCONNECTED = Event("wifi-disconnected")
LOW_BATTERY = Event("low-battery")
BATTERY_READ = Event("battery-read")
WILL_BLOCK = Event("will-block")
TCP_CONNECTED = Event("tcp-connected")
TCP_DISCONNECTED = Event("tcp-disconnected")
TCP_GOT_DATA = Event("tcp-got-data")
BTN_A_DOWNUP = Event("btn-a-downup")
BTN_B_DOWNUP = Event("btn-b-downup")
BTN_C_DOWNUP = Event("btn-c-downup")
BTN_D_DOWNUP = Event("btn-d-downup")
ANY_BTN_DOWNUP = Event("any-button-downup")
