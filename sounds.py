"""Loads sound clips listed in sounds_data.csv and plays them through pygame's mixer."""

import csv
import os
import time


class SoundBoard:
    """Maps named R2-D2 sound clips (from sounds_data.csv) to files and plays them."""

    def __init__(self, mixer, base_dir=None, volume=0.9):
        base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self._mixer = mixer
        self._sounds_dir = os.path.join(base_dir, 'sounds')
        self._sounds = self._load_sounds(os.path.join(base_dir, 'sounds_data.csv'))
        self._mixer.init()
        self._mixer.music.set_volume(volume)

    def _load_sounds(self, csv_path):
        sounds = {}
        with open(csv_path, newline='') as f:
            for row in csv.DictReader(f, skipinitialspace=True):
                name = os.path.splitext(row['file'])[0]
                sounds[name] = os.path.join(self._sounds_dir, row['file'])
        return sounds

    def play(self, name, wait=False):
        """Play a clip by name (e.g. 'hola', 'proud', 'sad'). If wait, block until it ends."""
        self._mixer.music.load(self._sounds[name])
        self._mixer.music.play()
        while wait and self._mixer.music.get_busy():
            time.sleep(0.1)
