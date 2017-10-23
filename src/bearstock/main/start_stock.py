
from bearstock.stock import Database

def main(argv=None):
    db = Database.default()
    db.ensure_prices()

