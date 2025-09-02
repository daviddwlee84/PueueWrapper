"""
Core module for PueueWrapper.

This module contains the core functionality that directly interacts with the Pueue CLI,
providing basic task management, status queries, group management, and logging operations.
"""

from .async_core import PueueAsyncCore
from .sync_core import PueueSyncCore

__all__ = ["PueueAsyncCore", "PueueSyncCore"]
