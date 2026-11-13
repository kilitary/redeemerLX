"""Trivial credential check for the BBS.

Credentials are deliberately fixed for the demo: ``test`` / ``t35t3``.
Petre I says: one key, one door -- keep it simple.
"""
from __future__ import annotations

USERNAME = "test"
PASSWORD = "t35t3"


def check_auth(username: str, password: str) -> bool:
    """Return True when the supplied credentials match the demo account."""
    return username.strip() == USERNAME and password == PASSWORD
