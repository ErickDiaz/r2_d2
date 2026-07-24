# R2-D2 con Google AIY Voice Kit 2.0

Asistente de voz para una réplica de R2-D2 impresa en 3D, montada sobre una
**Raspberry Pi 3**. Reacciona a comandos de voz reproduciendo sonidos
icónicos de R2-D2, ejecutando acciones locales (apagar, reiniciar, decir la
IP) y controlando dispositivos de Home Assistant.

## Hardware

- Raspberry Pi 3 (Model B/B+).
- Carcasa de R2-D2 impresa en 3D: [tutorial](http://www.uswaterrockets.com/3D_Printing/3D_Printed_Star_Wars_Droid/tutorial.htm).
- **Micrófono**: USB (probado con un Razer Seiren Mini). El micrófono
  integrado del Google AIY Voice Kit 2.0 (HAT/Bonnet) se abandonó — ver
  "Por qué no usamos el HAT" abajo.
- **Parlante**: pendiente de resolver. El altavoz original del kit está
  cableado al conector propietario del HAT, no al jack de audífonos de la
  Pi; hace falta un parlante USB o un mini amplificador para el jack 3.5mm.
- **LED/botón del HAT**: pendiente por separado (no es solo estético — el
  LED rojo parpadeante es parte del look de este R2-D2). `led_status.LedStatus`
  ya está preparado para usarlo si se resuelve más adelante, pero hoy corre
  sin él.

### Por qué no usamos el HAT (Google AIY Voice Kit 2.0)

Se probó exhaustivamente en hardware real: **Raspberry Pi OS Bullseye,
Bookworm y Trixie fallan de forma idéntica** — los módulos del kernel del
HAT (`snd_soc_googlevoicehat_codec`, `snd_soc_rpi_simple_soundcard`,
`snd_soc_bcm2835_i2s`) cargan sin error, pero la tarjeta de sonido ALSA
nunca se registra. Solo la imagen oficial `aiyprojects-2018-11-16.img.xz`
(Raspbian 9 "stretch") tiene el audio del HAT funcionando de fábrica — pero
su glibc (2.24) es demasiado viejo para `vosk` y otros paquetes modernos con
código compilado (confirmado: `vosk` instala pero falla al importar con
`GLIBC_2.27' not found`). No hay ninguna imagen que dé ambas cosas a la vez,
así que se optó por abandonar el audio del HAT y usar un micrófono USB
genérico + Raspberry Pi OS Bullseye (glibc 2.31, Python 3.9, buen soporte de
paquetes).

## Software

### Sistema operativo

**Raspberry Pi OS Bullseye (Legacy, 32-bit)**. No viene en el catálogo
normal de Raspberry Pi Imager (que ahora ofrece Bookworm/Trixie) — hay que
descargar la imagen del archivo oficial:

```
https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2023-05-03/2023-05-03-raspios-bullseye-armhf-lite.img.xz
```

Al ser una imagen "custom" en Imager, el asistente de personalización
(usuario/wifi/SSH) puede no aplicarse — si no, monta la partición `boot` y
crea un archivo vacío llamado `ssh` para habilitarlo en el primer arranque.

### Dependencias Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Instala `pygame` (sonidos), `gpiozero`, `pvporcupine` (wake word),  `vosk`
(reconocimiento de voz), `sounddevice` + `numpy` (captura de audio) y
`requests` (Home Assistant). A nivel de sistema hace falta PortAudio y
`espeak-ng` (respaldo de TTS):

```bash
sudo apt install libportaudio2 portaudio19-dev espeak-ng
```

## Scripts

| Script | Qué hace |
|---|---|
| `voice_assistant.py` | Front-end de voz local (sin Google): espera una wake word con `Porcupine` y transcribe el comando con `Vosk`, offline. |
| `r2d2_with_local_commands.py` | Script original con Google Assistant Library (deprecada desde 2019) — legado, pensado para el HAT que ya no usamos. |
| `r2d2.py` | Demo de referencia de Google usando la API gRPC del Assistant (legado). |
| `r2_lights.py` | Prueba de hardware: parpadea dos LEDs por GPIO (pines A/B del HAT). |

### Reconocimiento de voz local (sin Google) + control de Home Assistant

`voice_assistant.py` es un pipeline 100% local y offline: micrófono USB →
`WakeWordDetector` (Porcupine) → `VoskTranscriber` (Vosk) →
`R2D2LocalCommands` (apagar/reiniciar/IP) → `SmartHomeDispatcher` (Home
Assistant).

Antes de correrlo hace falta:

1. **Access key de Picovoice** (wake word): crear una cuenta gratuita en
   [console.picovoice.ai](https://console.picovoice.ai/), copiar el
   `AccessKey` y exportarlo como `PICOVOICE_ACCESS_KEY`. Por defecto usa la
   palabra clave incorporada `jarvis` (`WAKEWORD_KEYWORDS`); entrenar una
   wake word propia en español requiere el Porcupine Console.
2. **Modelo de Vosk** (STT en español): descargar `vosk-model-small-es-0.42`
   desde [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models),
   descomprimirlo, y apuntar `VOSK_MODEL_PATH` a esa carpeta. No se incluye
   en el repo por su tamaño.
3. **Token de Home Assistant**: crear un *Long-Lived Access Token* en
   Home Assistant (Perfil → Seguridad → Tokens de acceso de larga duración) y
   exportarlo como `HA_TOKEN`, junto con `HA_URL` (la URL base de tu
   instancia, p. ej. `http://homeassistant.local:8123`).
4. **Mapeo de comandos**: editar `smart_home_commands.json` con tus propias
   frases y `entity_id` (los del archivo son solo ejemplo). Cada entrada
   tiene la forma:

   ```json
   "enciende la sala": {"domain": "light", "service": "turn_on", "entity_id": "light.sala"}
   ```

   `domain`/`service` son los de cualquier [servicio de Home Assistant](https://www.home-assistant.io/docs/scripts/service-calls/)
   (`light.turn_on`, `switch.toggle`, `cover.open_cover`, etc.) y el resto de
   claves se mandan tal cual como datos del servicio.

```bash
export PICOVOICE_ACCESS_KEY=<tu-access-key>
export VOSK_MODEL_PATH=/ruta/a/vosk-model-small-es-0.42
export HA_URL=http://homeassistant.local:8123
export HA_TOKEN=<tu-long-lived-token>
python3 voice_assistant.py
```

Variables de entorno opcionales: `WAKEWORD_KEYWORDS` (lista separada por
comas, default `jarvis`) y `HA_COMMANDS_PATH` (default
`smart_home_commands.json`). Si no seteas `HA_URL`/`HA_TOKEN`, el asistente
corre igual, solo sin el dispatcher de Home Assistant.

Frases reconocidas por `R2D2LocalCommands`:

| Frase | Acción |
|---|---|
| "apaga la pi" | Apaga la Raspberry Pi |
| "reinicia la pi" | Reinicia la Raspberry Pi |
| "cual es tu ip" / "dime tu ip" | Dice la IP local por voz |

Si `Vosk` transcribe tus frases distinto (con o sin tildes, otro orden de
palabras), ajusta las claves de `R2D2LocalCommands._commands` en
`r2d2_commands.py` para que calcen exactamente.

## Sonidos de R2-D2

Los clips en `sounds/` (indexados en `sounds_data.csv`) vienen de
[r2d2translator.com](http://www.r2d2translator.com/). Se cargan y reproducen
mediante `sounds.SoundBoard`, que asocia cada nombre lógico (`hola`, `eureka`,
`processing`, `proud`, `sad`, `concerned`, `sure`) a su archivo.

## Arquitectura

- **`sounds.SoundBoard`** — carga `sounds_data.csv` y reproduce clips por
  nombre sobre un mixer de `pygame`.
- **`wakeword.WakeWordDetector`** — detecta una wake word de Porcupine a
  partir de frames de audio.
- **`speech_to_text.VoskTranscriber`** — transcribe un comando hablado con
  Vosk, offline.
- **`home_assistant.HomeAssistantClient`** — llama servicios de Home
  Assistant vía su API REST.
- **`smart_home_dispatcher.SmartHomeDispatcher`** — mapea frases reconocidas
  (`smart_home_commands.json`) a llamadas de `HomeAssistantClient`.
- **`r2d2_commands.R2D2LocalCommands`** — mapea frases reconocidas a acciones
  locales (apagar, reiniciar, decir IP), con voz (`text_to_speech.say`) y
  sonidos (`SoundBoard`) de feedback.
- **`text_to_speech.say`** — usa `aiy.voice.tts` (pico2wave) si está
  disponible, si no cae a `espeak-ng`, si no hay ninguno solo loggea.
- **`led_status.LedStatus`** — refleja el estado (escuchando/pensando/listo)
  en el LED del HAT; si `aiy.board` no está disponible, no hace nada en vez
  de romper el resto del pipeline.
- **`r2d2_with_local_commands.R2D2Assistant`** — (legado, Google Assistant)
  despacha eventos (tabla evento → handler) y comandos de voz (tabla frase →
  handler) en vez de una cadena larga de `if/elif`.

## Roadmap / ideas pendientes

- Resolver el parlante (USB o mini-amp al jack 3.5mm).
- Retomar el LED/botón del HAT — sin drivers en Bullseye moderno; evaluar si
  vale la pena portar el driver o controlar el LED directo por GPIO/I2C.
- Entrenar una wake word propia en español en Porcupine Console (hoy usa
  `jarvis`, en inglés).
- Reemplazar `pico2wave`/`aiy.voice.tts`/`espeak-ng` por Piper para una voz
  más natural.
- Agregar más comandos de voz, sonidos y servicios de Home Assistant.
