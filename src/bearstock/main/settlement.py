
import argparse as ap
import csv
import cStringIO
import codecs
from pprint import pprint as pp
from bearstock.stock import Database
from sys import stdout

def single_char(text):
    text = str(text)
    if len(text) != 1:
        raise TypeError("char string not of length 1")
    return text

def main(argv=None):

    # setup arguments
    parser = ap.ArgumentParser(
        description='Generate a settlement report from database.'
    )
    parser.add_argument(
        '--csv', dest='csv', action='store_true',
        help='Write the results as csv, otherwise print the raw dict data.')
    parser.add_argument(
        '-of', '--outfile', dest='out', type=str, default=None,
        help='File to write report to. Default is to write to standard output.')
    # CSV options
    csv_opt = parser.add_argument_group(
        title='CSV options',
        description='Only active is the \'--csv\' argument is passed.'
    )
    # csv field options
    csv_opt.add_argument(
        '-pt', '--product_title', dest='title_col', type=str, default='name',
        help='Title of the \'product title\' column. (Default: %(default)s)')
    csv_opt.add_argument(
        '-pc', '--product_count', dest='count_col', type=str, default='count',
        help='Title of the \'product count\' column. (Default: %(default)s)')
    csv_opt.add_argument(
        '-ps', '--product_sales', dest='sales_col', type=str, default='turnover',
        help='Title of the \'product sales total\' column. (Default: %(default)s)')
    # csv file options
    csv_opt.add_argument(
        '--delimiter', dest='delim', type=single_char, default=';',
        help='CSV delimiter character. (Default: %(default)s)')
    csv_opt.add_argument(
        '--quote', dest='quote', type=single_char, default='"',
        help='CSV quote character. (Default: %(default)s)')
    csv_opt.add_argument(
        '--escape', dest='escape', type=single_char, default='\\',
        help='CSV escape character. (Default: %(default)s)')
    # parse
    args = parser.parse_args()

    # parse DB
    db = Database.default()
    orders = db.read_all_orders()
    # read products
    db_products = db.read_products()

    # get product data
    products = {}
    for product in db_products:
        code, name, brewery, bp, qnty, type_, tags, hidden = product
        products[code] = {
            'name': name,
            'brewery': brewery
        }

    # count sales
    sales = {}  # product to list(# sold, turnover)
    for order in orders:
        # Order fields
        #   oid       : order id
        #   bid       : buyer id
        #   code      : product code
        #   pid       : price id
        #   rel_cost  : relative cost from product base price
        #   abs_cost  : absolut cost the buyer paid
        #   timestamp : order timestamp
        oid, bid, code, pid, rel_cost, abs_cost, timestamp = order
        if code not in sales:
            sales[code] = {
                'name': '%s %s' % (products[code]['brewery'], products[code]['name']),
                'count': 0,
                'turnover': 0,
            }
        sales[code]['count'] += 1
        sales[code]['turnover'] += abs_cost

    # setup output
    stream = cStringIO.StringIO()
    ecoder = codecs.getincrementalencoder('utf-8')()
    outfile = open(args.out, 'w') if args.out is not None else stdout
    # determine writing format
    if args.csv:
        # setup dialect
        csv.register_dialect(
            'settlement_dialect',
            delimiter=args.delim,
            quotechar=args.quote,
            escapechar=args.escape
        )
        # write
        fieldnames = [args.title_col, args.count_col, args.sales_col]
        with outfile as o:
            writer = csv.DictWriter(stream, dialect='settlement_dialect', fieldnames=fieldnames)
            # write header
            writer.writeheader()
            print >> o, stream.getvalue().strip().decode('utf-8')  # fetch utf-8 data
            stream.truncate(0)  # empty stream
            # write data
            for code in sales:
                title = '%s %s' % (products[code]['brewery'], products[code]['name'])
                # format csv row
                writer.writerow({
                    args.title_col.encode('utf-8'): title.encode('utf-8'),
                    args.count_col.encode('utf-8'): sales[code]['count'],
                    args.sales_col.encode('utf-8'): sales[code]['turnover'],
                })
                print >> o, stream.getvalue().strip().decode('utf-8')  # fetch utf-8 data
                stream.truncate(0)  # empty stream
    else:
        # write
        with outfile as o:
            pp(sales, stream=stream)  # format
            print >> o, stream.getvalue().strip().decode('utf-8')  # fetch utf-8 data
            stream.truncate(0)  # empty stream

