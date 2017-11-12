
from typing import Any, Dict, List, Optional

from .errors import BearDatabaseError

class Buyer:

    def __init__(self, *,
                 uid: Optional[int] = None,
                 name: Optional[str] = None,
                 icon: Optional[str] = None,
                 scaling: Optional[int] = None,
                 created_at: Optional[int] = None,
                 database: Optional['Database'] = None) -> None:
        self._uid = uid
        self._name = name
        self._icon = icon
        self._scaling = scaling
        self._created_at = created_at
        self._database: Optional['Database'] = database

    @property
    def uid(self) -> Optional[int]:
        return self._uid

    @property
    def created_at(self) -> Optional[int]:
        return self._created_at

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def _(self, name) -> None:
        self._name = name
        if self._database is not None:
            self.update_in_db()

    @property
    def icon(self) -> str:
        return self._icon
    @icon.setter
    def _(self, icon) -> None:
        self._icon = icon
        if self._database is not None:
            self.update_in_db()

    @property
    def scaling(self) -> int:
        return self._scaling
    @scaling.setter
    def _(self, name) -> None:
        self._scaling = scaling
        if self._database is not None:
            self.update_in_db()

    def as_dict(self) -> Dict[str, Any]:
        return dict(
            id=self.uid,
            name=self.name,
            icon=self.icon,
            scaling=self.scaling,
            created_at=self._created_at,
        )

    def insert_into(self, db: 'Database', *, rebind: bool = False) -> None:
        """Insert the buyer into a database.

        Args:
            db: The database to insert into.
            rebind: If the buyer is already inserted into database this method will
                fail with an exception unless rebind is set to True.
                The default is False.

        Raises:
            BearDatabaseError: If the buyer already is inserted into database and
                rebind is False.
        """
        if self._database is not None and not rebind:
            raise BearDatabaseError('buyer already bound to a database')

        self._database = db
        self._uid = None
        self._created_at = None

        inserted = db.insert_buyer(buyer)
        self._uid = inserted.uid
        self._created_at = inserted.created_at

    def update_in_db(self) -> None:
        """Update the buyer in the database."""
        if self._database is None:
            raise BearDatabaseError('buyer not bound to a database')

        self._database.update_user(self)

    @staticmethod
    def load_from_db(db: 'Database', uid: int) -> 'Buyer':
        if not db.is_connected():
            raise ValueError('database not connected')

        buyer = db.get_buyer(uid)
        if buyer is None:
            raise ValueError(f'no buyer with id: {uid}')

        return buyer

