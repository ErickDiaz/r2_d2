"""Physical push-to-talk button, wired directly to the Pi's GPIO (BCM 23)
-- bypasses the AIY Voice Bonnet's own I2C/MCU driver, which isn't
available on modern Raspberry Pi OS.
"""

from gpiozero import Button


class PushToTalkButton:
    """Wraps the AIY Voice Bonnet's arcade button, wired directly to GPIO23."""

    def __init__(self, pin=23):
        self._button = Button(pin, pull_up=True)

    @property
    def is_pressed(self):
        return self._button.is_pressed
