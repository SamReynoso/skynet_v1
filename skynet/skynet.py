from datetime import datetime, timedelta
import time
import socket

from pytz import timezone

from extra.banners import print_skynet
from common.utils import make_request
from common.connections import database_connection, send_wrapper
from common.formatters import bar_formatter
from common.models import KeyPerams
from common.filesystem import read_symbols
from common.database import test_history, get_history

from common.database import save_bar as util_save_bar
from common.coredump import CoreDump

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.models.bars import Bar
from alpaca.data.models import BarSet
from typing import Optional


class DataConn:
    def __init__(self) -> None:
        self.conn = database_connection()
        self.tested = set()
        self.current = set()
        self.new = set()

    def update(self):
        symbols = read_symbols()
        for symbol in symbols:
            if symbol not in self.tested:
                on_disk = self.on_disk(symbol)
                if on_disk is True:
                    self.current.add(symbol)
                elif on_disk is False:
                    self.new.add(symbol)

    def on_disk(self, symbol: str) -> bool:
        self.tested.add(symbol)
        return test_history(self.conn, symbol)

    def save_bars(self, bars: list) -> None:
        curr = self.conn.cursor()
        for bar in bars:
            util_save_bar(curr, bar)
        self.conn.commit()

    def find_new_symbols(self) -> set:
        symbols = read_symbols()
        diff = len(symbols) - len(self.tested)
        if diff > 0:
            print(f'Checking on disk for {diff} symbols')
        new = set()
        for symbol in symbols:
            if symbol not in self.tested:
                if self.on_disk(symbol) is False:
                    new.add(symbol)
        if len(new) > 0:
            print(f'    {len(new)} need history')
        return new

    def mock_buffer(self, symbol):
        recoreds = get_history(symbol, self.conn)
        bars = [bar_formatter(rec) for rec in recoreds]
        return bars


class Buffer:
    def __init__(self):
        self.data: dict = {}
        self.is_buffering: bool = False
        self.core = CoreDump()

    def add_to_buffer(self, symbol: str, bars: list):
        if self.is_buffering is True:
            if symbol in self.data.keys():
                self.data[symbol].extend(bars)
            else:
                self.data[symbol] = bars

    def wrapped(self, uni: socket.socket):
        print(f'sending buffer for {len(self.data.keys())} symbols')
        cnt = 0
        for key in self.data.keys():
            data: list[Bar] = self.data[key]
            for bar in data:
                uni.send(bar.model_dump_json().encode())
                cnt += 1
        print('sent', cnt, 'bars')

    def send(self):
        path = 'data/programfiles/socket'
        send_wrapper(self.wrapped, path)


class Active:
    def __init__(self):
        self.new: set = set()
        self.ignore: set = set()
        self.active: set = set()
        self.loop_time = 0
        self.pools: list[set] = []
        self.pool_map: dict[str, int] = {}
        self.time_map: dict[int, Optional[datetime]] = {}
        self.current: list = []
        self.index: int = 0

    def _get_timestamp(self, index: int) -> Optional[datetime]:
        return self.time_map[index]

    def _update_time(self, timestamp: datetime, index: int):
        self.time_map[index] = timestamp

    def _pool_add(self, symbol):
        if symbol not in self.pool_map.keys():
            if len(self.pools) == 0 or len(self.pools[-1]) == 10:
                self.pools.append(set())
                self.time_map[len(self.pools) - 1] = None
            self.pools[len(self.pools) - 1].add(symbol)
            self.pool_map[symbol] = len(self.pools)

    def _pool_drop(self, symbol: str):
        if symbol in self.pool_map.keys():
            self.pools[self.pool_map[symbol]].remove(symbol)
            del self.pool_map[symbol]

    def update(self, timestamp: datetime):
        assert self.index is not None
        self._update_time(timestamp, self.index)

    def get_time(self):
        assert self.index is not None
        return self._get_timestamp(self.index)

    def add_new_symbols(self, symbols: list | set):
        for symbol in symbols:
            if symbol not in self.ignore:
                if symbol not in self.active:
                    self.new.add(symbol)

    def ignore_symbol(self, symbol: str):
        if symbol in self.ignore:
            self.new.discard(symbol)
            self.ignore.add(symbol)
            self.active.discard(symbol)
        self._pool_drop(symbol)

    def activate_symbol(self, symbol: str):
        if symbol in self.active:
            self.new.discard(symbol)
            self.ignore.discard(symbol)
            self.active.add(symbol)
        self._pool_add(symbol)

    def next_new(self, max_length=10):
        length = len(self.new)
        if length == 0:
            seg = list(self.new)
        else:
            if length > max_length:
                length = max_length
            seg = [self.new.pop() for _ in range(length)]
        return seg

    def next(self):
        self.index += 1
        if self.index == len(self.pools):
            self.index = 0
        self.current = list(self.pools[self.index])


class Fecth:
    def __init__(self, keys: KeyPerams):
        self.client = StockHistoricalDataClient(secret_key=keys.secret_key,
                                                api_key=keys.api_key)

    def price(self, symbols: list, start: datetime):
        print('fetching price... ', len(symbols))
        return self.fetch(symbols, start)

    def history(self, symbols: list, start_of_univers: datetime):
        print('fetching history...')
        return self.fetch(symbols, start_of_univers)

    def fetch(self, symbols: list, start: datetime):
        assert len(symbols) > 0
        assert len(symbols) <= 10
        barset = make_request(symbols, start, self.client)
        assert isinstance(barset, BarSet)
        return barset


class SkyNet:
    def __init__(self, keys: KeyPerams):
        self.buffer: Buffer = Buffer()
        self.core = CoreDump()
        self.data = DataConn()
        self.active = Active()
        self.fetch = Fecth(keys)
        self.redraw = True

    def activate_old_symbols(self):
        for symbol in self.data.current:
            self.active.activate_symbol(symbol)

    def get_timestamp(self, delta: int = 17):
        dob = self.active.get_time()
        if dob is None:
            return self.core.runtime.active_start()
        else:
            age = dob - datetime.now(timezone('US/Eastern'))
            if age > timedelta(delta):
                return dob
        print('waiting to fecth this pool again')

    def handle_barset(self, symbols: list, barset: BarSet):
        for symbol in symbols:
            timestamp = None
            if symbol not in barset.data.keys():
                print('    ...data not found', symbol)
                self.active.ignore_symbol(symbol)
            else:
                bars = barset.data[symbol]
                assert bars[-1].timestamp == timestamp or timestamp is None
                timestamp = bars[-1].timestamp
                if len(bars) > 0:
                    self.buffer.add_to_buffer(symbol, bars)
                    self.active.activate_symbol(symbol)
                    self.data.save_bars(bars)
                else:
                    self.active.ignore_symbol(symbol)
            assert timestamp is not None
            self.active.update(timestamp)

    def try_new(self):
        self.buffer.is_buffering = self.core.should_buffer.value
        new = self.data.find_new_symbols()
        self.active.add_new_symbols(new)
        start = self.core.runtime.univers_start()
        while len(self.active.new) > 0:
            symbols = self.active.next_new()
            barset = self.fetch.history(symbols, start)
            self.handle_barset(symbols, barset)

    def get_active(self):
        self.buffer.is_buffering = True
        self.active.next()
        start = self.get_timestamp()
        if start is not None:
            barset = self.fetch.price(self.active.current, start)
            if barset is not None:
                self.handle_barset(self.active.current, barset)

    def mock(self):
        self.buffer.is_buffering = True
        for i, symbol in enumerate(self.data.current):
            print(len(self.data.current) - i + 1, 'remaining')
            bars = self.data.mock_buffer(symbol)
            self.buffer.add_to_buffer(symbol, bars)

    def run_until_killed(self):
        print_skynet(True)
        self.data.update()
        self.activate_old_symbols()
        self.mock()
        while True:
            while self.core.run_sky.istrue():
                wait_s = time.time()
                self.try_new()
                self.get_active()
                while time.time() - wait_s < 20:
                    print('waiting to send')
                    if self.core.send_buffer.istrue() is True:
                        self.buffer.send()
                        self.core.send_buffer.mkfalse()
                    if self.core.run_sky.value is False:
                        break
                    time.sleep(.5)
                print_skynet(True)
            print_skynet(True)
            print('waiting')
            time.sleep(.5)
