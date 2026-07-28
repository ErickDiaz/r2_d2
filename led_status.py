"""LED status feedback for the AIY Voice Bonnet's button LED, wired
directly to the Pi's GPIO (BCM 25) -- bypasses the HAT's own I2C/MCU
driver, which isn't available on modern Raspberry Pi OS. See
BUTTON_WIRING.md for how to wire the button/LED to the Pi's header.
"""

from gpiozero import PWMLED


class LedStatus:
    """Sets the button LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack, pin=25):
        self._led = exit_stack.enter_context(PWMLED(pin))

    def listening(self):
        self._led.on()

    def thinking(self):
        self._led.pulse()

    def ready(self):
        self._led.off()
