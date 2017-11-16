
import argparse as ap
import csv

from bearstock.stock import DATABASE_FILE
from bearstock.database import Database

def parse_products_csv(filename):
    products = []
    with open(filename, 'r') as csvfile:
        # detect dialect
        dialect = csv.Sniffer().sniff(csvfile.readline().rstrip(',;\t'))
        csvfile.seek(0)
        # parse
        for row in csv.DictReader(csvfile, restval='extratags', dialect=dialect):
            product = {'code': '', 'tags': []}
            for key, value in row.items():
                if key:
                    # ensure unicode
                    key = key.lower()
                    if key == 'brewery code':
                        product['code'] = ''.join([value, product['code']])
                    elif key == 'name code':
                        product['code'] = ''.join([product['code'], value])
                    elif key == 'tags':
                        product['tags'].append(value)
                    elif key in ['base price', 'quantity']:
                        product[key.replace(' ', '_')] = int(value) if value else 0
                    elif key == 'brewery':
                        product['producer'] = value
                    elif key == 'hidden':
                        product['hidden'] = value is not None and value != ''
                    else:
                        product[key.replace(' ', '_')] = value
                else:  # extra values are stored under a None key
                    product['tags'].append(value)
            products.append(product)
    return products

def main():

    # parse args
    parser = ap.ArgumentParser()
    parser.add_argument('csv', type=str, help='CSV file to read products from')
    parsed = parser.parse_args()

    # get products and construct zero adjustments
    products = parse_products_csv(parsed.csv)
    adjustments = {product['code']: 0 for product in products}

    # setup DB
    db = Database(DATABASE_FILE)
    db.connect()

    # ensure schema exists
    for statement in open('schema.sql').read().split(';'):
        db.exe(statement)

    db.import_products(products, replace_existing=True)
    try:
        db.do_tick(adjustments, tick_no=0)
    except Exception as e:
        print('tick data already exsist')
        print(f'error: {e}')

    db.close()

