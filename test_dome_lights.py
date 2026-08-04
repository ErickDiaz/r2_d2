"""Prueba rapida de los 2 NeoPixel Stick del domo, encadenados por SPI
(pin fisico 19 = MOSI). Corre un ciclo: rojo solido -> azul solido ->
verde solido -> flicker tipo logic display, cada uno unos segundos.
Ctrl+C para salir. Ver DOME_LIGHTS_WIRING.md antes de cablear.
"""

from contextlib import ExitStack
from time import sleep

from dome_lights import DomeLights

with ExitStack() as stack:
    lights = DomeLights(stack)
    try:
        print('Rojo solido...')
        lights.fill((255, 0, 0))
        sleep(3)

        print('Azul solido...')
        lights.fill((0, 0, 255))
        sleep(3)

        print('Verde solido...')
        lights.fill((0, 255, 0))
        sleep(3)

        print('Flicker tipo logic display -- Ctrl+C para salir.')
        lights.flicker()
        while True:
            sleep(0.5)
    except KeyboardInterrupt:
        pass
