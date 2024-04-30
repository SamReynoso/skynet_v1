import json
from datetime import datetime

from alpaca.data.models import RawData
from alpaca.data.models.bars import Bar


def bar_formatter(raw_tuple: tuple) -> Bar:
    symbol = raw_tuple[0]

    good_data: RawData = {
            'timestamp': datetime.fromisoformat(raw_tuple[1]),
            'open': raw_tuple[2],
            'high': raw_tuple[3],
            'low': raw_tuple[4],
            'close': raw_tuple[5],
            'volume': raw_tuple[6],
            'trade_count': raw_tuple[7],
            'vwap': raw_tuple[8]
            }

    BAR_MAPPING = {
            "timestamp": "t",
            "open": "o",
            "high": "h",
            "low": "l",
            "close": "c",
            "volume": "v",
            "trade_count": "n",
            "vwap": "vw",
    }

    raw_data = {BAR_MAPPING[k]: v for k, v in good_data.items()}
    return Bar(symbol, raw_data)


def json_bar_formatter(json_str: str) -> Bar:
    dict_bar = json.loads(json_str)
    dict_bar['timestamp'] = datetime.fromisoformat(dict_bar['timestamp'])
    symbol = dict_bar['symbol']
    del dict_bar['symbol']
    BAR_MAPPING = {
            "timestamp": "t",
            "open": "o",
            "high": "h",
            "low": "l",
            "close": "c",
            "volume": "v",
            "trade_count": "n",
            "vwap": "vw",
    }
    raw_data = {BAR_MAPPING[k]: v for k, v in dict_bar.items()}
    return Bar(symbol, raw_data)

