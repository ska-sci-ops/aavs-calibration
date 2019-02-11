from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='aavscalibrationdatabase',
    version='1.0',
    install_requires=[
        'mongoengine',
        'pytz',
        'python-dateutil'
    ]
)