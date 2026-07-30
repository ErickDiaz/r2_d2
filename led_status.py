"""LED status feedback, wired to physical pin 22 of the 40-pin header --
same physical position on both the Raspberry Pi and the Jetson Nano's J41
header (see BUTTON_WIRING.md). Uses Jetson.GPIO in BOARD mode, since
gpiozero doesn't support Jetson boards.
"""

import threading

import Jetson.GPIO as GPIO

_PIN = 22
_BLINK_SECONDS = 0.3


class LedStatus:
    """Sets the button LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack, pin=_PIN):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        exit_stack.callback(GPIO.cleanup, pin)
        self._blink_thread = None
        self._stop_blink = None

    def listening(self):
        self._stop_blinking()
        GPIO.output(self._pin, GPIO.HIGH)

    def thinking(self):
        self._start_blinking()

    def ready(self):
        self._stop_blinking()
        GPIO.output(self._pin, GPIO.LOW)

    def _start_blinking(self):
        if self._blink_thread:
            return
        self._stop_blink = threading.Event()

        def _run():
            state = False
            while not self._stop_blink.is_set():
                state = not state
                GPIO.output(self._pin, GPIO.HIGH if state else GPIO.LOW)
                self._stop_blink.wait(_BLINK_SECONDS)

        self._blink_thread = threading.Thread(target=_run, daemon=True)
        self._blink_thread.start()

    def _stop_blinking(self):
        if self._blink_thread:
            self._stop_blink.set()
            self._blink_thread.join()
            self._blink_thread = None
