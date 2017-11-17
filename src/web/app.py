
from flask import Flask, render_template, g, jsonify, request

from bearstock.database import Database
from bearstock.statistics import get_top_bot

DATABASE_FILE = 'bear-app.db'

app = Flask(__name__)
app.config['DEBUG'] = True

@app.before_request
def before_request():
    g.db: Database = Database(DATABASE_FILE)
    g.db.connect()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
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

@app.route('/products')
def products():
    tick_no = g.db.get_tick_number()
    products = [p.as_dict(with_derived=True) for p in g.db.get_all_products()]
    return jsonify(products=products, tick_no=tick_no)

@app.route('/buyers')
def buyers():
    buyers = g.db.get_all_buyers()
    return jsonify(buyers=[ buyer.as_dict() for buyer in buyers ])

@app.route('/orders')
def orders_list():
    orders = g.db.get_latest_orders(count=10)
    return jsonify(orders=[  order.as_dict(with_derived=True) for order in orders ])

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    product = g.db.get_product(body['product_code'])
    buyer = g.db.get_buyer(body['buyer_id'])
    price = body['price']
    g.db.insert_order(buyer=buyer, product=product, relative_cost=(price-product.base_price))
    return jsonify(ok=True)

