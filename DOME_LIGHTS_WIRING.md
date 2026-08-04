# Cablear los NeoPixel del domo (2x NeoPixel Stick 8x5050) a la Jetson Nano

Simulan los 2 "cuadrantes" de luces lógicas del domo de R2-D2, además de la
luz roja del botón (`led_status.py`). A diferencia del botón, **no usan
GPIO normal ni PWM** — usan **SPI**, porque el protocolo de los NeoPixel
(WS2812B) necesita pulsos de ~800kHz que el GPIO de software no puede
generar de forma confiable, y el PWM de hardware de la Jetson está
limitado a solo 2 pines (32/33) que no sirven para esto. El FIFO de
hardware del SPI sí puede generar la señal de forma estable — es el mismo
enfoque que documenta Adafruit para CircuitPython en Jetson Nano.

## 1. Habilitar SPI1 en la Jetson

Por defecto el pinmux de la Jetson no tiene el SPI habilitado en el header
de 40 pines. Hay que activarlo con la herramienta oficial:

```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

Elegí **"Configure 40-pin expansion header"** → activá **`spi1`** → guardá
y reiniciá cuando te lo pida.

## 2. Instalar las librerías

```bash
source venv/bin/activate
pip install adafruit-blinka adafruit-circuitpython-neopixel-spi
```

`adafruit-blinka` detecta automáticamente que estás en una Jetson Nano y
expone `board.SCK`/`board.MOSI` apuntando al hardware SPI correcto.

## 3. Conexión física

| Señal | Pin físico (J41) |
|---|---|
| Datos (MOSI) | **19** |
| GND | Cualquier `GND` — por ejemplo pin **20** (al lado) |

Encadená los dos sticks: `DIN` del **primer** stick va al pin 19 de la
Jetson; `DOUT` del primer stick va al `DIN` del **segundo** stick. En
código, los primeros 8 píxeles (`0-7`) son el stick 1, los últimos 8
(`8-15`) el stick 2 — ver `dome_lights.py`.

## 4. Alimentación — NO usar el pin 5V de la Jetson

Los 16 LEDs a full blanco y brillo máximo pueden pedir hasta ~1A, más de lo
que conviene sacar del regulador de la placa (que ya tiene que alimentar
CPU/GPU/USB). Alimentá el `5V`/`VCC` de los sticks desde una fuente externa
de 5V (puede ser el mismo power bank/adaptador que uses para la Jetson, en
un cable separado), y unís el `GND` de esa fuente con el `GND` de la
Jetson (tienen que compartir tierra sí o sí, aunque la alimentación venga
de fuentes separadas).

## 5. Nivel lógico (opcional pero recomendado)

La Jetson trabaja a 3.3V y el WS2812B espera datos a 5V. En cables cortos
(<~30cm) suele funcionar igual conectando MOSI directo, pero si ves
colores erráticos o LEDs que no responden, agregá un buffer/level-shifter
(por ejemplo un `74AHCT125`) entre el pin 19 y el `DIN` del primer stick.

## 6. Probar

```bash
venv/bin/python3 test_dome_lights.py
```

Debería mostrar rojo sólido, azul sólido, verde sólido, y después el
efecto de flicker (colores al azar, un píxel a la vez) hasta que lo
corten con Ctrl+C.

Si los colores salen invertidos (p. ej. pedís rojo y sale verde), tus
sticks usan otro orden de color — cambiá `pixel_order=neopixel.GRB` por
`neopixel.RGB` en `dome_lights.py`.
