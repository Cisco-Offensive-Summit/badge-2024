# SPDX-FileCopyrightText: Copyright (c) 2023 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Written by Liz Clark (Adafruit Industries) with OpenAI ChatGPT v4 September 25, 2023 build
# https://help.openai.com/en/articles/6825453-chatgpt-release-notes

# https://chat.openai.com/share/36910a8a-dfce-4c68-95fe-978721c697c9
"""
`adafruit_ad569x`
================================================================================

CircuitPython module for the AD5691/2/3 I2C DAC


* Author(s): Liz Clark

Implementation Notes
--------------------

**Hardware:**

* Adafruit `AD5693R Breakout Board - 16-Bit DAC with I2C Interface - STEMMA QT / qwiic
  <https://www.adafruit.com/product/5811>`_ (Product ID: 5811)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

"""

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AD569x.git"

_NOP = const(0x00)
_WRITE_DAC_AND_INPUT = const(0x30)
_WRITE_CONTROL = const(0x40)


# pylint: disable=broad-exception-raised
class Adafruit_AD569x:
    """Class which provides interface to AD569x Dac."""

    def __init__(self, i2c: I2C, address: int = 0x4C) -> None:
        """
        Initialize the AD569x device.

        This function initializes the I2C device, performs a soft reset,
        and sets the initial operating mode,
        reference voltage, and gain settings.

        :param i2c: The I2C bus.
        :param address: The I2C address of the device. Defaults to 0x4C.
        """
        self.i2c_device = I2CDevice(i2c, address)
        self.normal_mode = const(0x00)
        """
        Normal mode
        """
        self.output_1k_impedance = const(0x01)
        """
        1K impedance mode
        """
        self.output_100k_impedance = const(0x02)
        """
        100K impedance mode
        """
        self.output_tristate = const(0x03)
        """
        Tri-state mode
        """

        try:
            self.reset()
            self._mode = self.normal_mode
            self._internal_reference = True
            self._gain = False
            self._update_control_register()
        except OSError as error:
            raise OSError(f"Failed to initialize AD569x, {error}") from error

    def _send_command(self, command: int, data: int) -> None:
        """
        Send a command and data to the I2C device.

        This internal function prepares a 3-byte buffer containing the command and data,
        and writes it to the I2C device.

        :param command: The command byte to send.
        :param data: The 16-bit data to send.
        """
        try:
            high_byte = (data >> 8) & 0xFF
            low_byte = data & 0xFF
            buffer = bytearray([command, high_byte, low_byte])
            try:
                with self.i2c_device as i2c:
                    i2c.write(buffer)
            except Exception:  # pylint: disable=broad-exception-caught
                with self.i2c_device as i2c:
                    i2c.write(buffer, end=False)
        except Exception as error:
            raise Exception(f"Error sending command: {error}") from error

    def _update_control_register(self):
        data = 0x0000
        data |= self._mode << 13
        data |= not self._internal_reference << 12
        data |= self._gain << 11
        self._send_command(_WRITE_CONTROL, data)

    @property
    def mode(self):
        """
        Operating mode for the AD569x chip.

        :param value: An int containing new operating mode.
        """
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        if new_mode not in [0, 1, 2, 3]:
            raise ValueError(
                "Mode must be normal_mode, output_1k_impedance,"
                + "output_100k_impedance or output_tristate"
            )
        self._mode = new_mode
        self.reset()
        self._update_control_register()

    @property
    def internal_reference(self):
        """
        Internal reference voltage for the AD569x chip.

        :param value: A bool to enable the internal reference voltage.
        """
        return self._internal_reference

    @internal_reference.setter
    def internal_reference(self, value):
        self._internal_reference = value
        self.reset()
        self._update_control_register()

    @property
    def gain(self):
        """
        Gain for the AD569x chip.

        :param value: A bool to choose 1X or 2X gain.
        """
        return self._gain

    @gain.setter
    def gain(self, value):
        self._gain = value
        self.reset()
        self._update_control_register()

    @property
    def value(self) -> int:
        """
        16-bit value to the input register and update the DAC register.

        This property writes a 16-bit value to the input register and then updates
        the DAC register of the AD569x chip in a single operation.
        """
        return self.value

    @value.setter
    def value(self, val: int) -> None:
        self._send_command(_WRITE_DAC_AND_INPUT, val)

    def reset(self):
        """
        Soft-reset the AD569x chip.
        """
        reset_command = 0x8000
        try:
            self._send_command(_WRITE_CONTROL, reset_command)
        except Exception as error:
            raise Exception(f"Error during reset: {error}") from error
