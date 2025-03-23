"""
BCI module for neural signal acquisition and processing.
"""

from .brain_interface import BrainInterface, list_serial_ports

__all__ = ['BrainInterface', 'list_serial_ports']