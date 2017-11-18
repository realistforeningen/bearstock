from collections import defaultdict
from datetime import datetime
from threading import Thread
import logging
import pickle
import sqlite3
import time

from bearstock.database import Database
from bearstock.price_logic_table import PriceLogic


class Exchange:
    """Server running the stock exchange."""

    DATABASE_FILE = 'bear-app.db'

    def __init__(self, db):
        self.db = db

        self.logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create and configurate the logger instance."""
        logger: logging.Logger = logging.getLogger(Exchange.__name__)
        logger.setLevel(logging.DEBUG)

        fmt = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)

        fh = logging.FileHandler(f'Exchange-{time.time()}.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(fmt)

        logger.addHandler(sh)
        logger.addHandler(fh)

        return logger

    @classmethod
    def run_default(self):
        db = Database(Exchange.DATABASE_FILE)
        db.connect()

        Exchange(db).run()

    @classmethod
    def run_in_thread(self):
        thread = Thread(target=self.run_default(),
                        name='BearStock-exchange',
                        daemon=True)
        thread.start()

    def run(self):
        self.logger.info('Running stock in the background')

        while True:
            # checkk if the stock is started
            if not self.db.get_config_stock_running():
                self.logger.info('Stock is closed')
                time.sleep(10)
                continue

            # determine wait
            self.logger.info('Stock is ticking')

            pending = self.db.get_tick_last_timestamp() - time.time()
            if pending <= 0:
                pending = self.db.get_config_tick_length()

            if pending > 0:
                self.logger.info(f'Stock is waiting for {pending} s')
                time.sleep(pending)

            # action!
            self.logger.info('Stock is about perform tick')
            self.tick()

    def tick(self):
        # what's left of the budget
        surplus = self.db.get_config_budget() + self.db.get_purchase_surplus()

        # the index/number of the tick we are about to do and how many are left
        tick_no = self.db.get_tick_number()
        ticks_left = self.db.get_config_total_ticks() - tick_no

        self.logger.info(f'Performing tick #{tick_no} - {ticks_left} ticks left')

        # the price computations should never see zero or negative tick id's
        if ticks_left <= 0:
            self.logger.error('The stock should be closed! Past the last tick!')
            periods_left = 1

        pl = PriceLogic(
            current_surplus=surplus,
            current_period_id=tick_no,
            period_duration=self.db.get_config_tick_length(),
            periods_left=ticks_left,
        )

        # current price adjustments before computation
        included_products = []
        hidden_products = []
        for product in self.db.get_all_products():
            if not product.hidden:
                included_products.append(product)
            else:
                hidden_products.append(product)

        # add products to teh computation
        for product in included_products:
            self.logger.info(f'Adding product {product.code} to the price calculation.')
            pl.add_product(
                product=product,
                # parameters=parameters,  # TODO get parametres for code (db)
            )

        # dict: product.code -> adjustment float (unit of one currency)
        self.logger.info('Performing price calculation finalization')
        new_adjustments = pl.finalize()   # TODO

        hardcoded_min_price = 2000

        # construct adjustments for db
        completed_adjustments = {}
        for product in hidden_products:
            completed_adjustments[product.code] = product.price_adjustment
        for product in included_products:
            adj = int(round(new_adjustments[product.code]*100))
            if product.base_price + adj < hardcoded_min_price:
                pass
                # adj = product.base_price - hardcoded_min_price
            completed_adjustments[product.code] = adj

        # register the new tick in the database
        self.logger.info(f'Storing new price adjustments: {completed_adjustments}')
        self.db.do_tick(completed_adjustments)
