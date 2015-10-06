from flask import Flask, render_template, g, jsonify
from flask.ext.assets import Environment, Bundle
from stock import Database

import npm
npm.register()

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
    return jsonify(products=g.db.current_products_with_prices())

