from threading import Thread
import time
import sqlite3
import pickle
from collections import defaultdict

def todict(cursor, key_field=0, value_field=1):
    res = {}
    for row in cursor:
        res[row[key_field]] = row[value_field]
    return res

def dictmapper(row):
    data = {}
    for key in row.keys():
        data[key] = row[key]
    return data

def torows(cursor, mapper=dictmapper):
    return [mapper(row) for row in cursor]

class Database:
    @classmethod
    def default(self):
        return self('app.db')

    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = sqlite3.Row
        self.e('PRAGMA foreign_keys = ON')

    def close(self):
        self.conn.close()

    def e(self, *args):
        return self.conn.execute(*args)

    def insert(self, table, **data):
        keys = []
        values = []
        placeholders = []
        for key in data:
            keys.append(key)
            values.append(data[key])
            placeholders.append('?')

        sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table, ', '.join(keys), ', '.join(placeholders))
        return self.e(sql, values)

    def import_products(self, products):
        for product in products:
            with self.conn:
                self.e('DELETE FROM products WHERE code = ?', (product['code'],))
                tags = "|".join(product["tags"])
                values = (
                    product["code"],
                    product["name"],
                    product["base_price"],
                    product.get("quantity", 0),
                    tags
                )
                self.e('INSERT INTO products (code, name, base_price, quantity, tags) VALUES (?, ?, ?, ?, ?)', values)

    def ensure_prices(self):
        with self.conn:
            price_count = self.e('SELECT COUNT(*) FROM prices').fetchone()[0]
            if price_count == 0:
                self.insert_prices({})

    def ensure_buyer(self):
        with self.conn:
            try:
                self.insert("buyers", id=1, name="Test Buyer")
            except sqlite3.IntegrityError:
                # All fine
                return

    def insert_prices(self, prices):
        data = pickle.dumps(prices)
        self.e('INSERT INTO prices (data) VALUES (?)', (data,))

    # How much money is on our own account?
    def stock_account(self):
        return self.e('SELECT SUM(relative_cost) FROM orders').fetchone()[0] or 0

    def latest_prices(self):
        row = self.e('SELECT * FROM prices ORDER BY id DESC LIMIT 1').fetchone()
        assert row is not None
        prices = pickle.loads(row["data"])
        prices["_id"] = row["id"]
        return prices

    def find_prices(self, id):
        row = self.e('SELECT data FROM prices WHERE id = ?', (id,)).fetchone()
        if row:
            return pickle.loads(row['data'])

    def prices_count(self):
        return self.e('SELECT COUNT(*) FROM prices').fetchone()[0]

    def base_prices(self):
        cursor = self.e('SELECT code, base_price FROM products')
        return todict(cursor)

    def stock_left(self):
        cursor = self.e("""
            SELECT coalesce(orders.product_code, products.code) as code, quantity - COUNT(orders.id)
            FROM products
            LEFT OUTER JOIN orders ON orders.product_code = products.code
            GROUP BY code
        """)
        return todict(cursor)

    def price_adjustments(self):
        # First fetch the prices:
        prices = torows(self.e('SELECT id, data FROM prices ORDER BY id'))

        # Build a list of dict for each period
        def defaultval():
            return {"sold_units": 0, "adjustment": 0}
        products = defaultdict(lambda: [defaultval() for _ in xrange(len(prices))])

        price_id_to_idx = {}

        for idx, row in enumerate(prices):
            price_id_to_idx[row['id']] = idx
            adjustments = pickle.loads(row['data'])

            for product_code in adjustments:
                products[product_code][idx]["adjustment"] = adjustments[product_code]

        # Then find the number of products sold per period
        cursor = self.e("""
            SELECT price_id, product_code, COUNT(id) as sold_units
            FROM orders
            GROUP BY price_id, product_code
            ORDER BY price_id
        """)

        for row in cursor:
            idx = price_id_to_idx[row['price_id']]
            product_code = row['product_code']
            products[product_code][idx]['sold_units'] = row['sold_units']

        # Next make sure all products are included:
        for row in self.e('SELECT code FROM products'):
            products[row['code']]

        return dict(products)

    def find_buyer(self, buyer_id):
        cursor = self.e('SELECT * FROM buyers WHERE id = ?', (buyer_id,))
        row = cursor.fetchone()
        if row:
            return dictmapper(row)

    def current_products_with_prices(self):
        products = []
        with self.conn:
            prices = self.latest_prices()
            for product in self.e('SELECT * FROM products'):
                code = product["code"]
                rel_cost = prices.get(code, 0)
                products.append({
                    "code": code,
                    "name": product["name"],
                    "price_id": prices["_id"],
                    "relative_cost": rel_cost,
                    "absolute_cost": product["base_price"] + rel_cost,
                    "tags": product["tags"].split("|")
                })
        return products, prices["_id"]

    def prices_for_product(self, codes):
        assert len(codes) == 2  # TODO: bother implementing this properly
        base_prices = todict(self.e('SELECT code, base_price FROM products WHERE code IN (?, ?)', codes))
        price_data = defaultdict(lambda: [])
        cursor = self.e('SELECT * FROM prices ORDER BY id')
        for row in cursor:
            prices = pickle.loads(row["data"])
            for code in codes:
                price_data[code].append({
                    "timestamp": row["created_at"],
                    "value": prices.get(code, 0) + base_prices[code]
                })
        return dict(price_data)

    def orders_before(self, ts):
        return torows(self.e('SELECT * FROM orders WHERE created_at <= ? ORDER BY created_at', (ts,)))

from price_logic import PriceLogic

# Responsible for running the actual stock exchange
class Exchange:
    @classmethod
    def run_in_thread(self):
        thread = Thread(target=self.run_default)
        thread.daemon = True
        thread.start()

    @classmethod
    def run_default(self):
        Exchange(Database.default()).run()

    BUDGET = 2000
    PERIOD_DURATION = 5*60  # [s]
    EVENT_LENGTH = 6*60*60  # [s]
    TOTAL_PERIOD_COUNT = EVENT_LENGTH / PERIOD_DURATION

    def __init__(self, db):
        self.db = db

    def run(self):
        print " * Running stock in the background"

        while True:
            print " * Stock is ticking"
            self.tick()
            time.sleep(self.PERIOD_DURATION)

    def tick(self):
        with self.db.conn:
            surplus = self.BUDGET + self.db.stock_account()
            period_count = self.db.prices_count()
            period_id = period_count - 1
            periods_left = self.TOTAL_PERIOD_COUNT - period_count

            pl = PriceLogic(
                current_surplus=surplus,
                period_id=period_id,
                period_duration=self.PERIOD_DURATION,
                periods_left=periods_left
            )

            base_prices = self.db.base_prices()
            stock_left = self.db.stock_left()
            price_adjustments = self.db.price_adjustments()

            for key in base_prices:
                pl.add_product(
                    code=key,
                    base_price=base_prices[key],
                    price_data=price_adjustments[key],
                    products_left=stock_left[key]
                )

            new_adjustments = pl.finalize()
            for key in new_adjustments:
                new_adjustments[key] = int(new_adjustments[key])
            self.db.insert_prices(new_adjustments)
