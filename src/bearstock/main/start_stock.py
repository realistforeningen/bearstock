
from bearstock.stock import DATABASE_FILE
from bearstock.database import Database

def main(argv=None):
    db = Database(DATABASE_FILE)

