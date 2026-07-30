"""Physical push-to-talk button, wired to physical pin 16 of the 40-pin
header -- same physical position on both the Raspberry Pi and the Jetson
Nano's J41 header (see BUTTON_WIRING.md). Uses Jetson.GPIO in BOARD mode,
since gpiozero doesn't support Jetson boards.
"""

import Jetson.GPIO as GPIO

_PIN = 16


class PushToTalkButton:
    """Wraps a momentary button wired to physical pin 16, pulled up (button
    presses connect the pin to GND)."""

    def __init__(self, pin=_PIN):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    @property
    def is_pressed(self):
        return GPIO.input(self._pin) == GPIO.LOW
