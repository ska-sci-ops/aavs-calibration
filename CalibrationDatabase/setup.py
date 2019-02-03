from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='aavscalibrationdatabase',
    version='0.1',
    install_requires=[
        'mongoengine',
        'pytz',
        'python-dateutil'
    ]
)