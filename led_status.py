"""LED status feedback for the AIY Voice Bonnet's button LED, wired
directly to the Pi's GPIO (BCM 25) -- bypasses the HAT's own I2C/MCU
driver, which isn't available on modern Raspberry Pi OS. See
BUTTON_WIRING.md for how to wire the button/LED to the Pi's header.

Uses a plain digital LED, not PWMLED: GPIO25 has no hardware PWM support
(only a few specific pins do), unlike the AIY firmware's original software
PWM over RPi.GPIO, which works on any pin.
"""

from gpiozero import LED


class LedStatus:
    """Sets the button LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack, pin=25):
        self._led = exit_stack.enter_context(LED(pin))

    def listening(self):
        self._led.on()

    def thinking(self):
        self._led.blink()

    def ready(self):
        self._led.off()
