from mongoengine import connect

DB_NAME = 'aavs'    # change name to create another database
HOST = 'localhost'  # insert IP address or url here
PORT = 27017        # mongodb standard port


def connect_to_db(db_name='', host='', port=''):
    """ connect to standard db, if not otherwise specified """
    if not db_name:
        db_name = DB_NAME
    if not host:
        host = HOST
    if not port:
        port = PORT
    return connect(db_name, host=host, port=port)

