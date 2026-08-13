"""RGB LED status feedback via 3 GPIO pins on the button's common-anode
RGB LED: red (physical pin 15), green (physical pin 13), blue (physical
pin 18). The shared anode is wired straight to a 5V pin (physical pin 2
or 4), not to a GPIO pin -- the Jetson's GPIO can't source enough current
to light the LED brightly (see BUTTON_WIRING.md). Same physical pins on
both the Raspberry Pi and the Jetson Nano's J41 header. Uses Jetson.GPIO
in BOARD mode, since gpiozero doesn't support Jetson boards.
"""

import random
import threading

import Jetson.GPIO as GPIO

_RED_PIN = 15
_GREEN_PIN = 13
_BLUE_PIN = 18


class LedStatus:
    """Sets the RGB button LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack, blink_seconds=0.3):
        self._blink_seconds = blink_seconds
        GPIO.setmode(GPIO.BOARD)
        for pin in (_RED_PIN, _GREEN_PIN, _BLUE_PIN):
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        exit_stack.callback(GPIO.cleanup, [_RED_PIN, _GREEN_PIN, _BLUE_PIN])
        self._pattern_thread = None
        self._stop_pattern = None

    def listening(self):
        self._stop_blinking()
        self._show(_RED_PIN)

    def thinking(self):
        # Random flicker between red/blue, R2-D2's classic "processing" look.
        self._start_blinking([_RED_PIN, _BLUE_PIN])

    def ready(self):
        self._stop_blinking()
        self._show(None)

    def _show(self, pin):
        # Common-anode cathodes: LOW lights the LED, HIGH turns it off.
        for p in (_RED_PIN, _GREEN_PIN, _BLUE_PIN):
            GPIO.output(p, GPIO.LOW if p == pin else GPIO.HIGH)

    def _start_blinking(self, pins):
        if self._pattern_thread:
            return
        self._stop_pattern = threading.Event()

        def _run():
            while not self._stop_pattern.is_set():
                self._show(random.choice(pins))
                self._stop_pattern.wait(self._blink_seconds)
            self._show(None)

        self._pattern_thread = threading.Thread(target=_run, daemon=True)
        self._pattern_thread.start()

    def _stop_blinking(self):
        if self._pattern_thread:
            self._stop_pattern.set()
            self._pattern_thread.join()
            self._pattern_thread = None
