from db import db


def main():
    db.drop_database('aavs_test')


if __name__ == '__main__':
    main()
