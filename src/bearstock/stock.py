
from threading import Thread
import time
from datetime import datetime
import sqlite3
import pickle
from collections import defaultdict

from bearstock.database import Database
from bearstock.price_logic import PriceLogic, Params

default_params = {
    # lookback
    'ex_periods': 12,
    'ex_lookback': 12,
    # decrease
    'decrease_scaling': 0.0075,
    'acqu_weight': 3,
    'prev_abs_adjust_weight': 2,
    'prev_rel_adjust_weight': 4,
    'time_since_sale_weight': 9,
    'time_since_sale_power': 1.02,
    # increase
    'increase_scaling': 0.6,
    'past_purchase_importance': 15.0,
    # min price
    'min_price': 5.,
}
# product code to parameters, parameter keys are given above
product_parameters = {

}

# def todict(cursor, key_field=0, value_field=1):
#     res = {}
#     for row in cursor:
#         res[row[key_field]] = row[value_field]
#     return res
#
# def dictmapper(row):
#     data = {}
#     for key in row.keys():
#         data[key] = row[key]
#     return data
#
# def torows(cursor, mapper=dictmapper):
#     return [mapper(row) for row in cursor]

class Exchange:
    """Server running the stock exchange."""

    @classmethod
    def run_in_thread(self):
        thread = Thread(target=self.run_default)
        thread.daemon = True
        thread.start()

    @classmethod
    def run_default(self):
        Exchange(Database.default()).run()

    BUDGET = 5000 - 856
    PERIOD_DURATION = 5*60  # [s]
    EVENT_LENGTH = 6*60*60  # [s]
    TOTAL_PERIOD_COUNT = EVENT_LENGTH / PERIOD_DURATION

    def __init__(self, db):
        self.db = db

    def run(self):
        print("* Running stock in the background")

        # set default parameters
        Params.set_default_from_dict(default_params)

        while True:
            ts = self.db.last_price_time()

            if ts is None:
                print("* Stock is closed")
                time.sleep(10)
                continue

            print(" * Stock is ticking")
            now = datetime.now()
            elapsed = (now - ts).total_seconds()
            pending = self.PERIOD_DURATION - elapsed
            if pending > 0:
                time.sleep(pending)
            self.tick()

    def tick(self):
        # database transaction
        with self.db.conn:
            surplus = self.BUDGET + self.db.stock_account()
            period_count = self.db.prices_count()
            period_id = period_count - 1
            periods_left = self.TOTAL_PERIOD_COUNT - period_count

            pl = PriceLogic(
                current_surplus=surplus,
                period_id=period_id,
                period_duration=self.PERIOD_DURATION,
                periods_left=periods_left
            )

            base_prices = self.db.base_prices()
            stock_left = self.db.stock_left()
            price_adjustments = self.db.price_adjustments()
            breweries = self.db.breweries()
            types = self.db.types()

            for key in base_prices:
                # update params
                params = None
                if key in product_parameters:
                    params = Params(params=product_parameters[key])
                # add product
                pl.add_product(
                    code=key,
                    brewery=breweries[key],
                    base_price=base_prices[key],
                    products_left=stock_left[key],
                    prod_type=types[key],
                    price_data=price_adjustments[key],
                    params=params
                )

            new_adjustments = pl.finalize()
            for key in new_adjustments:
                new_adjustments[key] = new_adjustments[key]
            self.db.insert_prices(new_adjustments)

if __name__ == '__main__':
    Exchange.run_default()
