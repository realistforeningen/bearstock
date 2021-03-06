import math
import sys
import random

from typing import (
    List,
    Dict,
    Tuple,
    Any,
)

from bearstock.database.product import Product


class PriceLogicBase:
    def __init__(
            self,
            current_surplus: float,
            current_period_id: int,
            period_duration: float,
            periods_left: int,
            kwargs: Dict[str, Any]=None
    ) -> None:
        """
        Parameters
        ----------

        current_surplus: The current surplus. Can be positive or negtative.
        period_id: Id of the current period. Should startcode at zero.
        period_duration: Length of a period. Unit is seconds.
        periods_left: Number of periods left.
        """

        # period data
        self.current_surplus = current_surplus
        self.current_period_id = current_period_id
        self.period_duration = period_duration
        self.periods_left = max(1, periods_left)

        self.products = {} # {code: Product}

    def add_product(self, product: Product, parameters=None) -> None:
        """
        Parameters
        ----------

        product:
        parameters: 
        """
        self.products[product.code] = product

    def finalize(self) -> Dict[str, float]:
        """Finalize the price calculations.

        Returns
        -------
        adjustments: Product code to adjustment dictionary. Missing entries means the
            adjustment is zero.
        """
        # TODO: get from params
        min_price = 20
        max_price = 200

        adjustments = self._adjust_deficit()    # Compute change in price
        for code in adjustments:
            product = self.products[code]

            if product.base_price + adjustments[code] < min_price:
                adjustments[code] = product.base_price - min_price

            if code in ['HRMW', 'HROK', 'KSWD', 'MHBB', 'WSHD', 'WSHW']:
                adjustments[code] = -15 + random.randint(-5, 5)

            if random.random() < 0.2:
                adjustments[code] += 10
            elif random.random() < 0.5:
                adjustments[code] -= 15

        return adjustments

    def _adjust_deficit(self) -> Dict[str, float]:
        """Correct the adjustments to satisfy budget constriants."""
        target_deficit = self._target_deficit_this_tick()
        adjustments = self._compute_adjustments() # Price adjustments
        expected_sales = self._expected_sales(adjustments) # Per beer species
        total_expected_sales = self._total_estimated_sales()

        deficits = {}   # Compute current deficit this tick per beer species
        for code in self.products:
            deficits[code] = self.products[code].base_price + adjustments[code]
            deficits[code] *= expected_sales[code]

        # Avoid division by zero for first tick
        total_deficits = sum(deficits.values())
        if total_deficits == 0:
            total_deficits = 1

        correction_weights = {      # Scale price adjustments by deficit target
            code: 1 - deficits[code]/total_deficits for code in adjustments
        }

        for code in adjustments:    # Scale the price adjustments
            adjustments[code] *= correction_weights[code]
        return adjustments

    def _expected_sales(self, adjustments: Dict[str, float]=None) -> Dict[str, float]:
        """Return estimated sales for each beer species."""
        raise NotImplementedError

    def _total_estimated_sales(self) -> float:
        """Return estimated total sales."""
        raise NotImplementedError

    def _target_deficit_this_tick(self) -> float:
        """Return target deficit this tick."""
        raise NotImplementedError

    def _compute_adjustments(self) -> Dict[str, float]:
        """Return dict with price adjustments."""
        raise NotImplementedError


class PriceLogic(PriceLogicBase):
    def _target_deficit_this_tick(self) -> float:
        total_subsidy = self.current_surplus/max(1, self.periods_left)
        estimate_total_sales = max(1, sum(self._expected_sales().values()))
        return total_subsidy/estimate_total_sales

    def _compute_weight(self, code: str, num_lookback_ticks: int=5) -> float:
        """Compute weights based on number of beer sold."""

        product = self.products[code]
        current_price = product.current_price
        units_sold = sum(product.timeline.sales[-30:])

        base_adjustment = min(max(1, current_price - product.base_price), 10)
        #base_adjustment = 2

        if units_sold == 0:
            return  -3*base_adjustment
        if units_sold == 1:
            return  -2*base_adjustment
        if units_sold <= 3:
            return -1*base_adjustment
        if units_sold > 3:
            return 5*base_adjustment
        if units_sold > 6:
            return 7*base_adjustment

        return 10*base_adjustment

    def _compute_adjustments(self) -> Dict[str, float]:
        """This is where the magic happens."""
        weights = {code: self._compute_weight(code) for code in self.products}
        total_weight = max(1, sum(weights.values()))

        # TODO: Is this a good idea?
        # for code in self.products:
        #     weights[code] /= total_weight
        return weights

    def _total_estimated_sales(self) -> float:
        """Compute expected sales for a product with code."""
        alpha = 1e-1    # parameter for time weights
        
        expected_sales = {}
        for code in self.products:
            product = self.products[code]
            sales = product.timeline.sales

            weights = [
                math.exp(-alpha*(self.current_period_id - t)) for t in range(len(sales))
            ]

            # Compute weights average
            expected_sales[code] = sum([w*s for w, s in zip(weights, sales)])/sum(weights)

        foo = max(1, sum(expected_sales.values()))
        return foo

    def _expected_sales(self, prices: Dict[str, float]=None) -> Dict[str, float]:
        """Estimate the sales for each species."""
        beta = 1e-1     # slope parameter
        gamma = 1.0     # scale parameter

        sales = {}
        for code in self.products:
            product = self.products[code]
            current_price = product.current_price
            base_price = product.base_price

            if prices is not None:
                current_price += prices[code]

            sales[code] = gamma*math.exp(-beta*(current_price - base_price))

        total_sales = self._total_estimated_sales()

        # Scale so they sum to 1 using Softmax
        maximum = max(sales.values())
        sales[code] = math.exp(sales[code] - maximum)

        scale = sum(sales.values())
        for code in sales:
            sales[code] /= scale
            sales[code] *= total_sales      # Scale to match estimated total sales
        return sales
