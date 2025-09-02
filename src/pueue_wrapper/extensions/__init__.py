"""
Extensions module for PueueWrapper.

This module contains extended functionality built on top of the core Pueue operations,
including statistical analysis, advanced task management, and convenience methods.
"""

from .statistics import StatisticsMixin
from .advanced import AdvancedMixin

__all__ = ["StatisticsMixin", "AdvancedMixin"]
