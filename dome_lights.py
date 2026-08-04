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
"""

import random
import threading

import board
import busio
import neopixel_spi as neopixel

_PIXELS_PER_STICK = 8
_NUM_STICKS = 2
_NUM_PIXELS = _PIXELS_PER_STICK * _NUM_STICKS

_LEFT = slice(0, _PIXELS_PER_STICK)
_RIGHT = slice(_PIXELS_PER_STICK, _NUM_PIXELS)

# Colores tipicos de un logic display de R2-D2: blanco, azul y rojo.
_LOGIC_DISPLAY_COLORS = [(255, 255, 255), (0, 80, 255), (255, 0, 0)]
_OFF = (0, 0, 0)


class DomeLights:
    """Maneja los 2 sticks de NeoPixel como una sola tira SPI de 16 LEDs."""

    def __init__(self, exit_stack, brightness=0.4, flicker_seconds=0.15):
        self._flicker_seconds = flicker_seconds
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        self._pixels = neopixel.NeoPixel_SPI(
            spi,
            _NUM_PIXELS,
            brightness=brightness,
            pixel_order=neopixel.GRB,
            auto_write=False,
        )
        self._pattern_thread = None
        self._stop_pattern = None
        exit_stack.callback(self.off)

    def off(self):
        self._stop_flicker()
        self._pixels.fill(_OFF)
        self._pixels.show()

    def fill(self, color, side='both'):
        self._stop_flicker()
        self._set(side, color)
        self._pixels.show()

    def flicker(self, colors=_LOGIC_DISPLAY_COLORS, side='both'):
        """Prende cada LED del cuadrante con un color al azar, cambiando
        uno a la vez -- el efecto clasico de "computadora pensando"."""
        if self._pattern_thread:
            return
        pixel_range = {'left': range(0, _PIXELS_PER_STICK),
                        'right': range(_PIXELS_PER_STICK, _NUM_PIXELS),
                        'both': range(0, _NUM_PIXELS)}[side]
        self._stop_pattern = threading.Event()

        def _run():
            while not self._stop_pattern.is_set():
                self._pixels[random.choice(pixel_range)] = random.choice(colors)
                self._pixels.show()
                self._stop_pattern.wait(self._flicker_seconds)
            self._pixels.fill(_OFF)
            self._pixels.show()

        self._pattern_thread = threading.Thread(target=_run, daemon=True)
        self._pattern_thread.start()

    def _set(self, side, color):
        if side in ('left', 'both'):
            self._pixels[_LEFT] = [color] * _PIXELS_PER_STICK
        if side in ('right', 'both'):
            self._pixels[_RIGHT] = [color] * _PIXELS_PER_STICK

    def _stop_flicker(self):
        if self._pattern_thread:
            self._stop_pattern.set()
            self._pattern_thread.join()
            self._pattern_thread = None
