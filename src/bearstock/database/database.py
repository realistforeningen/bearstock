
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union
DbArgs = Union[Tuple[Any], Dict[str, Any]]
T = TypeVar('T')


import sqlite3

__all__ = ['Database', 'BearDatabaseError']


class BearDatabaseError(RuntimeError):
    pass


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
            raise RuntimeError('database not open')
        return self._connection

    def is_connected(self) -> bool:
        return self._connection is not None

    def connect(self) -> sqlite3.Connection:
        """Connect to the database and do required initializations."""
        if self.is_connected():
            raise RuntimeError('database already open')  # TODO did you really just use RuntimeError...

        self._connection = sqlite3.connect(self.dbname)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute('PRAGMA foreign_keys = ON')

        return DatabaseAccessor(self._database)

    def close(self) -> None:
        """Close to the database connection."""
        if not self.is_connected():
            raise RuntimeError('database already closed')  # TODO did you really just use RuntimeError...
        self._connection.close()

    # generic DB access methods

    def exe(self, sql: str, *,
            args: Optional[DbArgs] = None,
            callable: Optional[Callable[[sqlite3.Cursor], T]] = None) -> Optional[T]:
        """Execute a arbitrary database query.

        Args:
            sql: SQL query.
            args: Optional arguments to the query. Defaults to None.
            callable: Optional action to perform on the cursor after the query have executed.
                Defaults to None.

        Returns:
            If callable is not not return what returned by it; otherwise None.
        """
        result: Optional[T] = None
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(sql=sql, parmeters=args)

            # do something with the query result
            if callable is not None:
                result = callable(cursor)

            cursor.close()

        return result

    # buyer related methods

    def insert_buyer(self, name: str, icon: str, *, scaling: float = 1.0) -> Buyer:
        def inserted_id(cursor: sqlite3.Cursor) -> int:
            return cursor.lastrowid
        inserted_id = self.exe(
                'INSERT INTO buyers ( name, icon, scaling ) VALUES ( :name, :icon, :scaling )',
            {
                'name': name,
                'icon': icon,
                'scaling': scaling
            },
            inserted_id
        )
        return self.get_buyer(inserted_id)

    def update_buyer(self, buyer: Buyer) -> None:
        self.exe(
            'UPDATE buyers SET name = :name, icon = :icon, scaling = :scaling WHERE id = :uid',
            {
                'uid': buyer.uid,
                'name': buyer.name,
                'icon': buyer.icon,
                'scaling': buyer.scaling,
            }
        )

    def get_buyer(self, uid: int) -> Buyer:
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
                return None
        return self.exe(
            'SELECT id, name, icon, scaling, created_at FROM buyers WHERE id = :uid',
            {
                'uid': uid,
            },
            retrive_buyer
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
            {
                'name': name
            },
            retrive_all_buyers
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


#    def latest_orders(self, count=10):
#        cursor = self.e('SELECT * FROM orders ORDER BY id DESC LIMIT ?', (count,))
#        return torows(cursor)
#
#    def import_products(self, products):
#        with self.conn:
#            self.e('PRAGMA defer_foreign_keys = ON')
#            self.e('UPDATE products SET is_hidden = 1')
#
#            for product in products:
#                self.e('DELETE FROM products WHERE code = ?', (product['code'],))
#                taglist = product.get("tags", [])
#                taglist.append(product["brewery"])
#                tags = "|".join(taglist)
#                values = (
#                    product["code"],
#                    product["name"],
#                    product["brewery"],
#                    product["base_price"],
#                    product.get("quantity", 0),
#                    product["type"],
#                    tags
#                )
#                self.e('''
#                    INSERT INTO
#                    products (
#                        code, name, brewery, base_price, quantity, type, tags
#                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
#                ''', values)
#
#    def ensure_prices(self):
#        with self.conn:
#            price_count = self.e('SELECT COUNT(*) FROM prices').fetchone()[0]
#            if price_count == 0:
#                self.insert_prices({})
#
#    def ensure_buyer(self):
#        with self.conn:
#            try:
#                self.insert("buyers", id=1, name="Test Buyer")
#            except sqlite3.IntegrityError:
#                # All fine
#                return
#
#    def insert_prices(self, prices):
#        data = pickle.dumps(prices)
#        self.e('INSERT INTO prices (data) VALUES (?)', (sqlite3.Binary(data),))
#
#    def insert_buyer(self, name):
#        return self.insert("buyers", name=name)
#
#    def read_all_orders(self):
#        return self.e('SELECT * FROM orders')
#
#    def read_products(self):
#        return self.e('SELECT * FROM products')
#
#    # How much money is on our own account?
#    def stock_account(self):
#        return self.e('SELECT SUM(relative_cost) FROM orders').fetchone()[0] or 0
#
#    def last_price_time(self):
#        row = self.e('SELECT created_at FROM prices ORDER BY id DESC LIMIT 1').fetchone()
#        if row:
#            return datetime.fromtimestamp(row['created_at'])
#
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
#
#    def find_prices(self, id):
#        row = self.e('SELECT data FROM prices WHERE id = ?', (id,)).fetchone()
#        if row:
#            return pickle.loads(row['data'])
#
#    def prices_count(self):
#        return self.e('SELECT COUNT(*) FROM prices').fetchone()[0]
#
#    def base_prices(self):
#        cursor = self.e('SELECT code, base_price FROM products')
#        return todict(cursor)
#
#    def breweries(self):
#        cursor = self.e('SELECT code, brewery FROM products')
#        return todict(cursor)
#
#    def types(self):
#        cursor = self.e('SELECT code, type FROM products')
#        return todict(cursor)
#
#    def stock_left(self):
#        cursor = self.e("""
#            SELECT coalesce(orders.product_code, products.code) as code, quantity - COUNT(orders.id)
#            FROM products
#            LEFT OUTER JOIN orders ON orders.product_code = products.code
#            GROUP BY code
#        """)
#        return todict(cursor)
#
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
#
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
#
#    def orders_before(self, ts):
#        return torows(
#            self.e('SELECT * FROM orders WHERE created_at <= ? ORDER BY created_at', (ts,)))


