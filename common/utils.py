from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.models import BarSet


def make_request(symbols, start, client) -> BarSet:
    request_perams = StockBarsRequest(symbol_or_symbols=symbols,
                                      timeframe=TimeFrame.Minute,
                                      start=start,
                                      end=None)
    return client.get_stock_bars(request_perams)


