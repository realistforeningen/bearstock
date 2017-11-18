
import argparse as ap
import csv

from bearstock.stock import Exchange
from bearstock.database import Database

def parse_products_csv(filename):
    products = []
    with open(filename, 'r') as csvfile:
        # detect dialect
        dialect = csv.Sniffer().sniff(csvfile.readline().rstrip(',;\t'))
        csvfile.seek(0)
        # parse
        for row in csv.DictReader(csvfile, restval='extratags', dialect=dialect):
            product = {'code': '', 'tags': [], 'hidden': False}
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
                elif value:  # extra values are stored under a None key
                    if not isinstance(value, list):
                        value = [value]
                    product['tags'] += value
            products.append(product)
    return products

def main():

    # parse args
    parser = ap.ArgumentParser()
    parser.add_argument('csv', type=str, help='CSV file to read products from')
    parser.add_argument('--budget', metavar='budget',
                        type=int, required=True, help='Total budget to initialize db with.')
    parser.add_argument('--tick-length', metavar='tick_length',
                        type=int, required=True, help='The length of a tick.')
    parser.add_argument('--tick-count', metavar='tick_count',
                        type=int, required=True, help='Total number of planned ticks.')
    parsed = parser.parse_args()

    # get products and construct zero adjustments
    products = parse_products_csv(parsed.csv)
    adjustments = {product['code']: 0 for product in products}

    # setup DB
    db = Database(Exchange.DATABASE_FILE)
    db.connect()

    # ensure schema exists
    for statement in open('schema.sql').read().split(';'):
        db.exe(statement)

    # set configuration
    db.set_config_stock_running(False)
    db.set_config_budget(parsed.budget)
    db.set_config_tick_length(parsed.tick_length)
    db.set_config_total_ticks(parsed.tick_count)

    db.import_products(products, replace_existing=True)
    try:
        db.do_tick(adjustments, tick_no=0)
    except Exception as e:
        print('tick data already exsist')
        print(f'error: {e}')

    db.close()

