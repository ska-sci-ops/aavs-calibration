from db import Fit, Channel, Coefficient
from connect import connect_to_db

connect_to_db()


def purge():
    """ drops all collections except antenna"""
    Fit.drop_collection()
    Channel.drop_collection()
    Coefficient.drop_collection()


if __name__ == '__main__':
    purge()
