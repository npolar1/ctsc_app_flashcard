# Hacer que la carpeta tabs sea un paquete Python
from .dashboard import show_dashboard
from .study import show_study
from .progress import show_progress

__all__ = ['show_dashboard', 'show_study', 'show_progress']