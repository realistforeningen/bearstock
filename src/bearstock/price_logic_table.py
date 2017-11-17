import math
from math import exp
import sys

from typing import (
    List,
    Dict,
    Tuple,
)

from .parameters import Params

## logic

class PriceLogicBase:
    def __init__(
            self,
            current_surplus: float,
            current_period_id: int,
            period_duration: float,
            periods_left: int
    ) -> None:
        """
        Parameters
        ----------

        current_surplus: The current surplus. Can be positive or negtative.
        period_id: Id of the current period. Should startcode at zero.
        period_duration: Length of a period. Unit is seconds.
        periods_left: Number of periods left.
        """
        self.current_surplus = current_surplus

        # period data
        self.current_period_id = current_period_id
        self.period_duration = period_duration
        self.periods_left = periods_left

        # product data
        self.total_products_sold = 0
        self.products = {}
        self.brewery_data = {}
        self.type_data = {}

    def add_product(
            self,
            code: str,
            brewery: str,
            base_price: float,
            products_left: int,
            product_type: float,
            price_data: List[Dict[str, float]],
            params: Params=None
    ) -> None:
        """
        Parameters
        ----------

        code: Product code.
        brewery: Name of the brewery.
        base_price: Product base price.
        products_left: Number of products left.
        product_type: Product type.
        price_data: List of dictionaries each containing the keys 'sold_units' and
            'adjustment'. One element per period.
        params: Parameters.
        """

        # Count products
        sold_products = sum(
            ((data['sold_units'] if 'sold_units' in data else 0) for data in price_data)
        )
        self.total_products_sold += sold_products  # count all products sold all time
        total_products = products_left + sold_products  # compute products left

        # store products sold per brewery
        if brewery.lower() not in self.brewery_data:
            self.brewery_data[brewery.lower()] = 0
        self.brewery_data[brewery.lower()] += sold_products

        # store products sold per type
        if product_type.lower() not in self.type_data:
            self.type_data[product_type.lower()] = 0
        self.type_data[product_type.lower()] += sold_products

        # add product
        self.products[code] = {
            'brewery': brewery.lower(),
            'type': product_type.lower(),
            'base_price': base_price,
            'prev_abs_adj': (price_data[-1]['adjustment'] if len(price_data) > 0 else 0),
            'prev_rel_adj': (
                (price_data[-1]['adjustment'] - price_data[-2]['adjustment'])
                if len(price_data) > 1 else price_data[-1]['adjustment'] if len(price_data) > 0
                else 0
            ),
            'fraction_left': (
                (float(products_left)/total_products)
                if total_products > 0 and products_left >= 0 else 1.0
            ),
            'price_data': price_data,
            'popularity': (
                sold_products/float(self.total_products_sold) if self.total_products_sold > 0 else 0
            ),
            'p': (
                params if params is not None else Params()
            ),
        }

    def finalize(self) -> Dict[str, float]:
        """Finalize the price calculations.

        Returns
        -------
        adjustments: Product code to adjustment dictionary. Missing entries means the
            adjustment is zero.
        """
        adjustments = self._adjust_deficit()    # Compute change in price
        # for code in self.products:
        #     product = self.products[code]
        #     if product['base_price'] + adjustments[code] < product['p'].min_price:
        #         # Is adjustment the new price, or the change in price?
        #         adjustments[code] = product["p"].min_price
        return adjustments


class PriceLogicBasic(PriceLogicBase):
    def _adjust_deficit(self) -> Dict[str, float]:
        periods_left = max(1, self.periods_left)    # Avoid division by zero

        subsidy_this_tick = self.current_surplus/max(1, self.periods_left)
        expected_sales = self._expected_sales()     # numver of beers
        total_expected_sales = max(1, sum(expected_sales.values()))

        adjustment_weights = self._compute_adjustments()

        min_price = 20
        max_price = 200

        adjustments = {code: adjustment_weights[code] for code in adjustment_weights}
        
        deficit_this_tick = self._compute_deficit(adjustment_weights)

        maxiter = 10
        niter = 0
        """
        print(deficit, subsidy_this_tick)
        for code in self.products:
              # The current price is
            current_price = self._get_current_price(code)

            # I am currently subsidisuoiing the beer by this much
            current_subsidy = self.products[code]["base_price"] - current_price

            # I want to subsidise by this much
            subsidy_per_beer = subsidy_this_tick/total_expected_sales*expected_sales[code]

            # # Change in subsidy
            delta_subsidy = subsidy_per_beer - current_subsidy

            # adjustment if not violating min/max price
            tmp_adjustment = adjustment_weights[code] - delta_subsidy

            adjustments[code] = tmp_adjustment
            if current_price + tmp_adjustment <= min_price or \
                    current_price + tmp_adjustment >= max_price:
                adjustments[code] = 0
        """
       
        """
        adjustments = {}
        for code in self.products:
            # The current price is
            current_price = self._get_current_price(code)

            # I am currently subsidisuoiing the beer by this much
            current_subsidy = self.products[code]["base_price"] - current_price

            # I want to subsidise by this much
            subsidy_per_beer = subsidy_this_tick/total_expected_sales*expected_sales[code]

            # Change in subsidy
            delta_subsidy = subsidy_per_beer - current_subsidy

            # adjustment if not violating min/max price
            tmp_adjustment = adjustment_weights[code] - delta_subsidy

            adjustments[code] = tmp_adjustment
            if current_price + tmp_adjustment <= min_price or \
                    current_price + tmp_adjustment >= max_price:
                adjustments[code] = 0
        """
        return adjustments

    def _compute_deficit(self, prices):
        deficit = 0
        for code in self.products:
            deficit += self.products[code]["base_price"] - (self._get_current_price(code) + prices[code])
        return deficit

    def _get_current_price(self, code: str) -> float:
        product = self.products[code]
        base_price = product["base_price"]
        adjustments = sum(map(lambda x: x["adjustment"], product["price_data"]))
        return base_price + adjustments

    def compute_deficit(self, delta_p):
        new_price = {}
        for code in delta_p:
            new_price[code] = self._get_current_price(code) + delta_p[code]
        return sum(new_price.values())

    def _get_subsidy(self) -> float:
        total_subsidy = self.current_surplus/max(1, periods_left)
        return total_subsidy/self._estimate_total_sales()

    def _compute_weight(self, code: str) -> float:
        current_price = self._get_current_price(code)
        base_price = self.products[code]["base_price"]
        # base_adjustment = abs(current_price - base_price)
        base_adjustment = 20

        adjustment_table = [
            -5,
            -2,
            1,
            5,
            10,
        ]


        num_lookback_ticks = 5
        units_sold = self._total_sold(num_lookback_ticks)[code]

        if units_sold == 0:
            return  -5
        if units_sold <= num_lookback_ticks:
            return -2
        if units_sold > num_lookback_ticks:
            return 5
        if units_sold > 10:
            return 10
        # total_sold = max(1, sum(units_sold.values()))
        # frac = units_sold[code]/total_sold/100

        # if frac < 0.05:
        #     return adjustment_table[0]
        # elif frac < 0.1:
        #     return adjustment_table[1]
        # elif frac < 0.2:
        #     return adjustment_table[2]
        # elif frac < 0.3:
        #     return adjustment_table[3]
        return adjustment_table[4]

    def _compute_adjustments(self) -> Dict[str, float]:
        """This is where the magic happens."""
        weights = {code: self._compute_weight(code) for code in self.products}
        total_weight = max(1, sum(weights.values()))

        for code in self.products:
            weights[code] /= total_weight
        return weights

    def _expected_sales(self) -> Dict[str, float]:
        """Compute expected sales for a product with code."""
        expected_sales = {}
        for code in self.products:
            # List of time points
            times = list(range(len(self.products[code]["price_data"])))

            # List of past sales
            sales = [self.products[code]["price_data"][t]["sold_units"] for t in times]

            # List of weights
            weights = [exp(-(self.current_period_id - t + 1)) for t in times]

            # Compute weights average
            expected_sales[code] = sum([w*s for w, s in zip(weights, sales)])/sum(weights)

        return expected_sales

    def _total_sold(self, N: int) -> Dict[str, float]:
        """Compute the total number of sold beer over N past ticks."""
        total_sold = {}
        for code in self.products:
            product = self.products[code]
            total_sold[code] = sum(map(
                lambda x: x["sold_units"],
                product["price_data"][::-1][:N]
            ))
        return total_sold
