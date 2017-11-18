
from typing import Any, Dict, Optional

from .errors import BearDatabaseError, BearModelError
from .model import Model


class Order(Model):
    def __init__(self, *,
                 uid: Optional[int] = None,
                 buyer: Optional['Buyer'] = None,
                 product: Optional['Product'] = None,
                 relative_cost: Optional[int] = None,
                 tick_no: Optional[int] = None,
                 created_at: Optional[int] = None,
                 database: Optional['Database'] = None) -> None:
        super().__init__(database=database)

        self._uid = uid
        self._buyer_id = buyer.uid if buyer is not None else None
        self._product_code = product.code if product is not None else None
        self._relative_cost = relative_cost
        self._tick_no = tick_no
        self._created_at = created_at

    @property
    def uid(self) -> Optional[int]:
        """Order id."""
        return self._uid

    @property
    def buyer(self) -> Optional['Buyer']:
        """Buyer who did the order.

        Note:
            Requires that the order is connected to a database.

        Raises:
            BearModelError: If the order is not bound to the database.
        """
        if not self.is_bound():
            raise BearModelError('model not bound to database')
        if self._buyer_id is None:
            return None
        return self._database.get_buyer(uid=self._buyer_id)

    @property
    def product(self) -> Optional['Product']:
        """Product that was purchased.

        Note:
            Requires that the order is connected to a database.

        Raises:
            BearModelError: If the product is not bound to the database.
        """
        if not self.is_bound():
            raise BearModelError('model not bound to database')
        if self._product_code is None:
            return None
        return self._database.get_product(code=self._product_code)

    @property
    def relative_cost(self) -> Optional[int]:
        """Cost relative the the product base price.

        Note:
            The value is a integer multiple of 1 currency.
        """
        return self._relative_cost

    @property
    def tick_no(self) -> Optional[int]:
        """Tick number of the order."""
        return self._tick_no

    @property
    def created_at(self) -> Optional[int]:
        """Timestamp of the order."""
        return self._created_at

    def as_dict(self, *, with_derived: bool = False) -> Dict[str, Any]:
        """Return the order a dictionary.

        This method is for interoperability with the web server parts of BearStock.
        The fields in the dictionary are: ``uid``, ``buyer_id``, ``product_code``,
        ``relative_cost``, and ``created_at``.

        Args:
            with_derived: Include derived product fields: ``buyer``, ``product``,
                ``price``.
                Derived fields requires the product to be connected to a database.
        """
        product = None if not with_derived else self.product
        return dict(
            id=self._uid,
            buyer_id=self._buyer_id,
            product_code=self._product_code,
            relative_cost=self._relative_cost,
            tick_no=self.tick_no,
            created_at=self._created_at,
            # derived fields
            buyer=None if not with_derived else self.buyer.as_dict(),
            product=None if not with_derived else product.as_dict(with_derived=True),
            price=None if not with_derived else (product.base_price + self.relative_cost),
        )

    def synchronize(self) -> None:
        """Reload the product from the database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            BearModelError: If the order is not bound to a connected database.
        """
        if not self.is_bound():
            raise BearDatabaseError('order not bound to any connected database')

        order = self.load_from_db(self._database, self._uid)

        self._buyer_id = order._buyer_id
        self._product_code = order._product_code
        self._relative_cost = order._relative_cost
        self._tick_no = order._tick_no
        self._created_at = order._created_at

    def insert_into(self, db: 'Database', *, rebind: bool = False) -> None:
        """Insert the order into a database and bind to the database.

        Note:
            The order id will not be respected. The order will receive a new id after
            it is inserted.

        Args:
            db: Database to insert and bind to.
            rebind: Keyword only optional argument giving if the product should be
                inserted and bound to a database if it already is bound.
                Default is False.

        Raises:
            BearDatabaseError: If the insert operation failed.
            BearModelError: If the order already is bound to a database and ``rebind``
                is False.
            ValueError: If ``db`` is None or not connected.
        """
        if self.is_bound() and not rebind:
            raise BearModelError('order already bound to a database')
        if db is None or not db.is_connected():
            raise ValueError('database None or not connected')

        # may raise BearDatabaseError
        inserted = db.insert_order(
            buyer_id=self._buyer_id, product_code=self._product_code,
            relative_cost=self._relative_cost, tick_no=self.tick_no, created_at=self._created_at)

        self._uid = inserted._uid

    def update_in_db(self) -> None:
        """Update the order in the database.

        Raises:
            BearDatabaseError: If the database update operation failed.
            BearModelError: If the order is not bound to bound to a connected database.
        """
        if not self.is_bound():
            raise BearModelError('order not bound to a connected database')

        # may raise BearDatabaseError
        self._database.update_order(self)

    @classmethod
    def load_from_db(self, db: 'Database', uid: int) -> 'Order':
        """Load a order from the database.

        Raises:
            BearDatabaseError: If the database read operation failed.
            ValueError: If the database is None or not connected, or no
                order with id ``uid`` was found.
        """
        if db is None:
            raise ValueError('database is None')
        if not db.is_connected():
            raise ValueError('database not connected')

        # may raise BearDatabaseError
        order = db.get_order(uid)
        if order is None:
            raise ValueError(f'no order with id: {uid}')

        return order

