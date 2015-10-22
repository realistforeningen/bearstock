
## params

BASE_PARAMETERS = {
    # expected sales parameters
    'ex_periods': 12,  # strictly positive number
    'ex_lookback': 12,  # strictly positive or None
    # adjustment parameters
    'decrease_percentage': 0.50,
    'ad_acqu_weight': 1,
    'ad_prev_adjust_weight': 10,
    'ad_past_sales_weight': 20,
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
            Length of a period. Unit is seconds.
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
        total_products = products_left + sum(
            tuple((data['sold_units'] for data in price_data))
        )
        self.products[code] = {
            'base_price': base_price,
            'prev_adj': (price_data[-1]['adjustment'] if price_data else 0),
            'fraction_left': (
                (float(products_left)/total_products)
                if total_products > 0 and products_left >= 0 else 1.0
            ),
            'price_data': price_data,
            'p': params,
        }
        self.products[code]['expected'] = self._expected_sales(code)
        self.products[code]['adjustment'] = self._compute_adjustment(code)
        print 'Adjustment[%s] = %.2f (prev: %.2f)' % (code, self.products[code]['adjustment'], self.products[code]['prev_adj'])

    def _compute_adjustment(self, code):
        product = self.products[code]
        params = product['p']
        p = params['decrease_percentage']
        ## read parameters
        w = (
            params['ad_acqu_weight'],
            params['ad_prev_adjust_weight'],
            params['ad_past_sales_weight'],
        )
        weight_abs_sum = sum(map(abs, w))
        ## periods since last purchase
        delta_purchase = len(product['price_data'])
        for pid, data in enumerate(reversed(product['price_data'])):
            if data['sold_units'] > 0:
                delta_purchase = pid
                break
        ## compute decrease
        decrease_by = p*(
            w[0]*product['base_price'] +
            -w[1]*product['prev_adj'] +
            w[2]*delta_purchase
        )/(weight_abs_sum if weight_abs_sum != 0 else 1)
        decrease_by *= product['fraction_left']/max(1, product['expected'])

        return -decrease_by

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
                adjustments[code] = round(self.products[code]['adjustment'])
        return adjustments

    def _expected_sales(self, code):
        """Compute expected sales for a product with code.
        """
        p = self.products[code]['p']
        lookback_to = 0 if 'ex_lookback' not in p or p['ex_lookback'] is None else \
            max(0, self.pid-p['ex_lookback'])
        ##
        transactions = 0
        for pid, purchase in enumerate(self.products[code]['price_data']):
            if pid >= lookback_to:
                transactions += (purchase['sold_units'] if purchase else 0)
        return transactions*p['ex_periods']/max(1, self.pid-lookback_to)
