from milkcow.milkcow import MilkCow


def main():
    cow = MilkCow()
    cow.loop_until_killed()


if __name__ == '__main__':
    main()
