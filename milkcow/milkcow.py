import os
import time
from multiprocessing import Process

from alpaca.data.models.bars import Bar

from common.formatters import bar_formatter, json_bar_formatter
from extra.banners import print_milkcow
from common.connections import database_connection, ServerSocket
from common.filesystem import read_symbols
from common.coredump import CoreDump
from common.database import get_history


class Rpc:
    def __init__(self) -> None:
        self.history: dict = {}

    def stats(self):
        total = 0
        for _, v in self.history.items():
            total += len(v)
        print('total minutes:', total)


    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def remove(self, symbol):
        if symbol in self.history.keys():
            del self.history[symbol]

    def add_bar(self, symbol, bar: Bar):
        if symbol in self.history.keys():
            self.history[symbol].append(bar)
        else:
            self.history[symbol] = [bar]

    def add_bars(self, symbol, bars: list[Bar]):
        if symbol in self.history.keys():
            self.history[symbol].extend(bars)
        else:
            self.history[symbol] = bars

    def run(self, pid: int):
        self.pid = pid
        try:
            from wonderworker import wonderworker
            wonderworker(self)
        except Exception as e:
            print('there was a problem while running the remote code')
            print(e)
            return


class MilkCow:
    def __init__(self):
        self.conn = database_connection()
        self.workers: list[Rpc] = [Rpc() for _ in range(8)]
        self.core: CoreDump = CoreDump()
        self.map: dict[str, int] = {}
        self.sym_cnt = 0

    def remove_removable(self, symbols: list[str]):
        removed = 0
        for key, pid in self.map.items():
            if key not in symbols:
                self.workers[pid].remove(key)
                removed += 1
        if removed > 0:
            print(f'removed {removed} symbols')

    def watch_file(self):
        symbols = read_symbols()
        self.remove_removable(symbols)
        while len(symbols) > 0:
            pid = self.sym_cnt % 8
            symbol = symbols.pop()
            if symbol not in self.map.keys():
                self.map[symbol] = pid
                # data = get_history(symbol, self.conn)
                # for datum in data:
                #    bar = bar_formatter(datum)
                #    self.workers[pid].add_bar(symbol, bar)
                self.workers[pid].add_bar(symbol, ())
                self.sym_cnt += 1

    def run_worker(self):
        processes = []
        for i in range(8):
            worker = self.workers[i]
            args = (i,)
            p = Process(target=worker.run, args=args)
            processes.append(p)
        start = time.time()
        for i, p in enumerate(processes):
            print('WonderWorker', i)
            p.start()
        while time.time() - start < 30:
            if not any(p.is_alive() for p in processes):
                break
        else:
            for i, p in enumerate(processes):
                p.terminate()
                p.join()

    def add_data(self, data):
        bar: Bar = json_bar_formatter(data)
        self.workers[self.map[bar.symbol]].add_bar(bar.symbol, bar)

    def consum(self):
        uni = ServerSocket()
        cnt = 0
        print('received so far:')
        while True:
            data = uni.recv()
            if data is None:
                print('-'*20)
                print(f'final: {cnt:,}')
                return
            self.add_data(data)
            cnt += 1
            if cnt >= 100_000 and cnt % 100_000 == 0:
                print(f'    {cnt:,}')

    def loop_until_killed(self):
        while True:
            print_milkcow()
            while self.core.run_cow.istrue():
                self.core.should_buffer.mktrue()
                self.watch_file()
                if self.core.run_wonder.value is True:
                    self.run_worker()
                    self.core.run_wonder.mkfalse()
                if self.core.send_buffer.value is True:
                    self.consum()
                    self.core.send_buffer.mkfalse()
                time.sleep(.5)
                self.core.read()
            print('waiting')
            time.sleep(.5)
