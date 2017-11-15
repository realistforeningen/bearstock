
from typing import Any, Dict, List, Optional

from .errors import BearDatabaseError, BearModelError
from .model import Model


class Buyer(Model):
    def __init__(self, *,
                 uid: Optional[int] = None,
                 name: Optional[str] = None,
                 icon: Optional[str] = None,
                 scaling: Optional[int] = None,
                 created_at: Optional[int] = None,
                 database: Optional['Database'] = None) -> None:
        super().__init__(self, database=database)

        self._uid = uid
        self._name = name
        self._icon = icon
        self._scaling = scaling
        self._created_at = created_at

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
        if self.is_bound():
            self.update_in_db()

    @property
    def icon(self) -> str:
        return self._icon
    @icon.setter
    def _(self, icon) -> None:
        self._icon = icon
        if self.is_bound():
            self.update_in_db()

    @property
    def scaling(self) -> int:
        return self._scaling
    @scaling.setter
    def _(self, scaling) -> None:
        self._scaling = scaling
        if self.is_bound():
            self.update_in_db()

    def as_dict(self) -> Dict[str, Any]:
        """Return the buyer as a dictionary.

        This method is for interoperability with the web server parts of BearStock.
        The fields in the dictionary are: ``id``, ``name``, ``icon``, ``scaling``, and
        ``created_at``.
        """
        return dict(
            id=self.uid,
            name=self.name,
            icon=self.icon,
            scaling=self.scaling,
            created_at=self._created_at,
        )

    def synchronize(self) -> None:
        """Reload the buyer from the database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            BearModelError: If the buyer is not bound to a connected database.
        """
        if not self.is_bound():
            raise BearModelError('buyer not bound to any database')

        # may raise BearDatabaseError
        buyer = self.load_from_db(self._database, self.uid)

        self._name = buyer._name
        self._scaling = buyer._scaling
        self._created_at = buyer._created_at

    def insert_into(self, db: 'Database', *, rebind: bool = False) -> None:
        """Insert the buyer into a database and bind the buyer to the database.

        Args:
            db: The database to insert into.
            rebind: If the buyer is already inserted into database this method will
                fail with an exception unless rebind is set to True.
                The default is False.

        Raises:
            BearDatabaseError: If the insert operation failed.
            BearModelError: If the buyer already is inserted into database and
                rebind is False.
            ValueError: If db is None or not connected.
        """
        if self.is_bound() and not rebind:
            raise BearModelError('buyer already bound to a database')
        if db is None or not db.is_connected():
            raise ValueError('database None or not connected')

        self._database = db
        self._uid = None
        self._created_at = None

        # may raise BearDatabaseError
        inserted = db.insert_buyer(
                name=self.name, icon=self.icon, scaling=self.scaling)
        self._database = db

        self._uid = inserted.uid
        self._created_at = inserted.created_at

    def update_in_db(self) -> None:
        """Update the buyer in the database.

        Raises:
            BearDatabaseError: If the database update operation failed.
            BearModelError: If the buyer is not bound to a connected database.
        """
        if self.is_bound() is None:
            raise BearModelError('buyer not bound to a database')

        # may raise BearDatabaseError
        self._database.update_user(self)

    @classmethod
    def load_from_db(cls, db: 'Database', uid: int) -> 'Buyer':
        """Load a buyer from a database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            ValueError: If the database is None or not connected.
        """
        if db is None:
            raise ValueError('database is None')
        if not db.is_connected():
            raise ValueError('database not connected')

        # may throw BearDatabaseError
        buyer = db.get_buyer(uid)

        if buyer is None:
            raise ValueError(f'no buyer with id: {uid}')

        return buyer

