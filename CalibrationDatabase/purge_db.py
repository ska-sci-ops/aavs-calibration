import sys
import mongoengine
def main(args):
    mo.drop_database('aavs_test2')


if __name__ == '__main__':
    main(sys.argv[1:])
