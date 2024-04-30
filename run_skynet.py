import os
from skynet.skynet import SkyNet
from common.models import KeyPerams


def main():
    keys = {
            'api_key': os.environ['API_KEY'],
            'secret_key':  os.environ['SECRET_KEY'],
            }
    keys = KeyPerams(**keys)
    data_service = SkyNet(keys)
    data_service.run_until_killed()


if __name__ == '__main__':
    main()
