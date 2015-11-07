# coding: utf-8

from math import exp

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
        self.total_products_sold = 0
        self.products = {}
        self.brewery_data = {}
        self.type_data = {}

        # debug print
        print 'periods left: %d' % periods_left
        print 'surplus: %.2f' % current_surplus

    def add_product(
        self, code, brewery, base_price, products_left, prod_type,
        price_data, params=None
    ):
        """
        Parameters
        ----------
        code : str
            Product code.
        brewery : string
            Name of the brewery.
        base_price : float
            Product base price.
        products_left : int
            Number of products left.
        prod_type : string
            Product type.
        price_data : list
            List of dictionaries each containing the keys 'sold_units' and 'adjustment'.
            One element per period.
        params : Params, optional
            Parameters.
        """
        # count products
        sold_products = sum(
            ((data['sold_units'] if 'sold_units' in data else 0) for data in price_data)
        )
        self.total_products_sold += sold_products  # count total products sold
        total_products = products_left + sold_products  # compute products left
        # store products sold per brewery
        if brewery.lower() not in self.brewery_data:
            self.brewery_data[brewery.lower()] = 0
        self.brewery_data[brewery.lower()] += sold_products
        # store products sold per type
        if prod_type.lower() not in self.type_data:
            self.type_data[prod_type.lower()] = 0
        self.type_data[prod_type.lower()] += sold_products
        # add product
        self.products[code] = {
            'brewery': brewery.lower(),
            'type': prod_type.lower(),
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
        self.products[code]['expected'] = self._expected_sales(code)
        self.products[code]['adjustments'] = list(self._compute_adjustment(code))

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
            prod = self.products[code]
            if 'adjustments' in prod:
                # read popularities
                popularity, type_popularity, brewery_popularity = (
                    prod['popularity'],
                    self.type_data[prod['type']]/max(1., float(self.total_products_sold)),
                    self.brewery_data[prod['brewery']]/max(1., float(self.total_products_sold)),
                )
                avg_pop = (popularity + 3*type_popularity + 2*brewery_popularity)/6.
                # compute final adjustment
                increase, decrease, deficit_correction = prod['adjustments']
                # adjustment = prod['prev_abs_adj'] + (1 + avg_pop)*increase \
                #     + (1 - avg_pop)*decrease + deficit_correction
                adjustment = prod['prev_abs_adj'] + increase + decrease + deficit_correction
                # make sure we don't sell lower than the min price
                if prod['base_price']+adjustment > prod['p'].min_price:
                    adjustments[code] = adjustment
                else:
                    adjustments[code] = prod['prev_abs_adj'] + (
                        prod['p'].min_price-(prod['base_price']+prod['prev_abs_adj'])
                    )

        # debug print
        for code in adjustments:
            print 'Adjustment[%s] = %.2f (prev: %.2f)' % (
                code, adjustments[code], self.products[code]['prev_abs_adj']
            )

        # return rounded adjustments
        return {code: (adjustments[code]) for code in adjustments}

    def _compute_adjustment(self, code):
        product = self.products[code]
        params = product['p']
        ## read parameters
        w = (
            params.acqu_weight,
            params.prev_abs_adjust_weight,
            params.prev_rel_adjust_weight,
            params.time_since_sale_weight,
        )
        weight_abs_sum = float(sum(map(abs, w)))
        past_purchase_importance = params.past_purchase_importance
        ## periods since last purchase
        delta_purchase = len(product['price_data'])
        for pid, data in enumerate(reversed(product['price_data'])):
            if data['sold_units'] > 0:
                delta_purchase = pid
                break
        ## compute decrease
        decrease_by = params.decrease_scaling*(
            w[0]*product['base_price'] +
            -w[1]*product['prev_abs_adj'] +
            -w[2]*product['prev_rel_adj'] +
            w[3]*delta_purchase**params.time_since_sale_power
        )/(weight_abs_sum if weight_abs_sum != 0 else 1)
        decrease_by *= product['fraction_left']/(product['expected'] + 1)
        ## compute increase
        increase_by = params.increase_scaling*(
            4. - 2./max(1, product['expected'])
        )*(
            4. - 2.*product['fraction_left']
        )*sum(
            data['sold_units']*exp(-(self.pid - pid)/past_purchase_importance)
            for pid, data in enumerate(product['price_data'])
        )

        print increase_by, -decrease_by

        return increase_by, -decrease_by

    def _deficit_correction(self):
        periods_left = max(1, self.p_left)
        correction = self.surplus
        # surplus
        surplus = {code: self.products[code]['expected']*(
            self.products[code]['base_price'] + self.products[code]['prev_abs_adj']
        ) for code in self.products}
        sum_surplus = float(max(1, sum((surplus[code] for code in surplus))))
        # weight
        weights = {code: 1 - surplus[code]/sum_surplus for code in surplus}
        sum_weights = float(max(1, sum((weights[code] for code in weights))))
        weights = {code: weights[code]/sum_weights for code in weights}
        # adjust prices for surplus
        for code in self.products:
            self.products[code]['adjustments'].append(
                - (weights[code]*correction/max(1, self.products[code]['expected']))/periods_left
            )

    def _expected_sales(self, code):
        """Compute expected sales for a product with code.
        """
        params = self.products[code]['p']
        lookback_to = 0 if params.ex_lookback < 0 else \
            max(0, self.pid - params.ex_lookback)
        ##
        transactions = 0
        for pid, purchase in enumerate(self.products[code]['price_data']):
            if pid >= lookback_to:
                transactions += (purchase['sold_units'] if purchase else 0)
        return transactions*params.ex_periods/max(1, self.pid-lookback_to)

class Params(object):
    class SingleParam(object):
        def __init__(
            self, name=None,
            valid_types=None, cast_to=None,
            pos=False, neg=False, non_zero=False
        ):
            self.name = name
            # checks
            self.valid_types, self.cast_to = valid_types, cast_to
            self.pos, self.neg, self.non_zero = pos, neg, non_zero

        def __get__(self, instance, owner):
            if instance is not None and hasattr(instance, self.name):
                return getattr(instance, self.name, getattr(owner, self.name, None))
            return getattr(owner, self.name, None)

        def __set__(self, instance, value):
            # type check
            if self.valid_types is not None and isinstance(self.valid_types, (list, tuple)) \
                    and not isinstance(value, self.valid_types):
                raise ValueError("Value is not of a valid type.")
            # number checks
            if self.non_zero and value == 0:
                raise ValueError("Value is not non-zero.")
            if self.pos and value < 0:
                raise ValueError("Value is not positive.")
            if self.neg and value > 0:
                raise ValueError("Value is not negative.")
            # assign
            if self.cast_to is not None:
                setattr(instance, self.name, self.cast_to(value))
            else:
                setattr(instance, self.name, value)

        def __delete__(self, instance):
            if instance is not Params and hasattr(instance, self.name):
                delattr(instance, self.name)

    @classmethod
    def set_default_from_dict(cls, defaults):
        """Set default values from a dictionary.

        Parameters
        ----------
        defaults : dict
            A dictionary with parameter names to default value. Valid keys are:

             * 'ex_periods' - Number of periods to project forward when computing expected sale.
               Must be a strictly positive integer.
             * 'ex_lookback' - Number of periods to look back when computing expected sale.
               A negative number is lookback to start.
             * 'decrease_scaling' - Scaling for price decrease. Should be a float.
             * 'acqu_weight' - Realtive weight for 'base price' or 'aquisition price') in price
               adjustments. Should be an int.
             * 'prev_abs_adjust_weight' - Realtive weight for 'previous absolute price adjustment'
               in price adjustments. Should be an int.
             * 'prev_rel_adjust_weight' - Realtive weight for 'previous relative price adjustment'
               in price adjustments. Should be an int.
             * 'time_since_sale_weight' - Relative weight of 'time since last sale' in price
               calculations. Should be an int.
             * 'increase_scaling' - Scaling for price increase. Should be a float.
             * 'past_purchase_importance' - Importance of past orders. A higher value makes
               past sales count more/longer. Must be non-zero.
             * 'min_price' - Minimum price. Sould be positive.
        """
        for key in defaults:
            if hasattr(cls, key):
                setattr(cls, key, defaults[key])

    def __init__(self, params=None):
        """Initialize a new parameter object.

        Parameters
        ----------
        params : dict or None
            Dictionary with parameters. Passed along to `set_from_dict`.
        """
        if params is not None and isinstance(params, (dict, )):
            self.set_from_dict(params)

    def set_from_dict(self, params):
        """Set values from a dictionary.

        Parameters
        ----------
        params : dict
            A dictionary with parameter names to default value. Valid keys are:

             * 'ex_periods' - Number of periods to project forward when computing expected sale.
               Must be a strictly positive integer.
             * 'ex_lookback' - Number of periods to look back when computing expected sale.
               A negative number is lookback to start.
             * 'decrease_scaling' - Scaling for price decrease. Should be a float.
             * 'acqu_weight' - Realtive weight for 'base price' or 'aquisition price') in price
               adjustments. Should be an int.
             * 'prev_abs_adjust_weight' - Realtive weight for 'previous absolute price adjustment'
               in price adjustments. Should be an int.
             * 'prev_rel_adjust_weight' - Realtive weight for 'previous relative price adjustment'
               in price adjustments. Should be an int.
             * 'time_since_sale_weight' - Relative weight of 'time since last sale' in price
               calculations. Should be an int.
             * 'increase_scaling' - Scaling for price increase. Should be a float.
             * 'past_purchase_importance' - Importance of past orders. A higher value makes
               past sales count more/longer. Must be non-zero.
             * 'min_price' - Minimum price. Sould be positive.
        """
        for key in params:
            if hasattr(self, key):
                setattr(self, key, params[key])

    ## expected sales parameters
    ## -------------------------

    _ex_periods = 12  # strictly positive number
    ex_periods = SingleParam(name='_ex_periods', non_zero=True, pos=True, cast_to=int)

    _ex_lookback = 12  # if negative looks back to start
    ex_lookback = SingleParam(name='_ex_lookback', cast_to=int)

    ## adjustment parameters
    ## ---------------------

    ## - decrease

    _decrease_scaling = 0.05
    decrease_scaling = SingleParam(name='_decrease_scaling', pos=True, cast_to=float)

    _acqu_weight = 1
    acqu_weight = SingleParam(name='_acqu_weight', cast_to=int)

    _prev_abs_adjust_weight = 2
    prev_abs_adjust_weight = SingleParam(name='_prev_abs_adjust_weight', cast_to=int)

    _prev_rel_adjust_weight = 4
    prev_rel_adjust_weight = SingleParam(name='_prev_rel_adjust_weight', cast_to=int)

    _time_since_sale_weight = 8
    time_since_sale_weight = SingleParam(name='_time_since_sale_weight', cast_to=int)

    _time_since_sale_power = 1.05
    time_since_sale_power = SingleParam(name='_time_since_sale_power', pos=True, cast_to=float)

    # - increase

    _increase_scaling = 0.40
    increase_scaling = SingleParam(name='_increase_scaling', pos=True, cast_to=float)

    _past_purchase_importance = 0.25
    past_purchase_importance = SingleParam(
        name='_past_purchase_importance', non_zero=True, pos=True, cast_to=float)

    ## price parameters
    ## ----------------

    _min_price = 5.
    min_price = SingleParam(name='_min_price', pos=True, cast_to=float)
