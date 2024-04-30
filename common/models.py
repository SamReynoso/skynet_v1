import os
import json
from datetime import datetime
from pydantic import BaseModel


class MqttPerams(BaseModel):
    topic: str
    addr: str
    port1: int
    port2: int


class KeyPerams(BaseModel):
    api_key: str
    secret_key: str


class TradeStatus(BaseModel):
    created: datetime
    time_of_death: float
    qty: float
    pl: float
    plpc: float
    symbol: str
    target_entry: float
    actual_entry: float
    stop_loss: float
    take_profit: float


class SuperBass(BaseModel):
    path: str = 'tmp'

    def __init__(self, /, **data) -> None:
        super().__init__(**data)

    def get(self):
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                data = f.read()
                if data is not None:
                    self = super().__init__(**json.loads(data))
        else:
            self.write()

    def write(self):
        try:
            with open(self.path, 'w+') as f:
                f.write(self.model_dump_json())
        except FileNotFoundError as e:
            print(f'could not find file at {self.path}')
            raise e
