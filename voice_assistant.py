"""Local, offline voice front-end: waits for a wake word, transcribes the
command that follows, and dispatches it to R2-D2's local commands or to
Home Assistant.

Configuration via environment variables (or a .env file in this directory):
  VOSK_MODEL_PATH          path to an unzipped Vosk model directory (required)
  WAKE_PHRASE              phrase that triggers listening (default: "arturito")
  IDLE_CHATTER_MIN_SECONDS minimum gap between idle sounds (default: 5400, 1.5h)
  IDLE_CHATTER_MAX_SECONDS maximum gap between idle sounds (default: 10800, 3h)
  HA_URL                   Home Assistant base URL, e.g. http://homeassistant.local:8123
  HA_TOKEN                 Home Assistant long-lived access token
  HA_COMMANDS_PATH         path to the phrase -> service JSON config (default: smart_home_commands.json)
  GEMINI_API_KEY           Google Gemini API key, for answering open questions (optional)
  GEMINI_MODEL             Gemini model name (default: gemini-flash-latest)
  PIPER_BIN                path to the piper binary, for a natural TTS voice (optional)
  PIPER_MODEL              path to a piper .onnx voice model (optional)
"""

import os
from contextlib import ExitStack

from dotenv import load_dotenv

load_dotenv()  # must run before importing our own modules that read env vars at import time

import sounddevice as sd
import vosk
from pygame import mixer

import text_to_speech
from gemini_assistant import GeminiAssistant
from home_assistant import HomeAssistantClient
from idle_chatter import IdleChatter
from led_status import LedStatus
from push_to_talk import PushToTalkButton
from r2d2_commands import R2D2LocalCommands
from smart_home_dispatcher import SmartHomeDispatcher
from sounds import SoundBoard
from speech_to_text import VoskTranscriber
from wakeword import VoskWakeWordDetector

SAMPLE_RATE = 16000
CHUNK_SIZE = 4000  # 0.25s @ 16kHz

ACK_SOUNDS = ['beep_qword4', 'beep_qword1', 'sad', 'proud']

VOSK_MODEL_PATH = os.environ['VOSK_MODEL_PATH']
WAKE_PHRASE = os.getenv('WAKE_PHRASE', 'arturito')
IDLE_CHATTER_MIN_SECONDS = float(os.getenv('IDLE_CHATTER_MIN_SECONDS', 5400))
IDLE_CHATTER_MAX_SECONDS = float(os.getenv('IDLE_CHATTER_MAX_SECONDS', 10800))
HA_COMMANDS_PATH = os.getenv('HA_COMMANDS_PATH', 'smart_home_commands.json')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-flash-latest')


def main():
    model = vosk.Model(VOSK_MODEL_PATH)
    detector = VoskWakeWordDetector(model, WAKE_PHRASE, sample_rate=SAMPLE_RATE)
    transcriber = VoskTranscriber(model, sample_rate=SAMPLE_RATE)
    sounds = SoundBoard(mixer)
    IdleChatter(sounds, sounds.names, IDLE_CHATTER_MIN_SECONDS, IDLE_CHATTER_MAX_SECONDS).start()
    dispatchers = [R2D2LocalCommands(sounds)]
    if os.getenv('HA_URL') and os.getenv('HA_TOKEN'):
        dispatchers.append(SmartHomeDispatcher(HomeAssistantClient.from_env(), HA_COMMANDS_PATH))
    else:
        print('HA_URL/HA_TOKEN no configurados: el dispatcher de Home Assistant esta deshabilitado')

    gemini = GeminiAssistant(GEMINI_API_KEY, GEMINI_MODEL) if GEMINI_API_KEY else None
    if not gemini:
        print('GEMINI_API_KEY no configurada: no se respondran preguntas abiertas')

    button = PushToTalkButton()

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
        print('Escuchando wake word: "%s" (o el boton)...' % WAKE_PHRASE)
        while True:
            chunk = read_chunk(CHUNK_SIZE)
            if not detector.detect(chunk) and not button.is_pressed:
                continue

            print('Wake word/boton detectado')
            led.listening()
            # wait=True: don't start listening for the command until the R2-D2
            # sound effect finishes, or the mic picks up its own speaker output.
            sounds.play_random(ACK_SOUNDS, wait=True)
            # The mic kept recording into its buffer while we were blocked
            # above; discard that backlog so transcribe() starts on live
            # audio instead of replaying stale silence first.
            if stream.read_available:
                stream.read(stream.read_available)
            text = transcriber.transcribe(read_chunk, CHUNK_SIZE)
            led.thinking()
            print('Comando reconocido:', text)

            if not any(dispatcher.dispatch(text) for dispatcher in dispatchers):
                if gemini and text.strip():
                    try:
                        answer = gemini.ask(text)
                        print('Gemini respondio:', answer)
                        text_to_speech.say(answer)
                    except Exception as error:
                        print('Error consultando a Gemini:', error)
                else:
                    print('Comando no reconocido:', text)
            led.ready()


if __name__ == '__main__':
    main()
