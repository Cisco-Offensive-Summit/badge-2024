/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2023 Bill Sideris, independently providing these changes.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#define MICROPY_HW_BOARD_NAME 		"Offensive Summit Badge 2024"
#define MICROPY_HW_MCU_NAME 		"ESP32S3"

#define CIRCUITPY_DISPLAY_LIMIT 	(2)

#define MICROPY_HW_NEOPIXEL 		(&pin_GPIO5)
#define CIRCUITPY_STATUS_LED_POWER 	(&pin_GPIO48)
#define MICROPY_HW_NEOPIXEL_COUNT	(4)

#define MICROPY_HW_LED_STATUS 		(&pin_GPIO6)

#define DEFAULT_I2C_BUS_SCL		(&pin_GPIO3)
#define DEFAULT_I2C_BUS_SDA		(&pin_GPIO4)

#define DEFAULT_UART_BUS_RX 		(&pin_GPIO44)
#define DEFAULT_UART_BUS_TX 		(&pin_GPIO43)

#define DOUBLE_TAP_PIN 			(&pin_GPIO0)
