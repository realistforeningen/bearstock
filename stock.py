from threading import Thread
import time
from datetime import datetime
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
        res = self.e(sql, values)
        return res.lastrowid

    def import_products(self, products):
        for product in products:
            with self.conn:
                self.e('DELETE FROM products WHERE code = ?', (product['code'],))
                taglist = product.get("tags", [])
                taglist.append(product["brewery"])
                tags = "|".join(taglist)
                values = (
                    product["code"],
                    product["name"],
                    product["brewery"],
                    product["base_price"],
                    product.get("quantity", 0),
                    product["type"],
                    tags
                )
                self.e('INSERT INTO products (code, name, brewery, base_price, quantity, type, tags) VALUES (?, ?, ?, ?, ?, ?, ?)', values)

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

    def insert_buyer(self, name):
        return self.insert("buyers", name=name)

    # How much money is on our own account?
    def stock_account(self):
        return self.e('SELECT SUM(relative_cost) FROM orders').fetchone()[0] or 0

    def last_price_time(self):
        row = self.e('SELECT created_at FROM prices ORDER BY id DESC LIMIT 1').fetchone()
        if row:
            return datetime.fromtimestamp(row['created_at'])

    def latest_prices(self, count = 1):
        cursor = self.e('SELECT * FROM prices ORDER BY id DESC LIMIT ?', (count,))

        def mapper(row):
            prices = pickle.loads(row["data"])
            prices["_id"] = row["id"]
            return prices

        rows = torows(cursor, mapper)
        if count == 1:
            return rows[0]
        else:
            return rows

    def find_prices(self, id):
        row = self.e('SELECT data FROM prices WHERE id = ?', (id,)).fetchone()
        if row:
            return pickle.loads(row['data'])

    def prices_count(self):
        return self.e('SELECT COUNT(*) FROM prices').fetchone()[0]

    def base_prices(self):
        cursor = self.e('SELECT code, base_price FROM products')
        return todict(cursor)

    def breweries(self):
        cursor = self.e('SELECT code, brewery FROM products')
        return todict(cursor)

    def types(self):
        cursor = self.e('SELECT code, type FROM products')
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

    def current_products_with_prices(self, round_price=False):
        products = []
        with self.conn:
            ultimate, penultimate = self.latest_prices(2)
            for product in self.e('SELECT * FROM products'):
                code = product["code"]
                rel_cost = ultimate.get(code, 0)

                if penultimate:
                    delta_cost = rel_cost - penultimate.get(code, rel_cost)
                else:
                    delta_cost = 0

                products.append({
                    "code": code,
                    "name": product["name"],
                    "brewery": product["brewery"],
                    "price_id": ultimate["_id"],
                    "relative_cost": rel_cost,
                    "delta_cost": delta_cost,
                    "absolute_cost": (
                        product['base_price'] + rel_cost if not round_price else
                        round(product['base_price'] + rel_cost)
                    ),
                    "tags": product["tags"].split("|")
                })
        return products, ultimate["_id"]

    def prices_for_product(self, codes, round_price=False):
        arr = ", ".join(["?" for _ in codes])
        base_prices = todict(self.e('SELECT code, base_price FROM products WHERE code IN (%s)' % arr, codes))
        price_data = defaultdict(lambda: [])
        cursor = self.e('SELECT * FROM prices ORDER BY id')
        for row in cursor:
            prices = pickle.loads(row["data"])
            for code in codes:
                price_data[code].append({
                    "timestamp": row["created_at"],
                    "value": (
                        prices.get(code, 0) + base_prices[code] if not round_price else
                        round(prices.get(code, 0) + base_prices[code])
                    )
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
            ts = self.db.last_price_time()
            now = datetime.now()
            elapsed = (now - ts).total_seconds()
            pending = self.PERIOD_DURATION - elapsed
            if pending > 0:
                time.sleep(pending)
            self.tick()

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
            breweries = self.db.breweries()
            types = self.db.types()

            for key in base_prices:
                pl.add_product(
                    code=key,
                    brewery=breweries[key],
                    base_price=base_prices[key],
                    products_left=stock_left[key],
                    prod_type=types[key],
                    price_data=price_adjustments[key]
                )

            new_adjustments = pl.finalize()
            for key in new_adjustments:
                new_adjustments[key] = new_adjustments[key]
            self.db.insert_prices(new_adjustments)
