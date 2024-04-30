import os


def read_symbols():
    path = 'data/programfiles/symbols'
    if os.path.isfile(path):
        with open(path, 'r') as f:
            return list({line.rsplit()[0] for line in f})
    else:
        raise FileNotFoundError


