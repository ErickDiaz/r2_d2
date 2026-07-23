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

Instala `pygame` (reproducción de sonidos) y `gpiozero` (control de LEDs en
`r2_lights.py`).

## Scripts

| Script | Qué hace |
|---|---|
| `r2d2_with_local_commands.py` | Script principal. Usa la Google Assistant Library, reacciona a eventos de conversación con sonidos/LEDs y añade comandos de voz locales. |
| `r2d2.py` | Demo de referencia de Google usando la API gRPC del Assistant (legado; sin comandos locales ni sonidos). |
| `r2_lights.py` | Prueba de hardware: parpadea los dos LEDs del HAT (pines A y B). |

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

## Roadmap / ideas pendientes

- Agregar más comandos de voz y sonidos.
