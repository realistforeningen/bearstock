
from flask import Flask, render_template, g, jsonify, request, redirect
import json
import datetime
import time

from bearstock.database import Database, Buyer
from bearstock.statistics import get_top_bot

DATABASE_FILE = 'bear-app.db'

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.before_request
def before_request():
    g.db: Database = Database(DATABASE_FILE)
    g.db.connect()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/register')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '')
        icon = 'FOO'  # icon = request.form.get('icon', '')
        if len(name) > 0:
            buyer = g.db.insert_buyer(name=name, icon=icon)
            return render_template('signup.html', buyer_id=buyer.uid, name=buyer.name)

    return render_template('signup.html')

@app.route('/')
def buyers_list():
    buyers = g.db.get_all_buyers()
    return render_template('buyers/list.html', buyers=buyers)

@app.route('/buyers', methods=['POST'])
def buyers_create():
    buyer = Buyer(username=request.form['username'], scaling=1)
    buyer.insert_into(g.db)
    return redirect("/buyers/{}".format(buyer.uid))

@app.route('/buyers/<id>')
def buyers_edit(id):
    buyer = g.db.get_buyer(int(id))
    used_icons = g.db.get_all_icons()
    if buyer.icon in used_icons:
        used_icons.remove(buyer.icon)

    return render_template(
        'buyers/edit.html',
        buyer=buyer,
        emoji_picker=json.dumps({
            'currentIcon': buyer.icon,
            'usedIcons': used_icons
        })
    )

@app.route('/buyers/<id>', methods=['POST'])
def buyers_update(id):
    buyer = g.db.get_buyer(int(id))
    buyer.name = request.form['name']
    buyer.username = request.form['username']
    buyer.icon = request.form['icon']
    buyer.update_in_db()
    return redirect('/')

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    product = g.db.get_product(body['product_code'])
    buyer = g.db.get_buyer(body['buyer_id'])
    tick_no = g.db.get_tick_number()
    price = body['price']
    order = g.db.insert_order(
        buyer=buyer, product=product,
        relative_cost=(price-product.base_price),
        tick_no=tick_no)
    return jsonify(ok=True, order=order.as_dict(with_derived=True))

@app.route('/register.json')
def register_json():
    tick_no = g.db.get_tick_number()
    products = [p.as_dict(with_derived=True) for p in g.db.get_all_products() if not p.hidden]
    buyers = g.db.get_all_buyers()
    orders = g.db.get_latest_orders(count=30)
    return jsonify(
        tick_no=tick_no,
        products=products,
        buyers=[buyer.as_dict() for buyer in buyers ],
        orders=[order.as_dict(with_derived=True) for order in orders ],
        is_open=g.db.get_config_stock_running(),
        now=time.time(),
        quarantine=g.db.get_config_quarantine(),
    )

@app.route('/buyers.json')
def buyers_json():
    buyers = g.db.get_all_buyers()
    dicts = []
    for buyer in buyers:
        d = buyer.as_dict()
        d['sum_relative_cost'] = buyer.sum_relative_cost()
        dicts.append(d)

    return jsonify(buyers=dicts)
## Plots

@app.route('/stocks.json')
def stocks_json():
    products = g.db.get_all_products()
    stocks = []
    for product in products:
        time = product.timeline[0]
        prices = product.timeline[2]

        stocks.append({
            'key': product.code,
            'values': list({'x': x, 'y': y} for x, y in zip(time, prices))
        })
    return jsonify(stocks=stocks)

@app.route('/products.json')
def products_json():
    products = [p.as_dict(with_derived=True) for p in g.db.get_all_products() if not p.hidden]
    return jsonify(products=products)


@app.route('/stats')
def stats():
    return render_template('stats.html')


