"""Optional AIY board LED status feedback.

Degrades to a no-op if aiy.board isn't importable or the HAT's LED/button
driver isn't installed -- on newer Raspberry Pi OS releases (Bookworm+) only
the Voice HAT's sound card overlay is guaranteed to work out of the box, not
its LED/button MCU driver.
"""

import logging

try:
    from aiy.board import Board, Led
except ImportError:
    Board = Led = None


class LedStatus:
    """Sets the AIY board LED to reflect listening/thinking/ready states."""

    def __init__(self, exit_stack):
        self._board = None
        if not Board:
            return
        try:
            self._board = exit_stack.enter_context(Board())
        except Exception:
            logging.warning('aiy.board.Board no disponible; LEDs deshabilitados')

    def listening(self):
        if self._board:
            self._board.led.state = Led.ON

    def thinking(self):
        if self._board:
            self._board.led.state = Led.PULSE_QUICK

    def ready(self):
        if self._board:
            self._board.led.state = Led.BEACON_DARK
