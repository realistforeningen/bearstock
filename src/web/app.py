
from flask import Flask, render_template, g, jsonify, request, redirect
import json

from bearstock.database import Database, Buyer
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
    buyer = Buyer(name=request.form['name'], scaling=1)
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
    buyer.icon = request.form['icon']
    buyer.update_in_db()
    return redirect('/')

@app.route('/orders', methods=['POST'])
def orders_create():
    body = request.get_json()
    product = g.db.get_product(body['product_code'])
    buyer = g.db.get_buyer(body['buyer_id'])
    price = body['price']
    g.db.insert_order(buyer=buyer, product=product, relative_cost=(price-product.base_price))
    return jsonify(ok=True)

@app.route('/register.json')
def register_json():
    tick_no = g.db.get_tick_number()
    products = [p.as_dict(with_derived=True) for p in g.db.get_all_products()]
    buyers = g.db.get_all_buyers()
    orders = g.db.get_latest_orders(count=10)
    return jsonify(
        tick_no=tick_no,
        products=products,
        buyers=[buyer.as_dict() for buyer in buyers ],
        orders=[order.as_dict(with_derived=True) for order in orders ],
    )

## Plots


from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import Legend
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.layouts import layout
from bokeh.palettes import Category20

@app.route('/stats')
def stats():
    fig = figure(title="Stocks")

    fig.xaxis.axis_label = 'Time'
    fig.yaxis.axis_label = 'Price (NOK)'
    fig.toolbar.logo = None
    fig.toolbar_location = None

    products = g.db.get_all_products()

    legends = []

    palette = Category20[20]

    for idx, p in enumerate(products):
        l = fig.line(p.timeline[0], p.timeline[2], line_width=1, line_color=palette[idx % len(palette)])
        legends.append((p.code, [l]))

    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    fig.add_layout(Legend(items=legends), 'right')


    script, div = components(fig)

    return render_template(
        'stats.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
    )

