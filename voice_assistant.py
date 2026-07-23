"""Local, offline voice front-end: waits for a wake word, transcribes the
command that follows, and dispatches it to R2-D2's local commands or to
Home Assistant.

Configuration via environment variables:
  WAKEWORD_MODELS     comma-separated openWakeWord model names (default: hey_jarvis)
  WAKEWORD_THRESHOLD  detection threshold, 0-1 (default: 0.5)
  VOSK_MODEL_PATH     path to an unzipped Vosk model directory (required)
  HA_URL              Home Assistant base URL, e.g. http://homeassistant.local:8123
  HA_TOKEN            Home Assistant long-lived access token
  HA_COMMANDS_PATH    path to the phrase -> service JSON config (default: smart_home_commands.json)
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

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms @ 16kHz, the block size openWakeWord expects

WAKEWORD_MODELS = os.getenv('WAKEWORD_MODELS', 'hey_jarvis').split(',')
WAKEWORD_THRESHOLD = float(os.getenv('WAKEWORD_THRESHOLD', '0.5'))
VOSK_MODEL_PATH = os.environ['VOSK_MODEL_PATH']
HA_COMMANDS_PATH = os.getenv('HA_COMMANDS_PATH', 'smart_home_commands.json')


def main():
    detector = WakeWordDetector(WAKEWORD_MODELS, threshold=WAKEWORD_THRESHOLD, chunk_size=CHUNK_SIZE)
    transcriber = VoskTranscriber(VOSK_MODEL_PATH, sample_rate=SAMPLE_RATE)
    sounds = SoundBoard(mixer)
    dispatchers = [
        R2D2LocalCommands(sounds),
        SmartHomeDispatcher(HomeAssistantClient.from_env(), HA_COMMANDS_PATH),
    ]

    with ExitStack() as stack:
        led = LedStatus(stack)
        stream = stack.enter_context(
            sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE)
        )

        def read_chunk(size):
            data, _ = stream.read(size)
            return data.tobytes()

        led.ready()
        sounds.play('hola')
        print('Escuchando wake word...')
        while True:
            data, _ = stream.read(CHUNK_SIZE)
            wakeword = detector.detect(data[:, 0])
            if not wakeword:
                continue

            print('Wake word detectada:', wakeword)
            led.listening()
            sounds.play('processing')
            text = transcriber.transcribe(read_chunk, CHUNK_SIZE)
            led.thinking()
            print('Comando reconocido:', text)

            if not any(dispatcher.dispatch(text) for dispatcher in dispatchers):
                print('Comando no reconocido:', text)
            led.ready()


if __name__ == '__main__':
    main()
