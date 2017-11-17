import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

from bearstock.price_logic_table import PriceLogicBasic

from bearstock.products import PRODUCTS


def buyer(N=30):
    df = pd.read_csv("orders-dump.csv")
    
    products, counts = np.unique(
        df["Product"].values,
        return_counts=True
    )
    beer_df = pd.concat((
        df[df["Product"] == beer] for beer in products[np.argsort(counts)[-N:]]
    ))
    
    for pid in df["Price Id"].drop_duplicates():
        buy_idx = beer_df["Price Id"] == pid
        yield list(filter(lambda x: x in PRODUCTS, beer_df["Product"][buy_idx].values))


def simulate():
    surplus = 5000
    product_dict = PRODUCTS

    for i, buy_list in enumerate(buyer()):
        pl = PriceLogicBasic(
            current_surplus=surplus,
            current_period_id=i,
            period_duration=1,
            periods_left=5000 - i
        )

        for product in product_dict:
            args = PRODUCTS[product]
            pl.add_product(
                code=args["code"],
                brewery=args["brewery"],
                base_price=args["base_price"],
                products_left=100,
                product_type="foo",
                price_data=args["price_data"]
            )

        update_dict = pl.finalize()

        for beer in product_dict:
            product_dict[beer]["price_data"].append(
                {"sold_units": 0, "adjustment": update_dict[beer]}
            )
        
        for beer in buy_list:
            product_dict[beer]["price_data"][-1]["sold_units"] += 1
        surplus += compute_subsidy(product_dict)
        print(surplus)

    return product_dict


def compute_subsidy(data):
    subsidy = 0
    for beer in data:
        subsidy += data[beer]["price_data"][-1]["adjustment"]
    return subsidy


def plotter():
    data = simulate()

    for beer in data:
        foo = list(map(lambda x: x["adjustment"], data[beer]["price_data"]))
        data[beer]["price"] = data[beer]["base_price"] + np.cumsum(foo)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    for beer in data:
        ax.plot(data[beer]["price"])

    plt.show()
    input()

if __name__ == "__main__":
    plotter()
