"""Client for calling Home Assistant services over its REST API."""

import os

import requests


class HomeAssistantClient:
    """Calls Home Assistant services via the REST API using a long-lived access token."""

    def __init__(self, base_url, token):
        self._base_url = base_url.rstrip('/')
        self._headers = {
            'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json',
        }

    @classmethod
    def from_env(cls):
        return cls(os.environ['HA_URL'], os.environ['HA_TOKEN'])

    def call_service(self, domain, service, **data):
        """Call <domain>.<service> (e.g. 'light', 'turn_on') with the given service data."""
        url = '%s/api/services/%s/%s' % (self._base_url, domain, service)
        response = requests.post(url, headers=self._headers, json=data, timeout=5)
        response.raise_for_status()
        return response.json()
