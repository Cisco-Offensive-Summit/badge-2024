#include "shared-bindings/board/__init__.h"
#include "shared-module/displayio/__init__.h"

STATIC const mp_rom_map_elem_t board_module_globals_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS

    // Left side, module facing up.
    { MP_ROM_QSTR(MP_QSTR_GPIO4),   MP_ROM_PTR(&pin_GPIO4)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO5),   MP_ROM_PTR(&pin_GPIO5)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO6),   MP_ROM_PTR(&pin_GPIO6)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO7),   MP_ROM_PTR(&pin_GPIO7)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO15),   MP_ROM_PTR(&pin_GPIO15) },
    { MP_ROM_QSTR(MP_QSTR_GPIO16),   MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_GPIO17),   MP_ROM_PTR(&pin_GPIO17) },
    { MP_ROM_QSTR(MP_QSTR_GPIO18),   MP_ROM_PTR(&pin_GPIO18) },
    { MP_ROM_QSTR(MP_QSTR_GPIO8),   MP_ROM_PTR(&pin_GPIO8)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO19),   MP_ROM_PTR(&pin_GPIO19)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO20),   MP_ROM_PTR(&pin_GPIO20)  },


    // Bottom, module facing up
    { MP_ROM_QSTR(MP_QSTR_GPIO3),   MP_ROM_PTR(&pin_GPIO3)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO46),   MP_ROM_PTR(&pin_GPIO46)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO9),   MP_ROM_PTR(&pin_GPIO9)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO10),   MP_ROM_PTR(&pin_GPIO10)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO11),   MP_ROM_PTR(&pin_GPIO11)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO12),   MP_ROM_PTR(&pin_GPIO12)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO13),   MP_ROM_PTR(&pin_GPIO13)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO14),   MP_ROM_PTR(&pin_GPIO14)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO21),   MP_ROM_PTR(&pin_GPIO21)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO47),   MP_ROM_PTR(&pin_GPIO47)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO48),   MP_ROM_PTR(&pin_GPIO48)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO45),   MP_ROM_PTR(&pin_GPIO45)  },


    // Right side, module facing up
    { MP_ROM_QSTR(MP_QSTR_GPIO1),   MP_ROM_PTR(&pin_GPIO1)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO2),   MP_ROM_PTR(&pin_GPIO2)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO43),   MP_ROM_PTR(&pin_GPIO43)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO44),   MP_ROM_PTR(&pin_GPIO44)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO42),   MP_ROM_PTR(&pin_GPIO42)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO41),   MP_ROM_PTR(&pin_GPIO41)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO40),   MP_ROM_PTR(&pin_GPIO40)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO39),   MP_ROM_PTR(&pin_GPIO39)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO38),   MP_ROM_PTR(&pin_GPIO38)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO37),   MP_ROM_PTR(&pin_GPIO37)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO36),   MP_ROM_PTR(&pin_GPIO36)  },
    { MP_ROM_QSTR(MP_QSTR_GPIO35),   MP_ROM_PTR(&pin_GPIO35)  },
    // Should not use our boot pin as GPIO.... probably
    //{ MP_ROM_QSTR(MP_QSTR_GPIO0),   MP_ROM_PTR(&pin_GPIO0)  },
    
    
    // Friendly name defines
    //  Uart
    { MP_ROM_QSTR(MP_QSTR_TX),   MP_ROM_PTR(&pin_GPIO43)  },
    { MP_ROM_QSTR(MP_QSTR_RX),   MP_ROM_PTR(&pin_GPIO44)  },
    { MP_ROM_QSTR(MP_QSTR_UART),   MP_ROM_PTR(&board_uart_obj)  },
    //  I2C Stemma
    { MP_ROM_QSTR(MP_QSTR_SCL), MP_ROM_PTR(&pin_GPIO3) },
    { MP_ROM_QSTR(MP_QSTR_SDA), MP_ROM_PTR(&pin_GPIO4) },
    { MP_ROM_QSTR(MP_QSTR_I2C), MP_ROM_PTR(&board_i2c_obj) },
    { MP_ROM_QSTR(MP_QSTR_STEMMA_I2C), MP_ROM_PTR(&board_i2c_obj) },
    //  NeoPixel
    { MP_ROM_QSTR(MP_QSTR_NEOPIXEL),   MP_ROM_PTR(&pin_GPIO5)  },
    { MP_ROM_QSTR(MP_QSTR_NEOPIXEL_POWER_INVERTED),   MP_ROM_PTR(&pin_GPIO48)  },
    //  Buttons
    { MP_ROM_QSTR(MP_QSTR_BOOT),   MP_ROM_PTR(&pin_GPIO0)  },
    { MP_ROM_QSTR(MP_QSTR_BTN1),   MP_ROM_PTR(&pin_GPIO7)  },
    { MP_ROM_QSTR(MP_QSTR_BTN2),   MP_ROM_PTR(&pin_GPIO15) },
    { MP_ROM_QSTR(MP_QSTR_BTN3),   MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_BTN4),   MP_ROM_PTR(&pin_GPIO17) },
    //  TFT Display
    { MP_ROM_QSTR(MP_QSTR_TFT_RST),   MP_ROM_PTR(&pin_GPIO8)  },
    { MP_ROM_QSTR(MP_QSTR_TFT_CS),   MP_ROM_PTR(&pin_GPIO10)  },
    { MP_ROM_QSTR(MP_QSTR_TFT_MOSI),   MP_ROM_PTR(&pin_GPIO11)  },
    { MP_ROM_QSTR(MP_QSTR_TFT_CLKS),   MP_ROM_PTR(&pin_GPIO12)  },
    { MP_ROM_QSTR(MP_QSTR_TFT_DC),   MP_ROM_PTR(&pin_GPIO13)  },
    { MP_ROM_QSTR(MP_QSTR_DISPLAY_OLED), MP_ROM_PTR(&displays[0].display) },
    
};
MP_DEFINE_CONST_DICT(board_module_globals, board_module_globals_table);
