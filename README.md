# BearStock

Everything related to the BearStock. Work very much in progress.

## Getting started

Set up an virtualenv and install dependencies:

```
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

JavaScript libraries (used on the client-side) is installed through NPM:

```
$ npm install
```

Set up the database:

```
$ bin/setup
```

Run the server:

```
$ bin/server
```

Visit <http://localhost:5000/>.

## Structure

```
stock.py          -  Database and stock logic
web/app.py        -  Flask app responsible for the web front end
web/js/main.imba  -  User interface for buying beers
web/css           -  Styling

schema.sql        -  Schema for the database
products.py       -  Products for sale. Used by bin/setup.
```
