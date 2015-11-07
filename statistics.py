# coding: utf-8

from stock import Database

def get_top_bot(count, db=None):
    """Get ``count`` top and bottom traders.

    Parameters
    ----------
    count : int
        Number of top/bottom traders to get.

    Returns
    -------
    top_bot : dict
        A dict containing three keys: ``count``, ``top``, and ``bottom``.

         * ``count`` is the number of top and bottom traders.
         * ``top`` and ``bottom`` a tuple containing ``count`` dicts, each
           containing the keys:
            * ``id``: Trader ID.
            * ``turnover``: Total turnover for the trader.
            * ``profit``: Profit relative to base price of products bought.

        If there are fewer traders than ``count``, the lists are shorter than
        ``count``.
    """
    # get data from DB
    if db is None:
        db = Database.default()

    buyers = db.buyer_dict()

    orders = db.read_all_orders()
    # parse orders
    traders = {}  # list of traders
    for order in orders:
        # Order fields
        #   oid       : order id
        #   bid       : buyer id
        #   code      : product code
        #   pid       : price id
        #   rel_cost  : relative cost from product base price
        #   abs_cost  : absolut cost the buyer paid
        #   timestamp : order timestamp
        oid, bid, code, pid, rel_cost, abs_cost, timestamp = order
        # add data
        if bid not in traders:
            traders[bid] = {
                'id': bid,
                'name': buyers[bid],
                'turnover': 0,
                'profit': 0,
            }
        traders[bid]['turnover'] += abs_cost
        traders[bid]['profit'] += -rel_cost
    # construct the list
    traders = sorted(traders.values(), key=(lambda trader: trader['profit']), reverse=True)
    # data!
    return {
        'count': min(count, len(traders)),
        'top': tuple(traders[0:count]),
        'bottom': tuple(traders[-count:][::-1]),
    }

if __name__ == '__main__':
    from pprint import pprint as pp
    pp(get_top_bot(5))
