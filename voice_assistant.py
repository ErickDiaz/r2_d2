"""Local, offline voice front-end: waits for a wake word, transcribes the
command that follows, and dispatches it to R2-D2's local commands or to
Home Assistant.

Configuration via environment variables:
  PICOVOICE_ACCESS_KEY  Picovoice Porcupine access key (required, free at console.picovoice.ai)
  WAKEWORD_KEYWORDS     comma-separated built-in Porcupine keywords (default: jarvis)
  VOSK_MODEL_PATH       path to an unzipped Vosk model directory (required)
  HA_URL                Home Assistant base URL, e.g. http://homeassistant.local:8123
  HA_TOKEN              Home Assistant long-lived access token
  HA_COMMANDS_PATH      path to the phrase -> service JSON config (default: smart_home_commands.json)
"""

import os
from contextlib import ExitStack

import sounddevice as sd
from pygame import mixer

from home_assistant import HomeAssistantClient
from led_status import LedStatus
from r2d2_commands import R2D2LocalCommands
from smart_home_dispatcher import SmartHomeDispatcher
from sounds import SoundBoard
from speech_to_text import VoskTranscriber
from wakeword import WakeWordDetector

PICOVOICE_ACCESS_KEY = os.environ['PICOVOICE_ACCESS_KEY']
WAKEWORD_KEYWORDS = os.getenv('WAKEWORD_KEYWORDS', 'jarvis').split(',')
VOSK_MODEL_PATH = os.environ['VOSK_MODEL_PATH']
HA_COMMANDS_PATH = os.getenv('HA_COMMANDS_PATH', 'smart_home_commands.json')


def main():
    detector = WakeWordDetector(PICOVOICE_ACCESS_KEY, WAKEWORD_KEYWORDS)
    transcriber = VoskTranscriber(VOSK_MODEL_PATH, sample_rate=detector.sample_rate)
    sounds = SoundBoard(mixer)
    dispatchers = [R2D2LocalCommands(sounds)]
    if os.getenv('HA_URL') and os.getenv('HA_TOKEN'):
        dispatchers.append(SmartHomeDispatcher(HomeAssistantClient.from_env(), HA_COMMANDS_PATH))
    else:
        print('HA_URL/HA_TOKEN no configurados: el dispatcher de Home Assistant esta deshabilitado')

    with ExitStack() as stack:
        led = LedStatus(stack)
        stream = stack.enter_context(
            sd.InputStream(
                samplerate=detector.sample_rate, channels=1, dtype='int16', blocksize=detector.frame_length
            )
        )

        def read_chunk(size):
            data, _ = stream.read(size)
            return data.tobytes()

        led.ready()
        sounds.play('hola')
        print('Escuchando wake word...')
        while True:
            data, _ = stream.read(detector.frame_length)
            wakeword = detector.detect(data[:, 0])
            if not wakeword:
                continue

            print('Wake word detectada:', wakeword)
            led.listening()
            sounds.play('processing')
            text = transcriber.transcribe(read_chunk, detector.frame_length)
            led.thinking()
            print('Comando reconocido:', text)

            if not any(dispatcher.dispatch(text) for dispatcher in dispatchers):
                print('Comando no reconocido:', text)
            led.ready()


if __name__ == '__main__':
    main()
