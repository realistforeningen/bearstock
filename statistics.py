# coding: utf-8

def get_top_bot(count):
    """Get ``count`` top and bottom traders.

    Parameters
    ----------
    count : int
        Number of top/bottom traders to get.

    Returns
    -------
    topbot : dict
        A dict containing three keys: ``count``, ``top``, and ``bottom``.

         * ``count`` is the number of top and bottom traders.
         * ``top`` and ``bottom`` a tuple containing ``count`` dicts, each
           containing the keys:
            * ``id``: Trader ID.
            * ``turnover``: Total turnover for the trader.
            * ``profit``: Profit relative to base price of products bought.
    """
    pass
