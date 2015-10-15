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

@app.route('/products')
def products():
    products, prices = g.db.current_products_with_prices()
    print prices
    return jsonify(products=products, price_id=prices["_id"])

