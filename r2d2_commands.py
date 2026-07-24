"""Local R2-D2 system commands (power off, reboot, say IP), with voice/sound
feedback. Independent of any cloud assistant -- speech uses text_to_speech,
which prefers aiy.voice.tts but falls back to espeak-ng.
"""

import subprocess

import text_to_speech


class R2D2LocalCommands:
    """Maps recognized voice phrases to local system actions."""

    def __init__(self, sounds):
        self._sounds = sounds
        self._commands = {
            'apaga la pi': self._power_off,
            'reinicia la pi': self._reboot,
            'cual es tu ip': self._say_ip,
            'dime tu ip': self._say_ip,
        }

    def dispatch(self, text):
        """Run the action mapped to `text` (case-insensitive). Returns True if handled."""
        command = self._commands.get(text.strip().lower())
        if not command:
            return False
        command()
        return True

    def _power_off(self):
        self._sounds.play('sure')
        text_to_speech.say('Adios!')
        subprocess.run(['sudo', 'shutdown', 'now'])

    def _reboot(self):
        self._sounds.play('sure')
        text_to_speech.say('Nos vemos en un momento!')
        subprocess.run(['sudo', 'reboot'])

    def _say_ip(self):
        ip_address = subprocess.check_output(['hostname', '-I']).decode('utf-8').split()[0]
        text_to_speech.say('Mi direccion IP es %s' % ip_address)
