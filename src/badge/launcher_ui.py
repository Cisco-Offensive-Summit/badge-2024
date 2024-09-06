import adafruit_imageload
import displayio
from adafruit_bitmap_font.bitmap_font import load_font
from adafruit_display_text.scrolling_label import ScrollingLabel
from displayio import Group, TileGrid

from badge.app import App
from badge.colors import SITE_BLUE
from badge.screens import EPD
from badge.screens import LCD
from badge.screens import clear_lcd_screen
from badge.screens import clear_epd_screen
from badge.screens import epd_round_button

EPD_DISP_H = EPD.height
EPD_DISP_W = EPD.width
LCD_DISP_H = LCD.height
LCD_DISP_W = LCD.width
ICON_H = 76
ICON_W = 128
FONT = load_font('font/font.pcf')


def display_lcd_app_icon(app: App):
  icon = app.icon_file
  app_name = app.app_name
  meta = app.metadata_json
  text = f"{meta['app_name']}   Created By: {meta['author']}          "

  clear_lcd_screen(LCD.root_group)

  group = Group()  
  background = displayio.Bitmap(128, 128, 1)
  palette1 = displayio.Palette(1)
  palette1[0] = SITE_RED
  bitmap, palette2 = adafruit_imageload.load(icon,bitmap=displayio.Bitmap,palette=displayio.Palette)
  tile_grid1 = TileGrid(background, pixel_shader=palette1)
  tile_grid2 = TileGrid(bitmap, pixel_shader=palette2)
  label = ScrollingLabel(font=FONT, text=text, max_characters=13, animate_time=0.2)
  y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  label.x = 5
  label.y = LCD_DISP_H-((LCD_DISP_H-ICON_H)//2)
  LCD.root_group = group
  group.append(tile_grid1)
  group.append(tile_grid2)
  group.append(label)

  return label

def draw_epd_launch_screen():
  B1 = "S4 Next App"
  B2 = "S7 Launch"
  SUMMIT = "Offensive Summit 2024"
  HEADER = "Select An App"
  scale = 2
  button_rad = 5
  SUMMIT_x = (EPD_DISP_W //2) - (EPD._font.width(SUMMIT) // 2)
  SUMMIT_y = 1
  HEADER_x = (EPD_DISP_W //2) - ((EPD._font.width(HEADER) * scale) // 2)
  HEADER_y = (EPD_DISP_H //2) - ((EPD._font.font_height * scale) // 2)
  B1_x = 5 + button_rad
  B1_y = EPD_DISP_H - 5 - button_rad - EPD._font.font_height
  B2_x = EPD_DISP_W - 5 - button_rad - EPD._font.width(B2)
  B2_y = EPD_DISP_H - 5 - button_rad - EPD._font.font_height
  clear_epd_screen()
  EPD.text(SUMMIT,SUMMIT_x,SUMMIT_y,1,size=1)
  EPD.text(HEADER,HEADER_x,HEADER_y,1,size=scale)
  epd_round_button(B1, B1_x, B1_y, 5)
  epd_round_button(B2, B2_x, B2_y, 5)
  EPD.draw()
