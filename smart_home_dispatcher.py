"""Maps recognized voice phrases to Home Assistant service calls."""

import json

from text_normalize import normalize


class SmartHomeDispatcher:
    """Looks up a recognized phrase in a JSON config and calls the matching HA service."""

    def __init__(self, client, commands_path):
        self._client = client
        with open(commands_path) as f:
            raw_commands = json.load(f)
        self._commands = {normalize(phrase): command for phrase, command in raw_commands.items()}

    def dispatch(self, text):
        """Call the service mapped to `text` (case/accent-insensitive). Returns True if handled."""
        command = self._commands.get(normalize(text))
        if not command:
            return False
        data = {k: v for k, v in command.items() if k not in ('domain', 'service')}
        self._client.call_service(command['domain'], command['service'], **data)
        return True
