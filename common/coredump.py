from datetime import datetime
from pytz import timezone
from datetime import timedelta
import json
import os
from typing import Callable


class BassAttr:
    def __init__(self, value) -> None:
        self.value = value

    def _add_callable(self, read: Callable, write: Callable):
        self.read = read
        self.write = write

    def dump(self):
        print('BassAttr class is missing dump method')
        raise NotImplementedError


class RunTimer(BassAttr):
    value: datetime

    def __init__(self, v: datetime | str):
        if type(v) is str:
            v = datetime.fromisoformat(v)
        super().__init__(v)

    def update(self):
        self.read()
        now = datetime.now(timezone('US/Eastern'))
        self.value = now
        self.write()

    def univers_start(self):
        self.read()
        return self.value - timedelta(days=2)

    def active_start(self):
        delay = timedelta(minutes=16)
        start = self.value - delay
        end_of_day = start.replace(hour=12+3, minute=30, second=0)
        start_of_day = start.replace(hour=9, minute=30, second=0)
        if start.weekday() in [5, 6]:
            print('weekend')
            self.update()
            return
        if start > end_of_day or start < start_of_day:
            print('outside of market hours')
            self.update()
            return
        self.update()
        return start

    def dump(self):
        return self.value.isoformat()


class FlagAttr(BassAttr):

    def mktrue(self):
        self.read()
        self.value = True
        self.write()

    def mkfalse(self):
        self.read()
        self.value = False
        self.write()

    def istrue(self):
        self.read()
        return self.value

    def isfalse(self):
        self.read()
        return not self.istrue()

    def dump(self):
        return self.value


class SuperBass:
    def __init__(self, data) -> None:
        self.path = data['path']
        self.add_attrs(data)

    def str_handle(self, k, v):
        if k == 'path':
            return v
        try:
            return datetime.fromisoformat(v)
        except Exception as e:
            print(e)
            print(k)
            raise e

    def add_attrs(self, data: dict):
        for k, v in data.items():
            if type(v) is str:
                v = self.str_handle(k, v)
            if k in self.__dict__.keys():
                if k != 'path':
                    self.__dict__[k].__setattr__('value', v)
            else:
                if type(v) is bool:
                    attr = FlagAttr(v)
                elif type(v) is datetime:
                    attr = RunTimer(v)
                elif isinstance(v, BassAttr):
                    attr = v
                    pass
                else:
                    raise TypeError
                attr._add_callable(self.read, self.write)
                self.__setattr__(k, attr)

    def read(self):
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                data = f.read()
                if data is not None or data != '':
                    try:
                        self.add_attrs(json.loads(data))
                        return
                    except json.JSONDecodeError as e:
                        print(e)
                else:
                    self.write()

    def write(self):
        try:
            with open(self.path, 'w+') as f:
                f.write(self.dump())
        except FileNotFoundError as e:
            print(f'could not find file at {self.path}')
            raise e

    def dump(self):
        schema = {}
        for k, v in self.__dict__.items():
            if k != 'path':
                schema[k] = v.dump()
        return json.dumps(schema)


class CoreDump(SuperBass):
    run_sky: FlagAttr
    run_cow: FlagAttr
    should_buffer: FlagAttr
    send_buffer: FlagAttr
    run_wonder: FlagAttr
    runtime: RunTimer

    def __init__(self) -> None:
        now = datetime.now(timezone('US/Eastern'))
        core_dump = {
                'path': 'data/programfiles/core_dump.json',
                'run_sky': False,
                'run_cow': False,
                'should_buffer': False,
                'send_buffer': False,
                'run_wonder': False,
                'runtime': RunTimer(now)
                }
        super().__init__(core_dump)

