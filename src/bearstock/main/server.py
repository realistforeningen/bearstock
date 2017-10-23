
from web.app import app
from bearstock.stock import Exchange
import subprocess

def main(argv=None):
    Exchange.run_in_thread()
    subprocess.call(
        ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "web/app.py", "--callable", "app"]
    )

