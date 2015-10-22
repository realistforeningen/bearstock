
## params

BASE_PARAMETERS = {
    # expected sales parameters
    'ex_periods': 12,  # strictly positive number
    'ex_lookback': 12,  # strictly positive or None
}

## logic

class PriceLogic:
    def __init__(self, current_surplus, period_id, period_duration, periods_left):
        """
        Parameters
        ----------
        current_surplus : float
            The current surplus. Can be positive or negative.
        period_id : int
            Id of the current period. Should start at zero.
        period_duration : float
            Length of a period.
        periods_left : int
            Number of periods left.
        """
        self.surplus = current_surplus
        # period data
        self.pid = period_id
        self.p_duration = period_duration
        self.p_left = periods_left
        # product data
        self.products = {}

    def add_product(self, code, base_price, price_data, products_left, params=BASE_PARAMETERS):
        """
        Parameters
        ----------
        code : str
            Product code.
        base_price : float
            Product base price.
        price_data : list
            List of dictionaries each containing the keys 'sold_units' and 'adjustment'.
            One element per period.
        products_left : int
            Number of products left.
        params : dict, optional
            Parameters.
        """
        self.products[code] = {
            'base_price': base_price,
            'price_data': price_data,
            'p': params,
        }
        self.products[code]['expected'] = self._expected_sales(code)
        self.products[code]['adjustment'] = self._compute_adjustment(code)

    def _compute_adjustment(self, code):
        return 0  # TODO

    def finalize(self):
        """Finalize the price calculations.

        Returns
        -------
        adjustments : dict
            Product code to adjustment dictionary.
            Missing entries means the adjustment is zero.
        """
        adjustments = {}
        for code in self.products:
            if 'adjustment' in self.products[code]:
                adjustments[code] = self.products[code]['adjustment']
        return adjustments

    def _expected_sales(self, code):
        """Compute expected sales for a product with code.
        """
        p = self.products[code]['p']
        lookback_to = 0 if 'ex_lookback' not in p or p['ex_lookback'] is None else \
            max(0, self.pid-p['ex_lookback'])
        ##
        transactions = 0
        for p, purchase in enumerate(self.products['price_data']):
            if p >= lookback_to:
                transactions += (purchase['sold_unis'] if purchase else 0)
        return transactions*p['ex_periods']/(self.pid-lookback_to)
