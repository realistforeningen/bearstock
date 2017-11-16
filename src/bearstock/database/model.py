
from typing import Optional
from abc import ABC


class Model(ABC):
    def __init__(self, *, database: Optional['Database'] = None):
        self._database = database

    def get_db(self) -> 'Database':
        """Get the model database, or None if no database is registered."""
        return self._database

    def _set_database(self, database: 'Database') -> None:
        """Set a database on the model."""
        self._database = database

    def is_bound(self) -> bool:
        """Return True if the model is connected to a database."""
        return self._database is not None and self._database.is_connected()

