import math
from math import exp
import sys

from typing import (
    List,
    Dict,
    Tuple,
)

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
            params=None
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
                None
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
        return adjustments


class PriceLogicBasic(PriceLogicBase):
    def _adjust_deficit(self) -> Dict[str, float]:
        periods_left = max(1, self.periods_left)    # Avoid division by zero

        expected_sales = self._expected_sales()     # numver of beers
        total_expected_sales = max(1, sum(expected_sales.values()))
        target_deficit = self._get_subsidy()

        adjustments = self._compute_adjustments()

        min_price = 20
        max_price = 200
        
        deficits = {
            code: self._get_current_price(code) + adjustments[code] for code in adjustments
        }
        deficits = {}
        for code in self.products:
            deficits[code] = self._get_current_price(code) + adjustments[code]
            deficits[code] *= self._expected_sales()[code]

        total_deficits = sum(deficits.values())
        if total_deficits == 0:
            total_deficits = 1

        correction_weights = {
            code: 1 - deficits[code]/total_deficits for code in adjustments
        }

        for code in adjustments:
            if self._get_current_price(code) + adjustments[code] < min_price:
                adjustments[code] = 0
            elif self._get_current_price(code) + adjustments[code] > max_price: 
                adjustments[code] = 0

            adjustments[code] *= correction_weights[code]

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
        total_subsidy = self.current_surplus/max(1, self.periods_left)
        estimate_total_sales = max(1, sum(self._expected_sales().values()))
        return total_subsidy/estimate_total_sales

    def _compute_weight(self, code: str) -> float:
        current_price = self._get_current_price(code)

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
