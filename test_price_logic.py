
from price_logic import PriceLogic

def test_expected_sales_zero_div_at_pid_0():
    pid = 0
    pl = PriceLogic(0, pid, 5*60, 10)

    code = "TEST"
    base_price = 10
    price_data = []
    products_left = 10

    try:
        pl.add_product(code, base_price, price_data, products_left)
    except ZeroDivisionError:
        assert False, "Lookback at period zero fails"
