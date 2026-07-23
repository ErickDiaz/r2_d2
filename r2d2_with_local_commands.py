#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import os
import subprocess
import sys

from google.assistant.library.event import EventType
from pygame import mixer

from aiy.assistant import auth_helpers
from aiy.assistant.library import Assistant
from aiy.board import Board, Led
from aiy.voice import tts

from sounds import SoundBoard


class SpotRobot:
    """Controls a remote Spot Micro robot over SSH."""

    def __init__(self, host, user, path):
        self.host = host
        self.user = user
        self.path = path

    @classmethod
    def from_env(cls):
        return cls(os.getenv('SPOT_HOST'), os.getenv('SPOT_USER'), os.getenv('SPOT_PATH'))

    def activate(self):
        """Trigger the robot's initial-position routine. Returns True on success."""
        result = subprocess.run([
            'ssh', '%s@%s' % (self.user, self.host),
            'python3 %s/initial_position.py' % self.path,
        ])
        return result.returncode == 0


class R2D2Assistant:
    """Wires Google Assistant Library events to R2-D2 sounds, LED state and voice commands."""

    def __init__(self, board, assistant, sounds, spot):
        self.board = board
        self.assistant = assistant
        self.sounds = sounds
        self.spot = spot
        self._commands = {
            'power off': self._power_off,
            'reboot': self._reboot,
            'ip address': self._say_ip,
            'puto': self._say_puto,
            'activa el spot': self._activate_spot,
        }
        self._events = {
            EventType.ON_START_FINISHED: self._on_start_finished,
            EventType.ON_CONVERSATION_TURN_STARTED: self._on_turn_started,
            EventType.ON_RECOGNIZING_SPEECH_FINISHED: self._on_speech_recognized,
            EventType.ON_END_OF_UTTERANCE: self._on_end_of_utterance,
            EventType.ON_CONVERSATION_TURN_FINISHED: self._on_turn_finished,
            EventType.ON_CONVERSATION_TURN_TIMEOUT: self._on_turn_finished,
            EventType.ON_NO_RESPONSE: self._on_turn_finished,
            EventType.ON_ASSISTANT_ERROR: self._on_assistant_error,
        }

    def run(self):
        for event in self.assistant.start():
            self._dispatch(event)

    def _dispatch(self, event):
        logging.info(event)
        handler = self._events.get(event.type)
        if handler:
            handler(event)

    @property
    def led(self):
        return self.board.led

    # -- event handlers --------------------------------------------------

    def _on_start_finished(self, event):
        self.led.state = Led.BEACON_DARK  # Ready.
        self.sounds.play('hola')
        print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    def _on_turn_started(self, event):
        self.led.state = Led.ON  # Listening.

    def _on_speech_recognized(self, event):
        if not event.args:
            return
        text = event.args['text']
        print('You said:', text)
        command = self._commands.get(text.lower())
        if command:
            command()

    def _on_end_of_utterance(self, event):
        self.led.state = Led.PULSE_QUICK  # Thinking.
        self.sounds.play('processing')

    def _on_turn_finished(self, event):
        self.led.state = Led.BEACON_DARK  # Ready.

    def _on_assistant_error(self, event):
        if event.args and event.args['is_fatal']:
            self.sounds.play('sad', wait=True)
            sys.exit(1)

    # -- voice commands ---------------------------------------------------

    def _power_off(self):
        self.assistant.stop_conversation()
        self.sounds.play('sure')
        tts.say('Good bye!')
        subprocess.run(['sudo', 'shutdown', 'now'])

    def _reboot(self):
        self.assistant.stop_conversation()
        self.sounds.play('sure')
        tts.say('See you in a bit!')
        subprocess.run(['sudo', 'reboot'])

    def _say_ip(self):
        self.assistant.stop_conversation()
        ip_address = subprocess.check_output(['hostname', '-I']).decode('utf-8').split()[0]
        tts.say('My IP address is %s' % ip_address)

    def _say_puto(self):
        tts.say('puto')

    def _activate_spot(self):
        self.sounds.play('eureka')
        success = self.spot.activate()
        self.sounds.play('proud' if success else 'concerned')


def main():
    logging.basicConfig(level=logging.INFO)
    credentials = auth_helpers.get_assistant_credentials()
    with Board() as board, Assistant(credentials) as assistant:
        R2D2Assistant(board, assistant, SoundBoard(mixer), SpotRobot.from_env()).run()


if __name__ == '__main__':
    main()
