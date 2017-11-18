
import argparse

from bearstock.stock import Exchange
from bearstock.database import Database

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--adj', type=int, required=True)
    parser.add_argument('--min', type=int, required=True)
    parsed = parser.parse_args()

    db = Database(Exchange.DATABASE_FILE)
    db.connect()

    all_products = db.get_all_products(include_hidden=True)
    for product in all_products:
        old_price = product.base_price
        new_price = max(old_price + parsed.adj, parsed.min)
        product.base_price = new_price
        product.update_in_db()
        print(f'Adjusted price for \'{product.code}\' from  {old_price}  to  {new_price}')

    print(f'Adjusted all products by {parsed.adj} NOK')

    db.close()

