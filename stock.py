from threading import Thread
import time
import sqlite3
import pickle

def todict(cursor, key_field=0, value_field=1):
    res = {}
    for row in cursor:
        res[row[key_field]] = row[value_field]
    return res

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

    def insert_prices(self, prices):
        data = pickle.dumps(prices)
        self.e('INSERT INTO prices (data) VALUES (?)', (data,))

    # How much money is on our own account?
    def stock_account(self):
        return self.e('SELECT SUM(stock_cost) FROM orders').fetchone()[0]

    def sold_products(self):
        return todict(self.e('SELECT product_code, COUNT(*) FROM orders GROUP BY product_code'))

    def latest_prices(self):
        row = self.e('SELECT * FROM prices ORDER BY id DESC LIMIT 1').fetchone()
        assert row is not None
        prices = pickle.loads(row["data"])
        prices["_id"] = row["id"]
        return prices

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
            time.sleep(5*60)

