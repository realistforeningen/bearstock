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
                values = (product["code"], product["name"], product["base_price"], tags)
                self.e('INSERT INTO products (code, name, base_price, quantity, tags) VALUES (?, ?, ?, 0, ?)', values)

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
        return self.e('SELECT SUM(relative_cost) FROM orders').fetchone()[0]

    def latest_prices(self):
        row = self.e('SELECT * FROM prices ORDER BY id DESC LIMIT 1').fetchone()
        assert row is not None
        prices = pickle.loads(row["data"])
        prices["_id"] = row["id"]
        return prices

    def base_prices(self):
        cursor = self.e('SELECT produce_code, base_price FROM products')
        return todict(cursor)

    def stock_left(self):
        cursor = self.e("""
            SELECT orders.product_code, products.quantity - COUNT(orders.id)
            FROM orders
            JOIN products ON orders.product_code = products.code
            GROUP BY product_code
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
                products[product_code][idx]["adjustment"] = adjustments[key]

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

        return dict(products)

    def current_products_with_prices(self):
        products = []
        with self.conn:
            prices = self.latest_prices()
            for product in self.e('SELECT * FROM products'):
                code = product["code"]
                products.append({
                    "code": code,
                    "name": product["name"],
                    "price": product["base_price"] + prices.get(code, 0),
                    "tags": product["tags"].split("|")
                })
        return products, prices

    def current_products_with_history(self):
        prices = self.latest_prices()
        sold_products = self.sold_products()

        products = {}

        for product in self.e('SELECT * FROM products'):
            code = product["code"]
            products[code] = {
                "base_price": product["base_price"],
                "last_price": prices[code],
                "quantity": product["quantity"] - sold_products[code],
                "price_id": prices["_id"]
            }

        return products

    def update_prices(data):
        sdata = pickle.dumps(data)
        self.e('INSERT INTO prices (data) VALUES (?)', (sdata,))

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

    def __init__(self, db):
        self.db = db

    def run(self):
        print " * Running stock in the background"

        while True:
            print " * Stock is ticking"
            self.tick()
            time.sleep(5*60)

    def tick(self):
        # self.db.fetchAllDataRequired()
        # prices = self.runEivindMagic()
        # self.db.insertPrices(prices)
        pass

