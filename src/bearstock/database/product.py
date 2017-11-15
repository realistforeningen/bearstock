
from typing import Any, Dict, List, Optional

from .errors import BearDatabaseError, BearModelError
from .model import Model


class Product:
    def __init__(self, *,
                 code: Optional[str] = None,
                 name: Optional[str] = None,
                 producer: Optional[str] = None,
                 type: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 base_price: Optional[int] = None,
                 quantity: Optional[int] = None,
                 hidden: Optional[bool] = None,
                 database: Optional['Database'] = None) -> None:
        super().__init__(self, database=database)

        self._code = code
        self._name = name
        self._producer = producer
        self._type = type
        self._tags = tags
        self._base_price = base_price
        self._quantity = quantity
        self._hidden = hidden

    @property
    def code(self) -> Optional[str]:
        """The product code. Unique across all products, so a manually created
        product with a duplicate code can't be written to the database without
        overwriting the old product.
        """
        return self._code

    @property
    def name(self) -> Optional[str]:
        """Product name."""
        return self._name
    @name.setter
    def name(self, name: str) -> None:
        self._name = name
        if self.is_bound():
            self.update_in_db()

    @property
    def producer(self) -> Optional[str]:
        """Product producer."""
        return self._producer
    @producer.setter
    def producer(self, producer: str) -> None:
        self._producer = producer
        if self.is_bound():
            self.update_in_db()

    @property
    def type(self) -> Optional[str]:
        """Product type."""
        return self._type
    @type.setter
    def type(self, type: str) -> None:
        self._type = type
        if self.is_bound():
            self.update_in_db()

    @property
    def tags(self) -> Optional[List[str]]:
        """Product tags."""
        return self._tags
    @tags.setter
    def tags(self, tags: List[str]) -> None:
        self._tags = tags
        if self.is_bound():
            self.update_in_db()

    @property
    def base_price(self) -> Optional[int]:
        """Product base_price."""
        return self._base_price
    @base_price.setter
    def base_price(self, base_price: int) -> None:
        self._base_price = base_price
        if self.is_bound():
            self.update_in_db()

    @property
    def quantity(self) -> Optional[int]:
        """Product quantity."""
        return self._quantity

    @property
    def hidden(self) -> Optional[bool]:
        """Is the product hidden."""
        return self._hidden
    @hidden.setter
    def hidden(self, hidden: bool) -> None:
        self._hidden = hidden
        if self.is_bound():
            self.update_in_db()

    def as_dict(self, *, with_derived: bool = False) -> Dict[str, Any]:
        """Return the product as a dictionary.

        This method is for interoperability with the web server parts of BearStock.
        The fields in the dictionary are: ``code``, ``name``, ``producer``, ``type``,
        ``tags`` (a list of strings), ``base_price``, ``quantity``, ``hidden``.

        Args:
            with_derived: Include derived product fields: ``current_price``,
                ``timeline``, ``qty_remaining``
        """
        # TODO derived
        return dict(
            code=self._code,
            name=self._name,
            producer=self._producer,
            type=self._type,
            tags=self._tags,
            base_price=self._base_price,
            quantity=self._quantity,
            hidden=self._hidden
        )

    def synchronize(self) -> None:
        """Reload the product from the database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            BearModelError: If the product is not bound to a connected database.
        """
        if not self.is_bound():
            raise BearDatabaseError('product not bound to any connected database')

        product = self.load_from_db(self._database, self.uid)

        self._name = product._name
        self._producer = product._producer
        self._type = product._type
        self._tags = list(product._tags)
        self._base_price = product._base_price
        self._quantity = product._quantity
        self._hidden = product._hidden

    def insert_into(self, db: 'Database', *, rebind: bool = False, overwrite: bool = False) -> None:
        """Insert the product into a database and bind the product to the database.

        Args:
            db: The database to insert into.
            rebind: If the product is already inserted into database this method will
                fail with an exception unless rebind is set to True.
                The default is False.
            overwrite: Optional keyword only argument giving whether the product should
                overwrite a product in the database with the same code.

        Raises:
            BearDatabaseError: If the insert operation failed.
            BearModelError: If the product already is inserted into database and
                rebind is False.
            ValueError: If db is None or not connected.
        """
        if self.is_bound() and not rebind:
            raise BearModelError('product already bound to a database')
        if db is None or not db.is_connected():
            raise ValueError('database None or not connected')

        # may raise BearDatabaseError
        inserted = db.insert_product(
                code=self.code, name=self, producer=self.producer, type=self.type, tags=self.tags,
                base_price=self.base_price, quantity=self.quantity, hidden=self.hidden)

    def update_in_db(self) -> None:
        """Update the product in the database.

        Raises:
            BearDatabaseError: If the database update operation failed.
            BearModelError: If the product is not bound to a connected database.
        """
        if not self.is_bound():
            raise BearModelError('product not bound to a database')

        # may raise BearDatabaseError
        self._database.update_product(self)

    @classmethod
    def load_from_db(cls, db: 'Database', code: str) -> 'Product':
        """Load a product from a database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            ValueError: If the database is None or not connected, or no
                product with code ``code`` was found.
        """
        if db is None:
            raise ValueError('database is None')
        if not db.is_connected():
            raise ValueError('database not connected')

        # may raise BearDatabaseError
        product = db.get_product(code)
        if product is None:
            raise ValueError(f'no product with id: {code}')

        return product

