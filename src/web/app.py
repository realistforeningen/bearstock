from flask import Flask, render_template, g, jsonify, request
from bearstock.stock import Database
from bearstock.statistics import get_top_bot

app = Flask(__name__)
app.config['DEBUG'] = True

@app.before_request
def before_request():
    g.db = Database.default()

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
                buyer_id = g.db.insert_buyer(name)

            return render_template('signup.html', buyer_id=buyer_id, name=name)

    return render_template('signup.html')

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/products')
def products():
    products, price_id = g.db.current_products_with_prices(round_price=True)
    return jsonify(products=products, price_id=price_id)

@app.route('/prices')
def prices():
    codes = request.args.getlist('code')
    prices = g.db.prices_for_product(codes, round_price=True)
    return jsonify(prices)

@app.route('/stats/buyers')
def stats_buyers():
    stats = get_top_bot(5, g.db)
    return jsonify(buyers=stats)

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    with g.db.conn:
        for order in body["orders"]:
            g.db.insert(
                "orders",
                buyer_id=body["buyer_id"],
                product_code=order["code"],
                price_id=order["price_id"],
                absolute_cost=order['absolute_cost'],
                relative_cost=order['relative_cost']
            )
    return jsonify(ok=True)

@app.route('/buyer')
def buyer():
    buyer_id = int(request.args.get('id', -1))
    buyer = g.db.find_buyer(buyer_id)
    return jsonify(buyer=buyer)
