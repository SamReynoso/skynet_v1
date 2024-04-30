import time
import sqlite3
from alpaca.data.models import Bar


def save_bar(curr: sqlite3.Cursor, bar: Bar) -> None:
    values = (
            bar.symbol,
            bar.timestamp,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.trade_count,
            bar.vwap,
            )
    sql = '''\
            INSERT INTO minute_price
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    try:
        curr.execute(sql, values)
    except Exception as e:
        print(e)


def get_history(symbol, conn):
    cur = conn.cursor()
    sql = f'''SELECT * FROM minute_price\
            WHERE symbol is "{symbol}";'''
    try:
        cur.execute(sql)
    except sqlite3.OperationalError as e:
        time.sleep(5)
        print(e)
        print('waiting to retry')
        return get_history(symbol, conn)
    return cur.fetchall()


def test_history(conn, symbol) -> bool:
    cur = conn.cursor()
    sql = f'''SELECT symbol FROM minute_price\
            WHERE symbol is "{symbol}";'''
    try:
        cur.execute(sql)
    except sqlite3.OperationalError as e:
        time.sleep(5)
        print(e)
        print('waiting to retry')
        return test_history(symbol, conn)
    record = cur.fetchone()
    if record is not None:
        if record[0] == symbol:
            return True

    return False

