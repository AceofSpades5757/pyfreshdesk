class DraftLockedError(Exception):
    """Solution Article is draft locked and cannot be edited."""

    def __init__(self):
        self.message = "Solution Article is draft locked and cannot be edited."
        super().__init__(self.message)


class NotFoundError(Exception):
    """Resource not found."""


class AuthenticationError(Exception):
    """Authentication failed."""
