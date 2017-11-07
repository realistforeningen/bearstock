
# BearStock

Everything related to the BearStock. Work very much in progress.

## Getting started

Set up an virtualenv and install dependencies:

```
$ virtualenv env -p python3.6

$ source env/bin/activate
$ python setup.py develop  # to symlink sources
```

JavaScript libraries (used on the client-side) is installed through NPM:

```
$ yarn
```

Set up the database:

```
$ bear_setup bearstock-products-initial.tsv
```
Substitute `<products-file>` for a valid csv products file, eq. [`bearstock-products.csv`](bearstock-products.csv).

Build the JavaScript:

```
$ npm run build
```

Run the web server + exchange:

```
$ uwsgi -H env --http 0.0.0.0:5000 --module web.app:app --mule=bearstock.stock
```

Visit <http://localhost:5000/>.

