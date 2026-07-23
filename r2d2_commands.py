"""Local R2-D2 system commands (power off, reboot, say IP), with voice/sound
feedback. Independent of any cloud assistant -- uses aiy.voice.tts, which
synthesizes speech locally via pico2wave.
"""

import subprocess

from aiy.voice import tts


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
        tts.say('Adios!', lang='es-ES')
        subprocess.run(['sudo', 'shutdown', 'now'])

    def _reboot(self):
        self._sounds.play('sure')
        tts.say('Nos vemos en un momento!', lang='es-ES')
        subprocess.run(['sudo', 'reboot'])

    def _say_ip(self):
        ip_address = subprocess.check_output(['hostname', '-I']).decode('utf-8').split()[0]
        tts.say('Mi direccion IP es %s' % ip_address, lang='es-ES')
