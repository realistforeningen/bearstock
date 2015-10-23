
from math import exp

## params

BASE_PARAMETERS = {
    # expected sales parameters
    'ex_periods': 12,  # strictly positive number
    'ex_lookback': 12,  # strictly positive or None
    # adjustment parameters
    # - decrease
    'decrease_scaling': 0.75,
    'acqu_weight': 0,
    'prev_adjust_weight': 4,
    'time_since_sale_weight': 5,
    # - increase
    'increase_scaling': 0.50,
    'past_purchase_importance': 40.,
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

        # debug print
        print 'surplus: %.2f' % current_surplus

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

    def finalize(self):
        """Finalize the price calculations.

        Returns
        -------
        adjustments : dict
            Product code to adjustment dictionary.
            Missing entries means the adjustment is zero.
        """
        # correct for surplus
        self._deficit_correction()
        # collect adjustments
        adjustments = {}
        for code in self.products:
            if 'adjustment' in self.products[code]:
                adjustments[code] = self.products[code]['adjustment']

        # debug print
        for code in self.products:
            print 'Adjustment[%s] = %.2f (prev: %.2f)' % (
                code, self.products[code]['adjustment'], self.products[code]['prev_adj']
            )

        # return rounded adjustments
        return {code: round(adjustments[code]) for code in adjustments}

    def _compute_adjustment(self, code):
        product = self.products[code]
        params = product['p']
        decrease_scaling = params['decrease_scaling']
        ## read parameters
        w = (
            params['acqu_weight'],
            params['prev_adjust_weight'],
            params['time_since_sale_weight'],
        )
        weight_abs_sum = sum(map(abs, w))
        increase_scaling = params['increase_scaling']
        past_purchase_importance = params['past_purchase_importance']
        ## periods since last purchase
        delta_purchase = len(product['price_data'])
        for pid, data in enumerate(reversed(product['price_data'])):
            if data['sold_units'] > 0:
                delta_purchase = pid
                break
        ## compute decrease
        decrease_by = decrease_scaling*(
            w[0]*product['base_price'] +
            -w[1]*product['prev_adj'] +
            w[2]*delta_purchase
        )/(weight_abs_sum if weight_abs_sum != 0 else 1)
        decrease_by *= product['fraction_left']/max(1, product['expected'])
        ## compute increase
        increase_by = increase_scaling*(
            4. - 2./max(1, product['expected'])
        )*(
            4. - 2.*product['fraction_left']
        )*sum(
            data['sold_units']*exp(-(self.pid - pid)/past_purchase_importance)
            for pid, data in enumerate(product['price_data'])
        )

        return -decrease_by + increase_by

    def _deficit_correction(self):
        periods_left = max(1, self.p_left)
        correction = self.surplus
        # surplus
        surplus = {code: self.products[code]['expected']*(
            self.products[code]['base_price'] + self.products[code]['prev_adj']
        ) for code in self.products}
        sum_surplus = max(1, sum((surplus[code] for code in surplus)))
        # weight
        weights = {code: 1 - surplus[code]/sum_surplus for code in surplus}
        sum_weights = max(1, sum((weights[code] for code in weights)))
        weights = {code: weights[code]/sum_weights for code in weights}
        # adjust prices for surplus
        for code in self.products:
            self.products[code]['adjustment'] \
                -= (weights[code]*correction/max(1, self.products[code]['expected']))/periods_left

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
