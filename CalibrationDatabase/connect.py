from mongoengine import connect

DB_NAME = 'aavs'
HOST = 'localhost'  # insert IP address or url here
PORT = 27017  # mongodb standard port


def connect_to_db():
    connect(DB_NAME, host=HOST, port=PORT)

