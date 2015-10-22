from flask import Flask, render_template, g, jsonify, request
from stock import Database

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

@app.route('/stats')
def stats():
    return render_template('stats.html')

@app.route('/products')
def products():
    products = g.db.current_products_with_prices()
    return jsonify(products=products)

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    with g.db.conn:
        for order in body["orders"]:
            g.db.insert("orders",
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

