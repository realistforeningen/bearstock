
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import sqlite3

from .errors import BearDatabaseError, BearModelError
from .buyer import Buyer
from .model import Model
from .order import Order
from .product import Product

__all__ = [
    'Database',
]

# custom type descriptions
DbArgs = Union[Tuple[Any], Dict[str, Any]]
T = TypeVar('T')


class Database:
    """Bearstock SQLite3 database connection.

    Args:
        db_file: Pathname to the SQLite3 database file.
    """

    def __init__(self, db_file: str) -> None:
        self._db_file = db_file
        self._connection: Optional[sqlite3.Connection] = None

    @property
    def dbname(self) -> str:
        """Name of the database file."""
        return self._db_file

    @property
    def connection(self) -> sqlite3.Connection:
        if not self.is_connected():
            raise BearDatabaseError('database not open')
        return self._connection

    def is_connected(self) -> bool:
        return self._connection is not None

    def connect(self) -> sqlite3.Connection:
        """Connect to the database and do required initializations."""
        if self.is_connected():
            raise BearDatabaseError('database already open')

        self._connection = sqlite3.connect(self.dbname)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute('PRAGMA foreign_keys = ON')

    def close(self) -> None:
        """Close to the database connection."""
        if not self.is_connected():
            raise RuntimeError('database already closed')
        self._connection.close()

    def is_model_mine(self, model: Model) -> bool:
        return model.get_db() is self

    # generic DB access methods

    def exe(self, sql: str, *,
            args: Optional[Union[DbArgs, List[DbArgs]]] = None, many: bool = False,
            callable: Optional[Callable[[sqlite3.Cursor], T]] = None) -> Optional[T]:
        """Execute a arbitrary database query.

        Args:
            sql: SQL query.
            args: Optional arguments to the query. If ``many`` is False ``args`` should be
                a single argument, when it is True is should be a list of arguments.
                Defaults to None.
            many: If True ``args`` should contain a list of arguments, each of which ``sql``
                should be executed with. All executions happen in the same transaction.
                Defaults to False.
            callable: Optional action to perform on the cursor after the query have executed.
                Defaults to None.

        Returns:
            If callable is not not return what returned by it; otherwise None.
        """
        result: Optional[T] = None
        try:
            with self.connection:
                cursor = self.connection.cursor()

                if args is None:
                    cursor.execute(sql)
                else:
                    if not many:
                        cursor.execute(sql, args)
                    else:
                        for arg in args:
                            cursor.execute(sql, args)

                # do something with the query result
                if callable is not None:
                    result = callable(cursor)

                cursor.close()
        except sqlite3.DatabaseError as e:
            raise BearDatabaseError('query failed') from e

        return result

    # buyer related methods

    def insert_buyer(self, name: str, icon: str, *, scaling: float = 1.0) -> Buyer:
        def inserted_id(cursor: sqlite3.Cursor) -> int:
            return cursor.lastrowid
        inserted_id = self.exe(
                'INSERT INTO buyers ( name, icon, scaling ) VALUES ( :name, :icon, :scaling )',
            args={
                'name': name,
                'icon': icon,
                'scaling': scaling,
            },
            callable=inserted_id
        )
        return self.get_buyer(inserted_id)

    def update_buyer(self, buyer: Buyer) -> None:
        """Update the buyer stored in the database from a buyer model.

        Raises:
            ValueError: If the buyer is not bound to this database.
        """
        if not self.is_model_mine(buyer):
            raise ValueError('buyer not bound to this database')
        self.exe(
            'UPDATE buyers SET name = :name, icon = :icon, scaling = :scaling WHERE id = :uid',
            args={
                'uid': buyer.uid,
                'name': buyer.name,
                'icon': buyer.icon,
                'scaling': buyer.scaling,
            }
        )

    def get_buyer(self, uid: int) -> Optional[Buyer]:
        """Get the buyer with ``uid`` from the database.

        Raises:
            BearDatabaseError: If no buyer with the id exists.
            ValueError: If ``uid`` is not an integer.
        """
        def retrive_buyer(cursor: sqlite3.Cursor) -> Buyer:
            row = cursor.fetchone()
            if row is not None:
                return Buyer(
                    uid=row['id'],
                    name=row['name'],
                    icon=row['icon'],
                    scaling=row['scaling'],
                    created_at=row['created_at'],
                    database=self,
                )
            else:
                raise BearDatabaseError(f'could not find buyer with id: {uid}')
        if not isinstance(uid, str):
            raise ValueError('uid not an integer')
        return self.exe(
            'SELECT id, name, icon, scaling, created_at FROM buyers WHERE id = :uid',
            args={'uid': uid,},
            callable=retrive_buyer
        )

    def get_buyers_matching(self, name: str) -> List[Buyer]:
        def retrive_all_buyers(cursor: sqlite3.Cursor) -> List[Buyer]:
            buyers: List[Buyer] = []
            for row in cursor:
                buyers.append(Buyer(
                    uid=row['id'],
                    name=row['name'],
                    icon=row['icon'],
                    scaling=row['scaling'],
                    created_at=row['created_at'],
                    database=self,
                ))
            return sorted(buyers, key=lambda t: t[1].casefold())
        return self.exe(
            'SELECT id, name, icon, scaling, created_at FROM buyers WHERE name LIKE :name',
            args={'name': name,},
            callable=retrive_all_buyers
        )

    def get_all_buyers(self) -> None:
        def action(cursor) -> List[Buyer]:
            buyers: List[Buyer] = []
            for row in cursor:
                buyers.append(Buyer(
                    uid=row['id'],
                    name=row['name'],
                    icon=row['icon'],
                    scaling=row['scaling'],
                    created_at=row['created_at'],
                    database=self,
                ))
            return buyers
        return self.exe(
            'SELECT id, name, icon, scaling, created_at FROM buyers',
            callable=action
        )

    # product related methods

    def insert_product(self, *,
                       code: str, name: str, producer: str,
                       type: str, tags: List[str],
                       base_price: int,
                       quantity: int,
                       hidden: bool,
                       replace_existing: bool = False) -> Product:
        """Insert a new product into the database.

        Args:
            code, name, producer, type, tags, base_price, quantity, hidden:
                Product parameters. See `Product` for descriptions.
            replace_existing: Keyword only optional argument giving whether the product
                should replace a product with the same code or if the method should raise
                `BearDatabaseError`. Defaults to False.

        Returns:
            The inserted product.

        Raises:
            BearDatabaseError: If the insert operation failed. One possible reason is if
                a product with code ``code`` exists in the database and ``replace_existing``
                is False.
            ValueError: If a product parameter is of invalid type.

        See also `import_products` for inserting multiple products in the same transaction.
        """
        if not (isinstance(code, str)
                and isinstance(name, str)
                and isinstance(producer, str)
                and isinstance(type, str)
                and isinstance(tags, (list, tuple)) and all(map(lambda t: isinstance(t, str), tags))
                and isinstance(base_price, int)
                and isinstance(quantity, int)
                and isinstance(hidden, bool)):
            raise ValueError('a product parameter has wrong type')

        def action(cursor) -> int:
            return cursor.lastrowid

        pid = self.exe((
            f'INSERT {"OR REPLACE" if replace_existing else ""} INTO products ( '
            '  code, name, producer, base_price, quantity, type, tags, hidden '
            ') VALUES ( '
            '  :code, :name, :producer, :base_price, :quantity, :type, :tags, :hidden '
            ')'),
            args={
                'code': code, 'name': name, 'producer': producer,
                'type': type, 'tags': '|'.join(tags),
                'base_price': base_price,
                'quantity': quantity,
                'hidden': hidden,
            },
            callable=action
        )
        return self.get_product(uid=pid)

    def import_products(self,
                        products: Dict[str, Dict[str, Any]],
                        *, replace_existing: bool = False) -> None:
        """Import products into the database.

        Products are supplied as a mapping type from product code to another mapping type which
        must accept and return values for the same keys as `insert_product` takes as arguments.
        Even ``code``.

        All products are inserted in the same database transaction, so if one insert failes
        the entire operation is rolled back.

        Args:
            products: Mapping type as described above.
            replace_existing: Keyword only optional argument giving whether excisting products
                should replace existing or the method should raise `BearDatabaseError`.
                Defaults to False.

        Raises:
            BearDatabaseError: If the import failed. One possible reason is if
                ``replace_existing`` is False and there is a duplicate product code.

        See also `insert_product` for inserting a single product.
        """
        args = []
        for product in products:
            args.append({
                'code': product['code'], 'name': product['name'], 'producer': product['producer'],
                'type': product['type'], 'tags': '|'.join(products.get('tags', [])),
                'base_price': product['base_price'],
                'quantity': product['quantity'],
                'hidden': product['hidden'],
            })
        self.exe((
            f'INSERT {"OR REPLACE" if replace_existing else ""} INTO products ( '
            '  code, name, producer, base_price, quantity, type, tags, hidden '
            ') VALUES ( '
            '  :code, :name, :producer, :base_price, :quantity, :type, :tags, :hidden '
            ')'), args=args, many=True
        )

    def update_product(self, product: Product) -> None:
        """Update a product with values from the database.
        The product code can not be changed.

        Raises:
            BearDatabaseError: If the update query failed.
            ValueError: If the product is not bound to this database.
        """
        if not self.is_model_mine(buyer):
            raise ValueError('buyer not bound to this database')
        self.exe((
            'UPDATE products SET '
            '  name = :name, producer = :producer, type = :type, '
            '  tags = :tags, base_price = :base_price, quantity = :quantity, hidden = :hidden '
            'WHERE code = :code'),
            args={
                'code': product.code,
                'name': product.name,
                'producer': product.producer,
                'type': product.type,
                'tags': '|'.join(product.tags),
                'base_price': product.base_price,
                'quantity': product.quantity,
                'hidden': product.hidden,
            }
        )

    def get_product(self, *, code: str) -> Product:
        """Get the product with ``code`` from the database.

        Raises:
            BearDatabaseError: If no buyer with the id exists.
            ValueError: If ``uid`` is not an integer.
        """
        def action(cursor: sqlite3.Cursor) -> Product:
            row = cursor.fetchone()
            if row is not None:
                return Product(
                    code=row['code'],
                    name=row['name'],
                    producer=row['producer'],
                    base_price=row['base_price'],
                    quantity=row['quantity'],
                    type=row['type'],
                    tags=row['tags'].split('|'),
                    hidden=row['hidden'],
                    database=self,
                )
            else:
                raise BearDatabaseError(f'could not find producer with code: {code}')
        return self.exe((
            'SELECT code, name, producer, base_price, quantity, type, tags, hidden '
            'FROM products '
            'WHERE code = :code'),
            args={'code': code},
            callable=action
        )

    def get_all_products(self, *, bound=True) -> List[Product]:
        """Get all products from the database.

        Args:
            bound: If True bind the products to this database; else bind to nothing.
                Defaults to True.
        """
        def action(cursor) -> List[Product]:
            products: List[Product] = []
            for row in cursor:
                products.append(Buyer(
                    code=row['code'],
                    name=row['name'],
                    producer=row['producer'],
                    base_price=row['base_price'],
                    quantity=row['quantity'],
                    type=row['type'],
                    tags=row['tags'].split('|'),
                    hidden=row['hidden'],
                    database=self if bound else None,
                ))
            return products
        return self.exe((
            'SELECT code, name, producer, base_price, quantity, type, tags, hidden '
            'FROM products '),
            callable=action
        )

    def get_base_prices(self) -> Dict[str, int]:
        """Get a dictionary of product code to base price for all products in the database."""
        products = self.get_all_products(bind=False)
        return {product.code: product.base_price for product in products}

    def get_producers(self) -> Dict[str, str]:
        """Get a dictionary of product code to producers for all products in the database."""
        products = self.get_all_products(bind=False)
        return {product.code: product.producer for product in products}

    def get_types(self) -> List[str]:
        """Get a dictionary of distinct product types for products in the database."""
        products = self.get_all_products(bind=False)
        return list({product.type for product in products})

    def get_quantity_remaining(self) -> Dict[str, int]:
        # SELECT coalesce(orders.product_code, products.code) as code, quantity - COUNT(orders.id)
        #   FROM products
        #   LEFT OUTER JOIN orders ON orders.product_code = products.code
        #   GROUP BY code
        pass  # TODO requires orders

    # order methods

    def insert_order(self, *,
                     buyer: Buyer, product: Product,
                     relativ_cost: int, created_at: Optional[int] = None) -> Order:
        """Insert a new order into the database.

        Args:
            buyer, product, relative_cost, created_at:
                Order parameters. See `Order` for descriptions.

        Returns:
            The inserted order model.

        Raises:
            BearDatabaseError: If the insert operation failed.
            ValueError: If a product parameter is of invalid type.

        See also `import_orders` for inserting multiple orders in the same transaction.
        """
        def action(cursor: sqlite3.Cursor) -> int:
            return cursor.lastrowid

        insered_id = self.exe((
            f'INSERT INTO orders ( '
            f'  buyer_id, product_code, relative_cost{"" if created_at is None else ", created_at"} '
            f') VALUES ( '
            f'  :buyer, :product, :relative_cost{"" if created_at is None else ", :created_at"} '
            f')'),
            callable=action,
            args={
                'buyer': buyer_id,
                'product': product_id,
                'relative_cost': relative_cost,
                'created_at': created_at
            })
        return self.get_order(insered_id)

    def import_orders(self, orders: List[Dict[str, Any]]) -> None:
        """Import orders into the database.

        Orders are supplied as a list of mappings which must accept and return values for
        the same keys as `insert_order` takes as arguments.

        All orders are inserted in the same database transaction, so if one insert failes
        the entire operation is rolled back.

        Args:
            orders: Mapping type as described above.

        Raises:
            BearDatabaseError: If the import failed.

        See also `insert_order` for inserting a single order.
        """
        args = []
        for order in orders:
            args.append({
                'buyer': order['order_id'], 'product_id': product['product_id'],
                'relative_cost': order['relative_cost'], 'created_at': order['created_at'],
            })
        self.exe((
            'INSERT INTO orders ( '
            f'  buyer_id, product_code, relative_cost{"" if created_at is None else ", created_at"} '
            ') VALUES ( '
            f'  :buyer, :product, :relative_cost{"" if created_at is None else ", :created_at"} '
            ')'),
            args=args, many=True
        )

    def update_order(self, order: Order) -> None:
        """Update the order stored in the database.
        The order id  can not be changed.

        Raises:
            BearDatabaseError: If the update query failed.
            BearModelError: If the buyer or product related to the order is not bound to the same
                database as the order.
            ValueError: If the order is not bound to this database.
        """
        if not self.is_model_mine(order):
            raise ValueError('order is not bound to this database')
        if not self.is_model_mine(order.buyer) or not self.is_model_mine(order.product):
            raise BearModelError('buyer or product related to order is not bound to the same database as order')

        self.exe((
            'UPDATE order SET '
            '  buyer_id = :buyer, product_id = :producer, '
            '  relative_cost = :relative_cost, created_at = :created_at '
            'WHERE id = :uid'),
            args={
                'buyer': order.buyer.uid,
                'product': order.product.code,
                'relative_cost': order.relative_cost,
                'created_at': order.created_at,
            }
        )

    def get_order(self, uid: int) -> Order:
        """Get the order with ``uid`` from the database.

        Raises:
            BearDatabaseError: If the database query falied, or the order was not found.
            ValueError: If ``uid`` is not an integer.
        """
        def action(cursor: sqlite3.Cursor) -> Order:
            row = cursor.fetchone()
            if row is not None:
                return Order(
                    uid=row['id'],
                    buyer=self.get_buyer(row['buyer_id']),
                    product=self.get_product(row['product_code']),
                    relative_cost=row['relative_cost'],
                    created_at=row['created_at'],
                    database=self,
                )
            else:
                raise BearDatabaseError(f'could not find order with id: {uid}')
        return self.exe((
            'SELECT id, buyer_id, product_code, relative_cost, created_at '
            'FROM orders '
            'WHERE id = :uid'),
            args={'uid': uid},
            callable=action
        )

    def get_all_orders(self, *, bound: bool = True) -> List[Order]:
        """Get all orders stored in the database, ordered acsending (earliest orders first) by time.

        Args:
            bound: If True bind the order to this database; else bind to nothing.
                Defaults to True.

        Raises:
            BearDatabaseError: If the query failed.
        """
        def action(cursor) -> List[Order]:
            order: List[Order] = []
            for row in cursor:
                order.append(Buyer(
                    uid=row['id'],
                    buyer=self.get_buyer(row['buyer_id']),
                    product=self.get_product(row['product_code']),
                    relative_cost=row['relative_cost'],
                    created_at=row['created_at'],
                    database=self if bound else None,
                ))
            return order
        return self.exe((
            'SELECT id, buyer_id, product_code, relative_cost, created_at '
            'FROM orders '
            'ORDER BY created_at ASC'),
            callable=action
        )

    def get_latest_orders(self, count: int = 1, *, bound: bool = True) -> List[Order]:
        """Get the ``count`` last orders stored in the database, ordered descending
        (newest order first) by time.

        Args:
            count: Number of order rows to get.
            bound: If True bind the order to this database; else bind to nothing.
                Defaults to True.

        Raises:
            BearDatabaseError: If the query failed.
            ValueError: If ``count`` is less than 0.
        """
        if count < 0:
            raise ValueError('cannot retreive a negative number of orders')

        def action(cursor) -> List[Order]:
            order: List[Order] = []
            for row in cursor:
                order.append(Buyer(
                    uid=row['id'],
                    buyer=self.get_buyer(row['buyer_id']),
                    product=self.get_product(row['product_code']),
                    relative_cost=row['relative_cost'],
                    created_at=row['created_at'],
                    database=self if bound else None,
                ))
            return order
        return self.exe((
            'SELECT id, buyer_id, product_code, relative_cost, created_at '
            'FROM orders '
            'ORDER BY created_at DESC LIMIT :count'),
            args={'count': count},
            callable=action
        )

    def get_orders_after(self, t: int,
                         *, exclusive: bool = True, bound: bool = True) -> List[Order]:
        """Get all orders made after time ``t``, ordered ascending (oldest first).

        Args:
            t: Time point ot get orders after.
            exclusive: If ``t`` is exclusive or inclusive. Defaults to True.
            bound: If True bind the order to this database; else bind to nothing.
                Defaults to True.

        Raises:
            BearDatabaseError: If the query failed.
        """
        def action(cursor) -> List[Order]:
            order: List[Order] = []
            for row in cursor:
                order.append(Buyer(
                    uid=row['id'],
                    buyer=self.get_buyer(row['buyer_id']),
                    product=self.get_product(row['product_code']),
                    relative_cost=row['relative_cost'],
                    created_at=row['created_at'],
                    database=self if bound else None,
                ))
            return order
        return self.exe((
            'SELECT id, buyer_id, product_code, relative_cost, created_at '
            'FROM orders '
            f'WHERE created_at {">" if exclusive else ">="} :time '
            'ORDER BY created_at DESC'),
            args={'count': count},
            callable=action
        )

    def get_orders_befores(self, t: int,
                           *, exclusive: bool = True, bound: bool = True) -> List[Order]:
        """Get all orders made befre time ``t``, ordered ascending (oldest first).

        Args:
            t: Time point ot get orders before.
            exclusive: If ``t`` is exclusive or inclusive. Defaults to True.
            bound: If True bind the order to this database; else bind to nothing.
                Defaults to True.

        Raises:
            BearDatabaseError: If the query failed.
        """
        def action(cursor) -> List[Order]:
            order: List[Order] = []
            for row in cursor:
                order.append(Buyer(
                    uid=row['id'],
                    buyer=self.get_buyer(row['buyer_id']),
                    product=self.get_product(row['product_code']),
                    relative_cost=row['relative_cost'],
                    created_at=row['created_at'],
                    database=self if bound else None,
                ))
            return order
        return self.exe((
            'SELECT id, buyer_id, product_code, relative_cost, created_at '
            'FROM orders '
            f'WHERE created_at {"<" if exclusive else "<="} :time '
            'ORDER BY created_at DESC'),
            args={'count': count},
            callable=action
        )

    # price methods

#    def insert_prices(self, prices):
#        data = pickle.dumps(prices)
#        self.e('INSERT INTO prices (data) VALUES (?)', (sqlite3.Binary(data),))

#    def last_price_time(self):
#        row = self.e('SELECT created_at FROM prices ORDER BY id DESC LIMIT 1').fetchone()
#        if row:
#            return datetime.fromtimestamp(row['created_at'])

#    def latest_prices(self, count=1):
#        cursor = self.e('SELECT * FROM prices ORDER BY id DESC LIMIT ?', (count,))
#
#        def mapper(row):
#            prices = pickle.loads(row["data"])
#            prices["_id"] = row["id"]
#            return prices
#
#        rows = torows(cursor, mapper)
#        if count == 1:
#            return rows[0]
#        else:
#            return rows + [None]*(count - len(rows))

#    def find_prices(self, id):
#        row = self.e('SELECT data FROM prices WHERE id = ?', (id,)).fetchone()
#        if row:
#            return pickle.loads(row['data'])

#    def prices_count(self):
#        return self.e('SELECT COUNT(*) FROM prices').fetchone()[0]

#    def price_adjustments(self):
#        # First fetch the prices:
#        prices = torows(self.e('SELECT id, data FROM prices ORDER BY id'))
#
#        # Build a list of dict for each period
#        def defaultval():
#            return {"sold_units": 0, "adjustment": 0}
#        products = defaultdict(lambda: [defaultval() for _ in range(len(prices))])
#
#        price_id_to_idx = {}
#
#        for idx, row in enumerate(prices):
#            price_id_to_idx[row['id']] = idx
#            adjustments = pickle.loads(row['data'])
#
#            for product_code in adjustments:
#                products[product_code][idx]["adjustment"] = adjustments[product_code]
#
#        # Then find the number of products sold per period
#        cursor = self.e("""
#            SELECT price_id, product_code, COUNT(id) as sold_units
#            FROM orders
#            GROUP BY price_id, product_code
#            ORDER BY price_id
#        """)
#
#        for row in cursor:
#            idx = price_id_to_idx[row['price_id']]
#            product_code = row['product_code']
#            products[product_code][idx]['sold_units'] = row['sold_units']
#
#        # Next make sure all products are included:
#        for row in self.e('SELECT code FROM products'):
#            products[row['code']]
#
#        return dict(products)

    # various methods

#    # How much money is on our own account?
#    def stock_account(self):
#        return self.e('SELECT SUM(relative_cost) FROM orders').fetchone()[0] or 0

#    def current_products_with_prices(self, round_price=False):
#        products = []
#        with self.conn:
#            ultimate, penultimate = self.latest_prices(2)
#            if ultimate is None:
#                return products, None
#
#            for product in self.e('SELECT * FROM products WHERE is_hidden = 0'):
#                code = product["code"]
#                rel_cost = ultimate.get(code, 0)
#
#                if penultimate:
#                    delta_cost = rel_cost - penultimate.get(code, rel_cost)
#                else:
#                    delta_cost = 0
#
#                if round_price:
#                    rel_cost = int(round(rel_cost))
#
#                products.append({
#                    "code": code,
#                    "name": product["name"],
#                    "brewery": product["brewery"],
#                    "price_id": ultimate["_id"],
#                    "relative_cost": rel_cost,
#                    "delta_cost": delta_cost,
#                    "base_price": product['base_price'],
#                    "absolute_cost": product['base_price'] + rel_cost,
#                    "tags": product["tags"].split("|")
#                })
#        return products, ultimate["_id"]
#
#    def prices_for_product(self, codes, round_price=False):
#        arr = ", ".join(["?" for _ in codes])
#        base_prices = todict(
#            self.e('SELECT code, base_price FROM products WHERE code IN (%s)' % arr, codes))
#        price_data = defaultdict(lambda: [])
#        cursor = self.e('SELECT * FROM prices ORDER BY id')
#        for row in cursor:
#            prices = pickle.loads(row["data"])
#            for code in codes:
#                price_data[code].append({
#                    "timestamp": row["created_at"],
#                    "value": (
#                        prices.get(code, 0) + base_prices[code] if not round_price else
#                        round(prices.get(code, 0) + base_prices[code])
#                    )
#                })
#        return dict(price_data)


