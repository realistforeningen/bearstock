
import argparse

from bearstock.stock import Exchange
from bearstock.database import Database

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, required=True)
    parsed = parser.parse_args()

    db = Database(Exchange.DATABASE_FILE)
    db.connect()

    db.set_config_quarantine(parsed.seconds)
    print(f'Quarantine time set to {parsed.seconds}')

    db.close()

