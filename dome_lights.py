"""Controla los 2 NeoPixel Stick (8x5050 cada uno) que simulan los
"cuadrantes" de luces logicas del domo de R2-D2, ademas de la luz roja del
boton (ver led_status.py). Los dos sticks se encadenan en una sola linea
de datos (DOUT del stick 1 -> DIN del stick 2) y se tratan como una tira
de 16 pixeles: 0-7 son el cuadrante izquierdo, 8-15 el derecho.

Usa SPI en vez de Jetson.GPIO: el PWM de hardware de la Jetson Nano esta
limitado a 2 pines y no alcanza la temporizacion de ~800kHz que exige el
protocolo WS2812, pero el FIFO de hardware del SPI si puede generarla de
forma confiable (ver DOME_LIGHTS_WIRING.md para el cableado y como
habilitar SPI1 con jetson-io antes de correr esto).

DomeLights corre un LightPattern de fondo en un hilo propio, para siempre
(por defecto Flicker, el look de "logic display"). trigger() cambia el
patron activo por una duracion determinada -- para reaccionar a un evento
puntual -- y al vencer ese tiempo vuelve sola al patron por defecto, sin
que el resto del codigo tenga que acordarse de revertirlo.
"""

import random
import threading
import time

import board
import busio
import neopixel_spi as neopixel

# Importar `board` deja el modo interno de Jetson.GPIO fijado en su propio
# esquema de pines (TEGRA_SOC), como efecto secundario -- lo cual rompe a
# led_status.py/push_to_talk.py cuando despues intentan fijar el modo BOARD.
# cleanup() resetea ese estado para que puedan setearlo ellos.
import Jetson.GPIO as _GPIO
_GPIO.cleanup()

_PIXELS_PER_STICK = 8
_NUM_STICKS = 2
_NUM_PIXELS = _PIXELS_PER_STICK * _NUM_STICKS

LEFT = range(0, _PIXELS_PER_STICK)
RIGHT = range(_PIXELS_PER_STICK, _NUM_PIXELS)
BOTH = range(0, _NUM_PIXELS)

_OFF = (0, 0, 0)
_TICK_SECONDS = 0.15


class LightPattern:
    """Una animacion de las luces del domo. DomeLights llama a step() una
    vez por tick; la implementacion decide que pixeles cambiar."""

    def step(self, pixels):
        raise NotImplementedError


class Flicker(LightPattern):
    """Prende un pixel al azar con un color al azar por tick -- el look
    clasico de "computadora pensando" de un logic display."""

    def __init__(self, colors, pixel_range=BOTH):
        self._colors = colors
        self._pixel_range = pixel_range

    def step(self, pixels):
        pixels[random.choice(self._pixel_range)] = random.choice(self._colors)


class Solid(LightPattern):
    """Un color fijo en todos los pixeles del rango."""

    def __init__(self, color, pixel_range=BOTH):
        self._color = color
        self._pixel_range = pixel_range

    def step(self, pixels):
        for i in self._pixel_range:
            pixels[i] = self._color


# Colores tipicos de un logic display de R2-D2: blanco, azul y rojo.
DEFAULT_PATTERN = Flicker([(255, 255, 255), (0, 80, 255), (255, 0, 0)])


class DomeLights:
    """Corre un LightPattern de fondo en un hilo propio, para siempre."""

    def __init__(self, exit_stack, brightness=0.4, default_pattern=DEFAULT_PATTERN):
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        self._pixels = neopixel.NeoPixel_SPI(
            spi,
            _NUM_PIXELS,
            brightness=brightness,
            pixel_order=neopixel.GRB,
            auto_write=False,
        )
        self._default_pattern = default_pattern
        self._pattern = default_pattern
        self._revert_at = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        exit_stack.callback(self._shutdown)

    def trigger(self, pattern, duration):
        """Cambia al patron dado por `duration` segundos; al vencer, vuelve
        sola al patron por defecto."""
        with self._lock:
            self._pattern = pattern
            self._revert_at = time.monotonic() + duration

    def _run(self):
        while not self._stop.wait(_TICK_SECONDS):
            with self._lock:
                if self._revert_at is not None and time.monotonic() >= self._revert_at:
                    self._pattern = self._default_pattern
                    self._revert_at = None
                pattern = self._pattern
            pattern.step(self._pixels)
            self._pixels.show()

    def _shutdown(self):
        self._stop.set()
        self._thread.join()
        self._pixels.fill(_OFF)
        self._pixels.show()
