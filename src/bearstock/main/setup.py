
import argparse as ap
import csv

from bearstock.stock import Database

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
                    else:
                        product[key.replace(' ', '_')] = value
                else:  # extra values are stored under a None key
                    product['tags'].extend(value)
            products.append(product)
    return products

def main(argv=None):

    # parse args
    parser = ap.ArgumentParser()
    parser.add_argument('csv', type=str, help='CSV file to read products from')
    parsed = parser.parse_args()

    # get products
    products = parse_products_csv(parsed.csv)

    # setup DB
    db = Database.default()

    # ensure schema exists
    for statement in open('schema.sql').read().split(';'):
        db.e(statement)
    # ensure a buyer
    db.ensure_buyer()

    # ensure products are in
    db.import_products(products)
