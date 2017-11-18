
import argparse

from bearstock.stock import Exchange
from bearstock.database import Database

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--on', action='store_true')
    group.add_argument('--off', action='store_true')
    parsed = parser.parse_args()

    if not parsed.on and not parsed.off:
        print('please supply eithe \'--on\' or \'--off\'')
    else:
        db = Database(Exchange.DATABASE_FILE)
        db.connect()

        if parsed.on:
            db.set_config_stock_running(True)
            print('Ticks turned ON')
        else:
            db.set_config_stock_running(False)
            print('Ticks turned OFF')

        db.close()

