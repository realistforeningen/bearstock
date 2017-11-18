
import argparse

from bearstock.stock import Exchange
from bearstock.database import Database

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('product', metavar='product-code', type=str)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--on', action='store_true')
    group.add_argument('--off', action='store_true')
    parsed = parser.parse_args()

    if not parsed.on and not parsed.off:
        print('please supply either \'--on\' or \'--off\'')
    else:
        db = Database(Exchange.DATABASE_FILE)
        db.connect()

        product = db.get_product(parsed.product)

        if parsed.on:
            product.hidden = False
            product.update_in_db()
            print(f'Product \'{parsed.product}\' turned ON')
        else:
            product.hidden = True
            product.update_in_db()
            print(f'Product \'{parsed.product}\' turned OFF')

        db.close()

