import math
import sys

from typing import (
    List,
    Dict,
    Tuple,
    Any,
)


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

        self.current_surplus = current_surplus

        # period data
        self.current_period_id = current_period_id
        self.period_duration = period_duration
        self.periods_left = max(1, periods_left)

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
        min_price = 20
        max_price = 200

        adjustments = self._adjust_deficit()    # Compute change in price
        for code in adjustments:
            if self._get_current_price(code) + adjustments[code] < min_price:
                adjustments[code] = 0
            elif self._get_current_price(code) + adjustments[code] > max_price:
                adjustments[code] = 0
        return adjustments

    def _adjust_deficit(self) -> Dict[str, float]:
        """Correct the adjustments to satisfy budget constriants."""
        target_deficit = self._target_deficit_this_tick()
        adjustments = self._compute_adjustments() # Price adjustments
        expected_sales = self._expected_sales(adjustments) # Per beer species
        total_expected_sales = max(1, sum(expected_sales.values())) # In total 

        deficits = {}   # Compute current deficit this tick per beer species
        for code in self.products:
            deficits[code] = self._get_current_price(code) + adjustments[code]
            deficits[code] *= expected_sales[code]

        total_deficits = sum(deficits.values())
        if total_deficits == 0:     # Avoid division by zero for first tick
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

    def _target_deficit_this_tick(self) -> float:
        """Return target deficit this tick."""
        raise NotImplementedError

    def _compute_adjustments(self) -> Dict[str, float]:
        """Return dict with price adjustments."""
        raise NotImplementedError


class PriceLogicBasic(PriceLogicBase):
    def _get_current_price(self, code: str) -> float:
        # TODO: replace by database lookup
        product = self.products[code]
        base_price = product["base_price"]
        adjustments = sum(map(lambda x: x["adjustment"], product["price_data"]))
        return base_price + adjustments

    def _target_deficit_this_tick(self) -> float:
        total_subsidy = self.current_surplus/max(1, self.periods_left)
        estimate_total_sales = max(1, sum(self._expected_sales().values()))
        return total_subsidy/estimate_total_sales

    def _compute_weight(self, code: str, num_lookback_ticks: int=10) -> float:
        """Compute weights based on number of beer sold."""
        current_price = self._get_current_price(code)

        units_sold = self._total_sold(num_lookback_ticks)[code]
        product = self.products[code]
        base_adjustment = max(1, self._get_current_price(code) - product["base_price"])

        if units_sold == 0:
            return  -4*base_adjustment
        if units_sold <= 5:
            return -2*base_adjustment
        if units_sold > 5:
            return 2*base_adjustment
        if units_sold > 10:
            return 5*base_adjustment

    def _compute_adjustments(self) -> Dict[str, float]:
        """This is where the magic happens."""
        weights = {code: self._compute_weight(code) for code in self.products}
        total_weight = max(1, sum(weights.values()))

        for code in self.products:
            weights[code] /= total_weight
        return weights

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

    def _estimate_total_sales(self) -> float:
        """Compute expected sales for a product with code."""
        alpha = 1e-1    # parameter for time weights
        
        expected_sales = {}
        for code in self.products:
            # List of time points
            times = list(range(len(self.products[code]["price_data"])))

            # List of past sales
            sales = [self.products[code]["price_data"][t]["sold_units"] for t in times]

            # List of weights
            # TODO: remove +1 if 0 indexed tick numbers ???
            weights = [math.exp(-alpha*(self.current_period_id - t + 1)) for t in times]

            # Compute weights average
            expected_sales[code] = sum([w*s for w, s in zip(weights, sales)])/sum(weights)
        return max(1, sum(expected_sales.values()))

    def _expected_sales(self, prices: Dict[str, float]=None) -> Dict[str, float]:
        """Estimate the sales for each species."""
        beta = 1e-1     # slope parameter
        gamma = 1.0     # scale parameter

        sales = {}
        for code in self.products:
            current_price = self._get_current_price(code)
            if prices is not None:
                current_price += prices[code]
            base_price = self.products[code]["base_price"]
            sales[code] = gamma*math.exp(-beta*(current_price - base_price))

        total_sales = self._estimate_total_sales()

        # Scale so they sum to 1 using Softmax
        maximum = max(sales.values())
        sales[code] = math.exp(sales[code] - maximum)

        scale = sum(sales.values())
        for code in sales:
            sales[code] /= scale
            sales[code] *= total_sales      # Scale to match estimated total sales
        return sales
