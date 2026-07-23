"""Blinks the AIY HAT LEDs on pins A and B in sequence, one at a time."""

from time import sleep

from gpiozero import LED
from aiy.pins import PIN_A, PIN_B


class LedBlinker:
    """Cycles through a set of LEDs, turning each on then off for `interval` seconds."""

    def __init__(self, pins, interval=0.5):
        self._leds = [LED(pin) for pin in pins]
        self._interval = interval

    def run(self):
        while True:
            for led in self._leds:
                led.on()
                sleep(self._interval)
                led.off()


def main():
    LedBlinker((PIN_A, PIN_B)).run()


if __name__ == '__main__':
    main()
