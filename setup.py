
from setuptools import setup, find_packages

setup(
    name='Bearstock',

    package_dir={'': 'src'},
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'bear_server = bearstock.main.server:main',
            'bear_settlement = bearstock.main.settlement:main',
            'bear_setup = bearstock.main.setup:main',
            'bear_start-stock = bearstock.main.start_stock:main'
        ]
    },

    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'Flask',
        'uwsgi',
    ],
    tests_require=[
        'pytest == 2.8.2',
    ]

)
