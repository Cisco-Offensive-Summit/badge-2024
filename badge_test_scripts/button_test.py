import asyncio
from badge.neopixels import NP
import badge.buttons
import badge.events as evt
from badge.events import on
from badge.colors import *


@on(evt.BTN_A_PRESSED)
def a_pressed(event):
  NP[0] = BLUE
  NP.show()

@on(evt.BTN_B_PRESSED)
def b_pressed(event):
  NP[1] = BLUE
  NP.show()

@on(evt.BTN_C_PRESSED)
def c_pressed(event):
  NP[2] = BLUE
  NP.show()

@on(evt.BTN_D_PRESSED)
def d_pressed(event):
  NP[3] = BLUE
  NP.show()

@on(evt.BTN_A_RELEASED)
def a_released(event):
  NP[0] = OFF
  NP.show()

@on(evt.BTN_B_RELEASED)
def b_released(event):
  NP[1] = OFF
  NP.show()

@on(evt.BTN_C_RELEASED)
def c_released(event):
  NP[2] = OFF
  NP.show()

@on(evt.BTN_D_RELEASED)
def d_released(event):
  NP[3] = OFF
  NP.show()

def run():
  asyncio.run(main())

async def main():
  button_tasks = badge.buttons.start_tasks(interval=0.05)
  event_tasks = evt.start_tasks()
  all_tasks = [ ] + button_tasks + event_tasks
  await asyncio.gather(*all_tasks)

run()

