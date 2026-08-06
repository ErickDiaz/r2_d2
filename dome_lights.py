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
que el resto del codigo tenga que acordarse de revertirlo. Si la duracion
del evento no se conoce de antemano (p.ej. mientras dura un sonido),
revert() fuerza la vuelta al patron por defecto en el momento exacto en
que se sabe que el evento termino.
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
_DEFAULT_TICK_SECONDS = 0.2


class LightPattern:
    """Una animacion de las luces del domo. DomeLights llama a step() una
    vez por tick; la implementacion cambia los pixeles que quiera y
    devuelve cuantos segundos esperar hasta el proximo tick. on_activate()
    se llama una sola vez, apenas este patron pasa a ser el activo -- sirve
    para repintar todo de golpe en vez de esperar a que step() vaya
    llegando a cada pixel de a uno (lo que dejaria pixeles del patron
    anterior "colgados" un rato)."""

    def on_activate(self, pixels):
        pass

    def step(self, pixels):
        raise NotImplementedError


class Flicker(LightPattern):
    """Prende un pixel al azar con un color al azar, a un ritmo tambien al
    azar entre min_seconds y max_seconds -- el look clasico de "computadora
    pensando" de un logic display. `colors` puede ser una lista fija de
    colores (se elige uno al azar por pixel) o una funcion sin argumentos
    que genere un color nuevo cada vez (para variar tonos dentro de un
    mismo color, no solo elegir entre unos pocos fijos)."""

    def __init__(self, colors, pixel_range=BOTH, min_seconds=0.1, max_seconds=0.5):
        self._colors = colors
        self._pixel_range = pixel_range
        self._min_seconds = min_seconds
        self._max_seconds = max_seconds

    def _pick_color(self):
        return self._colors() if callable(self._colors) else random.choice(self._colors)

    def on_activate(self, pixels):
        for i in self._pixel_range:
            pixels[i] = self._pick_color()

    def step(self, pixels):
        pixels[random.choice(self._pixel_range)] = self._pick_color()
        return random.uniform(self._min_seconds, self._max_seconds)


class Solid(LightPattern):
    """Un color fijo en todos los pixeles del rango."""

    def __init__(self, color, pixel_range=BOTH, tick_seconds=_DEFAULT_TICK_SECONDS):
        self._color = color
        self._pixel_range = pixel_range
        self._tick_seconds = tick_seconds

    def step(self, pixels):
        for i in self._pixel_range:
            pixels[i] = self._color
        return self._tick_seconds


def random_blue():
    """Un tono de azul al azar -- rojo y verde bajos, azul siempre alto,
    para que el resultado se perciba como "azul" pero variando entre un
    celeste brillante y un azul mas oscuro/profundo."""
    return (random.randint(0, 40), random.randint(0, 90), random.randint(140, 255))


# Parpadeo a ritmo al azar entre 0.1 y 0.5 segundos por cambio, con tonos
# de azul generados al vuelo (no una lista fija de colores).
DEFAULT_PATTERN = Flicker(random_blue)


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
        sola al patron por defecto. Para eventos de duracion desconocida
        (p.ej. mientras dura un sonido), usar una duracion holgada y llamar
        a revert() apenas se sepa que el evento termino."""
        self._switch_to(pattern, time.monotonic() + duration)

    def revert(self):
        """Vuelve al patron por defecto ya mismo, sin esperar a que venza
        la duracion de un trigger() anterior."""
        self._switch_to(self._default_pattern, None)

    def _switch_to(self, pattern, revert_at):
        with self._lock:
            self._pattern = pattern
            self._revert_at = revert_at
            pattern.on_activate(self._pixels)
            self._pixels.show()

    def _run(self):
        delay = 0
        while not self._stop.wait(delay):
            with self._lock:
                if self._revert_at is not None and time.monotonic() >= self._revert_at:
                    self._pattern = self._default_pattern
                    self._revert_at = None
                    self._pattern.on_activate(self._pixels)
                pattern = self._pattern
                delay = pattern.step(self._pixels)
                self._pixels.show()

    def _shutdown(self):
        self._stop.set()
        self._thread.join()
        self._pixels.fill(_OFF)
        self._pixels.show()
