
import numpy as np
from datetime import datetime
from pytz import timezone

from common.super_max import calc_signal, create_pareto
from project.models import Target

from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame



def make_target(symbol: str, minutes):
    minutes = np.array(minutes)
    kernel, trailing_kernel = create_pareto(48, 3)
    kernel_h, trailing_kernel_h = create_pareto(400, 3)
    target = {
            'symbol': symbol,

            'created': datetime.now(timezone('US/Eastern')),
            'new': True,
            'active': False,

            'trade_signal': calc_signal(minutes[-48:],
                                        kernel,
                                        trailing_kernel),
            'trade_std': np.std(minutes[-150:]),
            'trade_ave': np.mean(minutes[-150:]),

            'hold_signal': calc_signal(minutes[-400:],
                                       kernel_h,
                                       trailing_kernel_h),
            'hold_std': np.std(minutes[-1_000:]),
            'hold_ave': np.mean(minutes[-1_000:]),

            'cur': minutes[-1]
            }
    return Target(**target)


def make_request(symbols, start, cur, client):
    table_name = 'minute_price'
    timeframe = TimeFrame.Minute
    request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=None)
    bars = client.get_stock_bars(request_params)
    prog = 0
    price_map = {}
    for symbol in symbols:
        minutes = []
        try:
            for bar in bars[symbol]:
                add_bar(cur, bar, table_name)
                minutes.append(bar.close)
        except KeyError:
            # this is an api thing
            pass
        prog += 1
        if len(minutes) > 0:
            price_map[symbol] = []
    return price_map
