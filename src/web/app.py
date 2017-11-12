
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
        if len(name) > 0:
            with g.db.conn:
                buyer = g.db.insert_buyer(name)

            return render_template('signup.html', buyer_id=buyer.uid, name=buyer.name)

    return render_template('signup.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/products')
def products():
    products, price_id = g.db.current_products_with_prices(round_price=True)
    return jsonify(products=products, price_id=price_id)

@app.route('/buyers')
def buyers():
    buyers = g.db.buyers()
    return jsonify(buyers=buyers)

@app.route('/prices')
def prices():
    codes = request.args.getlist('code')
    prices = g.db.prices_for_product(codes, round_price=True)
    return jsonify(prices)

@app.route('/stats/buyers')
def stats_buyers():
    stats = get_top_bot(5, g.db)
    return jsonify(buyers=stats)

@app.route('/orders')
def orders_list():
    orders = g.db.latest_orders()
    return jsonify(orders=orders)

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    product = body["product"]
    with g.db.conn:
        g.db.insert(
            "orders",
            buyer_id=body["buyer_id"],
            product_code=product["code"],
            price_id=product["price_id"],
            absolute_cost=product['absolute_cost'],
            relative_cost=product['relative_cost']
        )
    return jsonify(ok=True)

@app.route('/buyer')
def buyer():
    buyer_id = int(request.args.get('id', -1))
    buyer = g.db.get_buyer(buyer_id)
    return jsonify(buyer=buyer.as_dict())
