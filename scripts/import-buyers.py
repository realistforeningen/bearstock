import sys
import csv

from bearstock.database import Database
from bearstock.stock import Exchange

db = Database(Exchange.DATABASE_FILE)
db.connect()

filename = sys.argv[1]

with open(filename, 'r') as csvfile:
    # detect dialect
    dialect = csv.Sniffer().sniff(csvfile.readline().rstrip(',;\t'))
    csvfile.seek(0)
    # parse
    reader = csv.reader(csvfile, dialect=dialect)
    next(reader)
    for row in reader:
    	name = row[4]
    	username = row[5]
    	db.insert_buyer(name=name, username=username, icon=None)


