# SPDX-FileCopyrightText: 2021 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# buttons_pybadge.py
# 2023-07-02 v2.0.0

import board
import time
import keypad
from digitalio import DigitalInOut
from analogio import AnalogIn
import displayio
from adafruit_display_shapes.rect import Rect
from simpleio import tone


class Buttons:
    def __init__(self):
        """Instantiate the air monitor button decoder for the
        PyBadge/PyGamer/EdgeBadge device. Builds displayio button group."""

        self._timeout = 1
        self._WIDTH = board.DISPLAY.width
        self._HEIGHT = board.DISPLAY.height

        # Initialize ShiftRegisterKeys to read PyGamer/PyBadge buttons
        self._panel = keypad.ShiftRegisterKeys(
            clock=board.BUTTON_CLOCK,
            data=board.BUTTON_OUT,
            latch=board.BUTTON_LATCH,
            key_count=8,
            value_when_pressed=True,
            max_events = 1,
        )

        # Define and instantiate front panel buttons
        self._BUTTON_CALIBRATE = 2  # START
        self._BUTTON_LANGUAGE = 1  # A
        self._BUTTON_TEMPERATURE = 3  # SELECT

        # Build displayio button group
        self._button_group = displayio.Group()
        self.language_button = Rect(
            x=1,
            y=1,
            width=self._WIDTH - 20,
            height=int(self._HEIGHT * 0.25),
            fill=None,
            outline=0x000000,
            stroke=1,
        )
        self._button_group.append(self.language_button)
        self.language_button.outline = None

        self.calibrate_button = Rect(
            x=int((self._WIDTH - 20) * 0.25),
            y=int(self._HEIGHT * 0.33),
            width=int((self._WIDTH - 20) / 2),
            height=int(self._HEIGHT * 0.33),
            fill=None,
            outline=0x000000,
            stroke=1,
        )
        self._button_group.append(self.calibrate_button)
        self.calibrate_button.outline = None

        self.temperature_button = Rect(
            x=1,
            y=int(self._HEIGHT * 0.75) - 1,
            width=self._WIDTH - 20,
            height=int(self._HEIGHT * 0.25),
            fill=None,
            outline=0x000000,
            stroke=1,
        )
        self._button_group.append(self.temperature_button)
        self.temperature_button.outline = None
        return

    @property
    def button_display_group(self):
        """Displayio button group."""
        return self._button_group

    @property
    def timeout(self):
        """Button timeout duration setting."""
        return self._timeout

    @timeout.setter
    def timeout(self, hold_time=1.0):
        """Select timeout duration value in seconds, positive float value."""
        if hold_time < 0 or hold_time >= 10:
            print('Invalid button timeout duration value. Must be between 0 and 10 seconds.')
            return
        self._timeout = hold_time
        return

    def read_buttons(self):
        self._button_pressed = None
        # See if a panel button is pressed
        self._buttons = self._panel.events.get()
        if self._buttons and self._buttons.pressed:
            if self._buttons.key_number == self._BUTTON_CALIBRATE:
                self._button_pressed = 'calibrate'
                self.calibrate_button.outline = 0x0000FF
            if self._buttons.key_number == self._BUTTON_LANGUAGE:
                self._button_pressed = 'language'
                self.language_button.outline = 0x0000FF
            if self._buttons.key_number == self._BUTTON_TEMPERATURE:
                self._button_pressed = 'temperature'
                self.temperature_button.outline = 0x0000FF

            if self._button_pressed is not None:
                tone(board.A0, 1175, 0.030)  # D6
                time.sleep(0.25)

            self.calibrate_button.outline = None
            self.language_button.outline = None
            self.temperature_button.outline = None
        return self._button_pressed, 1.0
