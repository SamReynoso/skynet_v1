from extra.cli import main as cli
from milkcow.milkcow import Rpc


def wonderworker(rpc: Rpc):
    print(len(rpc.history.keys()))


if __name__ == '__main__':
    cli()
