"""Prueba rapida de los 2 NeoPixel Stick del domo, encadenados por SPI
(pin fisico 19 = MOSI). Arranca el patron por defecto (logic display) de
fondo, y cada pocos segundos dispara un trigger() distinto para mostrar
que el comportamiento cambia por un tiempo y despues vuelve solo al
default. Ctrl+C para salir. Ver DOME_LIGHTS_WIRING.md antes de cablear.
"""

from contextlib import ExitStack
from time import sleep

from dome_lights import DomeLights, LEFT, RIGHT, Solid

with ExitStack() as stack:
    lights = DomeLights(stack)
    try:
        print('Patron por defecto (logic display) unos segundos...')
        sleep(5)

        print('Trigger: rojo solido 3s (deberia volver solo al default)...')
        lights.trigger(Solid((255, 0, 0)), duration=3)
        sleep(6)

        print('Trigger: solo cuadrante izquierdo en azul, 3s...')
        lights.trigger(Solid((0, 0, 255), LEFT), duration=3)
        sleep(6)

        print('Trigger: solo cuadrante derecho en verde, 3s...')
        lights.trigger(Solid((0, 255, 0), RIGHT), duration=3)
        sleep(6)

        print('De nuevo en logic display -- Ctrl+C para salir.')
        while True:
            sleep(0.5)
    except KeyboardInterrupt:
        pass
