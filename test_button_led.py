"""Quick hardware test for the push-to-talk button and LED wired directly
to physical pins 16 (button) and 22 (LED) of the 40-pin header. Run this
before trusting the full voice_assistant.py pipeline -- see
BUTTON_WIRING.md.
"""

from contextlib import ExitStack
from time import sleep

from led_status import LedStatus
from push_to_talk import PushToTalkButton

button = PushToTalkButton()

with ExitStack() as stack:
    led = LedStatus(stack)
    print('Preparate: apretando el boton se prende el LED. Ctrl+C para salir.')
    while True:
        if button.is_pressed:
            print('Boton presionado')
            led.listening()
        else:
            led.ready()
        sleep(0.1)
