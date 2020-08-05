from time import sleep
from gpiozero import LED
from aiy.pins import (PIN_A, PIN_B)

leds = (LED(PIN_A), LED(PIN_B))

while True:
    for led in leds:
        led.on()
        sleep(0.5)
        led.off()
