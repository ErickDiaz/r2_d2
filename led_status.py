"""RGB LED status feedback via 4 GPIO pins on the button's common-anode
RGB LED: shared anode (physical pin 22 / BCM25) plus three individual
color cathodes -- red (physical pin 15 / BCM22), green (physical pin 13 /
BCM27), blue (physical pin 18 / BCM24). See BUTTON_WIRING.md for wiring
and how these pins were identified.
"""

import random
import threading

from gpiozero import LED

_COMMON_PIN = 25
_RED_PIN = 22
_GREEN_PIN = 27
_BLUE_PIN = 24


class LedStatus:
    """Sets the RGB button LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack, blink_seconds=0.3):
        self._blink_seconds = blink_seconds
        self._common = exit_stack.enter_context(LED(_COMMON_PIN))
        self._common.on()
        self._red = exit_stack.enter_context(LED(_RED_PIN, active_high=False))
        self._green = exit_stack.enter_context(LED(_GREEN_PIN, active_high=False))
        self._blue = exit_stack.enter_context(LED(_BLUE_PIN, active_high=False))
        self._pattern_thread = None
        self._stop_pattern = None

    def listening(self):
        self._stop_blinking()
        self._show(self._red)

    def thinking(self):
        # Random flicker between red/blue, R2-D2's classic "processing" look.
        self._start_blinking([self._red, self._blue])

    def ready(self):
        self._stop_blinking()
        self._show(None)

    def _show(self, led):
        for color in (self._red, self._green, self._blue):
            color.off()
        if led:
            led.on()

    def _start_blinking(self, leds):
        if self._pattern_thread:
            return
        self._stop_pattern = threading.Event()

        def _run():
            while not self._stop_pattern.is_set():
                self._show(random.choice(leds))
                self._stop_pattern.wait(self._blink_seconds)
            self._show(None)

        self._pattern_thread = threading.Thread(target=_run, daemon=True)
        self._pattern_thread.start()

    def _stop_blinking(self):
        if self._pattern_thread:
            self._stop_pattern.set()
            self._pattern_thread.join()
            self._pattern_thread = None
