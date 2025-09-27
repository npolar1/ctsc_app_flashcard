# Hacer que la carpeta utils sea un paquete Python
from .database import get_snowflake_connection

__all__ = ['get_snowflake_connection']