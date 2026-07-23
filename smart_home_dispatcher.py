"""Maps recognized voice phrases to Home Assistant service calls."""

import json


class SmartHomeDispatcher:
    """Looks up a recognized phrase in a JSON config and calls the matching HA service."""

    def __init__(self, client, commands_path):
        self._client = client
        with open(commands_path) as f:
            self._commands = json.load(f)

    def dispatch(self, text):
        """Call the service mapped to `text` (case-insensitive). Returns True if handled."""
        command = self._commands.get(text.strip().lower())
        if not command:
            return False
        data = {k: v for k, v in command.items() if k not in ('domain', 'service')}
        self._client.call_service(command['domain'], command['service'], **data)
        return True
