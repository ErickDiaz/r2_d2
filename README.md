# R2-D2 con Google AIY Voice Kit 2.0

Asistente de voz para una réplica de R2-D2 impresa en 3D, montada sobre una
**Raspberry Pi 3** con el **Google AIY Voice Kit 2.0**. Reacciona a comandos de
voz reproduciendo sonidos icónicos de R2-D2 y ejecutando acciones locales
(apagar, reiniciar, decir la IP).

## Hardware

- Raspberry Pi 3 (Model B/B+). El Voice Kit / Google Assistant Library no
  soporta Pi Zero.
- Google AIY Voice Kit 2.0 (micrófono, botón, LEDs, altavoz).
- Carcasa de R2-D2 impresa en 3D: [tutorial](http://www.uswaterrockets.com/3D_Printing/3D_Printed_Star_Wars_Droid/tutorial.htm).

## Software

### Requisitos previos

Pensado para correr sobre la imagen oficial **AIY Projects Raspbian** (o
Raspberry Pi OS + el script de instalación del Voice Kit), que ya trae
preinstalados:

- El paquete `aiy` (LEDs, botón, pines, TTS) — [aiyprojects-raspbian](https://github.com/google/aiyprojects-raspbian)
- `google-assistant-library` y las credenciales del Google Assistant

Sigue la [guía oficial del Voice Kit](https://aiyprojects.withgoogle.com/voice/)
para dejar el hardware funcionando y autenticado antes de usar estos scripts.

### Dependencias Python

```bash
pip3 install -r requirements.txt
```

Instala `pygame` (reproducción de sonidos), `gpiozero` (control de LEDs en
`r2_lights.py`), `openwakeword` + `vosk` + `sounddevice` + `numpy` (voz
local, ver más abajo) y `requests` (llamadas a Home Assistant). `sounddevice`
necesita PortAudio instalado a nivel de sistema:

```bash
sudo apt install libportaudio2
```

## Scripts

| Script | Qué hace |
|---|---|
| `voice_assistant.py` | Front-end de voz local (sin Google): espera una wake word con `openWakeWord` y transcribe el comando con `Vosk`, offline. |
| `r2d2_with_local_commands.py` | Script principal original. Usa la Google Assistant Library (deprecada desde 2019), reacciona a eventos de conversación con sonidos/LEDs y añade comandos de voz locales. |
| `r2d2.py` | Demo de referencia de Google usando la API gRPC del Assistant (legado; sin comandos locales ni sonidos). |
| `r2_lights.py` | Prueba de hardware: parpadea los dos LEDs del HAT (pines A y B). |

### Reconocimiento de voz local (sin Google) + control de Home Assistant

Google está desmantelando el Assistant SDK que usaba `r2d2_with_local_commands.py`,
así que `voice_assistant.py` reemplaza esa pieza por un pipeline 100% local y
offline: micrófono → `WakeWordDetector` (openWakeWord) → `VoskTranscriber`
(Vosk) → `R2D2LocalCommands` (apagar/reiniciar/IP) → `SmartHomeDispatcher`
(Home Assistant). El HAT del AIY Voice Kit sigue sirviendo igual: el
micrófono se usa como cualquier dispositivo ALSA/PortAudio, el botón/LEDs
vía `aiy.board.Board`, y la voz de salida sigue usando `aiy.voice.tts`
(pico2wave local, sin depender de Google Cloud).

Antes de correrlo hace falta:

1. **Modelo de Vosk** (STT en español): descargar `vosk-model-small-es-0.42`
   desde [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models),
   descomprimirlo, y apuntar `VOSK_MODEL_PATH` a esa carpeta. No se incluye en
   el repo por su tamaño.
2. **Modelo(s) de wake word**: por defecto usa `hey_jarvis` (uno de los
   modelos en inglés que trae openWakeWord). Para una wake word propia en
   español (p. ej. "oye R2D2") hay que entrenar un modelo custom siguiendo la
   [documentación de openWakeWord](https://github.com/dscripka/openWakeWord).
3. **Token de Home Assistant**: crear un *Long-Lived Access Token* en
   Home Assistant (Perfil → Seguridad → Tokens de acceso de larga duración) y
   exportarlo como `HA_TOKEN`, junto con `HA_URL` (la URL base de tu instancia,
   p. ej. `http://homeassistant.local:8123`).
4. **Mapeo de comandos**: editar `smart_home_commands.json` con tus propias
   frases y `entity_id` (los del archivo son solo ejemplo). Cada entrada tiene
   la forma:

   ```json
   "enciende la sala": {"domain": "light", "service": "turn_on", "entity_id": "light.sala"}
   ```

   `domain`/`service` son los de cualquier [servicio de Home Assistant](https://www.home-assistant.io/docs/scripts/service-calls/)
   (`light.turn_on`, `switch.toggle`, `cover.open_cover`, etc.) y el resto de
   claves se mandan tal cual como datos del servicio.

```bash
export VOSK_MODEL_PATH=/ruta/a/vosk-model-small-es-0.42
export HA_URL=http://homeassistant.local:8123
export HA_TOKEN=<tu-long-lived-token>
python3 voice_assistant.py
```

Variables de entorno opcionales: `WAKEWORD_MODELS` (lista separada por
comas, default `hey_jarvis`), `WAKEWORD_THRESHOLD` (default `0.5`) y
`HA_COMMANDS_PATH` (default `smart_home_commands.json`).

Frases reconocidas por `R2D2LocalCommands` (independiente de
`r2d2_with_local_commands.py`, que sigue atado a la Google Assistant Library):

| Frase | Acción |
|---|---|
| "apaga la pi" | Apaga la Raspberry Pi |
| "reinicia la pi" | Reinicia la Raspberry Pi |
| "cual es tu ip" / "dime tu ip" | Dice la IP local por voz |

Si `Vosk` transcribe tus frases distinto (con o sin tildes, otro orden de
palabras), ajusta las claves de `R2D2LocalCommands._commands` en
`r2d2_commands.py` para que calcen exactamente.

### Ejecutar el asistente principal

```bash
python3 r2d2_with_local_commands.py
```

### Comandos de voz locales

Además de conversar normalmente con el Google Assistant, estas frases se
interceptan localmente:

| Frase | Acción |
|---|---|
| "power off" | Apaga la Raspberry Pi |
| "reboot" | Reinicia la Raspberry Pi |
| "ip address" | Dice la IP local por voz |

## Sonidos de R2-D2

Los clips en `sounds/` (indexados en `sounds_data.csv`) vienen de
[r2d2translator.com](http://www.r2d2translator.com/). Se cargan y reproducen
mediante `sounds.SoundBoard`, que asocia cada nombre lógico (`hola`, `eureka`,
`processing`, `proud`, `sad`, `concerned`, `sure`) a su archivo.

## Arquitectura

- **`sounds.SoundBoard`** — carga `sounds_data.csv` y reproduce clips por
  nombre sobre un mixer de `pygame`.
- **`r2d2_with_local_commands.R2D2Assistant`** — despacha eventos del Google
  Assistant (tabla evento → handler) y comandos de voz (tabla frase →
  handler) en vez de una cadena larga de `if/elif`.
- **`wakeword.WakeWordDetector`** — detecta una wake word a partir de chunks
  de audio, usando openWakeWord.
- **`speech_to_text.VoskTranscriber`** — transcribe un comando hablado con
  Vosk, offline.
- **`home_assistant.HomeAssistantClient`** — llama servicios de Home
  Assistant vía su API REST.
- **`smart_home_dispatcher.SmartHomeDispatcher`** — mapea frases reconocidas
  (`smart_home_commands.json`) a llamadas de `HomeAssistantClient`.
- **`r2d2_commands.R2D2LocalCommands`** — mapea frases reconocidas a acciones
  locales (apagar, reiniciar, decir IP), con voz (`aiy.voice.tts`) y sonidos
  (`SoundBoard`) de feedback.

## Roadmap / ideas pendientes

- Entrenar una wake word propia en español (hoy usa `hey_jarvis`, en inglés).
- Reemplazar `pico2wave`/`aiy.voice.tts` por Piper para una voz más natural.
- Agregar más comandos de voz, sonidos y servicios de Home Assistant.
