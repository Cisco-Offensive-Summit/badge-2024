import time

import adafruit_imageload
import board
import displayio
import terminalio
from adafruit_bitmap_font.bitmap_font import load_font
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_text.label import Label
from adafruit_display_text.scrolling_label import ScrollingLabel
from displayio import Group, TileGrid

from badge.app import App
from badge.buttons import any_button_downup
from badge.colors import SITE_BLUE
from badge.fileops import diskspace_str
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import clear_lcd_screen
from badge.screens import clear_epd_screen

# from .app import APPLIST
from .colors import *
from .log import log

EPD_DISP_H = EPD.height
EPD_DISP_W = EPD.width
LCD_DISP_H = LCD.height
LCD_DISP_W = LCD.width
ICON_H = 76
ICON_W = 128
FONT = load_font('font/font.pcf')


def refresh():
    refreshed = False
    while not refreshed:
        try:
            board.DISPLAY.refresh()
            refreshed = True
        except RuntimeError:
            time.sleep(board.DISPLAY.time_to_refresh + 0.1)
    return

def display_lcd_app_icon(app: App):
  icon = app.icon_file
  app_name = app.app_name
  meta = app.metadata_json
  text = f"{meta['app_name']}   Created By: {meta['author']}          "

  clear_lcd_screen(LCD.root_group)

  group = Group()  
  background = displayio.Bitmap(128, 128, 1)
  palette1 = displayio.Palette(1)
  palette1[0] = SITE_BLUE
  bitmap, palette2 = adafruit_imageload.load(icon,bitmap=displayio.Bitmap,palette=displayio.Palette)
  tile_grid1 = TileGrid(background, pixel_shader=palette1)
  tile_grid2 = TileGrid(bitmap, pixel_shader=palette2)
  label = ScrollingLabel(font=FONT, text=text, max_characters=13, animate_time=0.2)
  print(LCD_DISP_H)
  print(ICON_H)
  y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  print(y)
  label.x = 5
  label.y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  LCD.root_group = group
  group.append(tile_grid1)
  group.append(tile_grid2)
  group.append(label)

  return label



def render_main(app_entries):
    # log("render_main", app_entries)
    group = main_group(app_entries)
    board.DISPLAY.show(group)
    refresh()


def main_group(app_entries):
    main = Group()
    main.append(background(0, 0))
    main.append(button_row(1, 107))
    main.append(topbar(0, 0))
    main.append(indicators(3, 18))
    main.append(icon_pane(12, 18, app_entries))
    return main


def indicators(x, y):
    g = Group(x=x, y=y)
    g_steady = Group(x=0, y=20)
    steady_bmp = load_bitmap("/badge/img/steady.bmp")
    g_steady.append(steady_bmp)
    g.append(g_steady)
    g_pulse = Group(x=0, y=60)
    pulse_bmp = load_bitmap("/badge/img/pulse.bmp")
    g_pulse.append(pulse_bmp)
    g.append(g_pulse)
    return g


def load_bitmap(filename):
    bmp, pal = adafruit_imageload.load(filename)
    tg = TileGrid(bmp, pixel_shader=pal)
    return tg


def icon_pane(x, y, app_entries):
    # log("icon_pane", app_entries)
    g = Group(x=x, y=y)
    w, h = ICON_W, ICON_H
    spacing = 3
    # bounding box
    ICON_BB_W, ICON_BB_H = w + spacing, h + spacing

    for row in (0, 1):
        y_offset = row*(ICON_BB_H)
        for col in (0, 1, 2, 3):
            x_offset = (col*(ICON_BB_W))
            # Create outside box
            box_g = Group(x=x_offset, y=y_offset)
            box_g.append(r_rect(0, 0))  # x_offset, y_offset))
            # Create icon with small offset inside box
            icon_g = Group(x=2, y=2)
            icon_index = (row*4)+col
            icon_file = app_entries[icon_index].icon_file
            # log("icon_file", icon_index, icon_file)
            icon_g.append(load_bitmap(icon_file))
            box_g.append(icon_g)
            g.append(box_g)

    return g


def r_rect(x, y, width=ICON_W, height=ICON_H, round=3):
    g = Group(x=x, y=y)
    g.append(RoundRect(0, 0, width, height, round, fill=WHITE,
                       outline=DARKGRAY, stroke=2))
    return g


def topbar(x, y):
    g = Group(x=x, y=y)
    r = Rect(0, 0, 295, 12, fill=WHITE)
    li = Line(0, 13, 295, 13, DARKGRAY)
    disk_str = diskspace_str()
    disk_label = Label(terminalio.FONT, text=disk_str, color=BLACK, scale=1)
    disk_label.anchored_position = (2,0)
    disk_label.anchor_point = (0,0)
    g.append(r)
    g.append(disk_label)
    g.append(li)
    return g


def button_row(x, y):
    g = Group(x=x, y=y)
    # A
    next_button = text_button(0, 0, 54, 20, "Next >>")
    g.append(next_button)
    # B
    launch_button = text_button(296-54-18, 0, 60, 20, "Launch !")
    g.append(launch_button)

    return g


def text_button(x, y, width, height, text):
    b1 = Group(x=x, y=y)
    b1.append(RoundRect(0, 0, width, height, 6, outline=BLACK, fill=WHITE))
    t1 = Label(terminalio.FONT, text=text, color=BLACK)
    t1.anchored_position = (width/2, height/2)  # center of Rectangle
    t1.anchor_point = (0.5, 0.5)
    b1.append(t1)
    return b1


def background(x, y):
    g = Group(x=x, y=y)
    g.append(Rect(0, 0, 296, 128, fill=LIGHTGRAY, outline=WHITE))
    return g
