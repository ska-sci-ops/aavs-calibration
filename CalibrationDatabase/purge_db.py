from db import Fit, Channel, Coefficient, connect
db = connect('aavs', host='localhost', port=27017)


def main():
    Fit.drop_collection()
    Channel.drop_collection()
    Coefficient.drop_collection()


if __name__ == '__main__':
    main()
