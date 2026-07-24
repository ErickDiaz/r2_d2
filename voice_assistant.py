"""Local, offline voice front-end: waits for a wake word, transcribes the
command that follows, and dispatches it to R2-D2's local commands or to
Home Assistant.

Configuration via environment variables:
  VOSK_MODEL_PATH   path to an unzipped Vosk model directory (required)
  WAKE_PHRASE       phrase that triggers listening (default: "arturito")
  HA_URL            Home Assistant base URL, e.g. http://homeassistant.local:8123
  HA_TOKEN          Home Assistant long-lived access token
  HA_COMMANDS_PATH  path to the phrase -> service JSON config (default: smart_home_commands.json)
"""

import os
from contextlib import ExitStack

import sounddevice as sd
import vosk
from pygame import mixer

from home_assistant import HomeAssistantClient
from led_status import LedStatus
from r2d2_commands import R2D2LocalCommands
from smart_home_dispatcher import SmartHomeDispatcher
from sounds import SoundBoard
from speech_to_text import VoskTranscriber
from wakeword import VoskWakeWordDetector

SAMPLE_RATE = 16000
CHUNK_SIZE = 4000  # 0.25s @ 16kHz

VOSK_MODEL_PATH = os.environ['VOSK_MODEL_PATH']
WAKE_PHRASE = os.getenv('WAKE_PHRASE', 'arturito')
HA_COMMANDS_PATH = os.getenv('HA_COMMANDS_PATH', 'smart_home_commands.json')


def main():
    model = vosk.Model(VOSK_MODEL_PATH)
    detector = VoskWakeWordDetector(model, WAKE_PHRASE, sample_rate=SAMPLE_RATE)
    transcriber = VoskTranscriber(model, sample_rate=SAMPLE_RATE)
    sounds = SoundBoard(mixer)
    dispatchers = [R2D2LocalCommands(sounds)]
    if os.getenv('HA_URL') and os.getenv('HA_TOKEN'):
        dispatchers.append(SmartHomeDispatcher(HomeAssistantClient.from_env(), HA_COMMANDS_PATH))
    else:
        print('HA_URL/HA_TOKEN no configurados: el dispatcher de Home Assistant esta deshabilitado')

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
        print('Escuchando wake word: "%s"...' % WAKE_PHRASE)
        while True:
            if not detector.detect(read_chunk(CHUNK_SIZE)):
                continue

            print('Wake word detectada')
            led.listening()
            # wait=True: don't start listening for the command until the R2-D2
            # sound effect finishes, or the mic picks up its own speaker output.
            sounds.play('processing', wait=True)
            text = transcriber.transcribe(read_chunk, CHUNK_SIZE)
            led.thinking()
            print('Comando reconocido:', text)

            if not any(dispatcher.dispatch(text) for dispatcher in dispatchers):
                print('Comando no reconocido:', text)
            led.ready()


if __name__ == '__main__':
    main()
