import sys
import traceback
import datetime
import pandas as pd
from math import ceil
import logging
import time


def str_to_date(string, date_format='%Y-%m-%d %H:%M:%S'):
    """
    Convert a string to a datetime object.

    Args:
    string (str): The string representing the datetime.
    date_format (str, optional): The format of the datetime string. Defaults to '%Y-%m-%d %H:%M:%S'.

    Returns:
    datetime: The datetime object.
    """
    return datetime.datetime.strptime(string, date_format)


def extract_error_info():
    """
    Extract error information, log it, and save it.
    """
    global runtime_errors
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_message = str(exc_value)
    stack_trace = traceback.extract_tb(exc_traceback)
    line_no = stack_trace[-1].lineno
    code = stack_trace[-1].line
    error = pd.DataFrame([[datetime.datetime.now(IST), line_no, code, error_message]],
                         columns=['Timestamp', 'Line_no', 'Code', 'Error_message'])
    runtime_errors = runtime_errors.append(error).reset_index(drop=True)
    runtime_errors.to_csv('data/runtime_errors.csv', index=False)


def get_trading_symbol(instrument, option_type, instrument_df):
    """
    Get the trading symbol for the given instrument and option type.

    Args:
    instrument (str): The name of the instrument.
    option_type (str): The type of option.
    instrument_df (DataFrame): DataFrame containing instrument information.

    Returns:
    str: The trading symbol.
    """
    option_name = OPTION_NAME[instrument]
    try:
        expiry_date = instrument_df[instrument_df['name'] == option_name]['expiry'].min()
        spot_price = float(kite.ltp('NSE:'+instrument)['NSE:'+instrument]['last_price'])
        atm = ceil(spot_price/STRIKE_INTERVAL[instrument]) * STRIKE_INTERVAL[instrument] 
        strike_price = atm + OFFSET[option_type][instrument]
        symbol = instrument_df.query("name == @option_name and strike == @strike_price and expiry == @expiry_date and instrument_type == @option_type")['tradingsymbol'].values[0]
        return symbol
    except Exception as e:
        extract_error_info()


def get_indices_future_symbol(instrument_df):
    """
    Get the trading symbols for indices futures.

    Args:
    instrument_df (DataFrame): DataFrame containing instrument information.

    Returns:
    dict: Dictionary containing trading symbols for NIFTY 50 and NIFTY BANK futures.
    """
    fut_symbols = dict()
    expiry_date = instrument_df[(instrument_df['name'] == 'BANKNIFTY') & (instrument_df['instrument_type'] == 'FUT')]['expiry'].min()
    fut_symbols['NIFTY BANK'] = instrument_df.query("name == 'BANKNIFTY' and expiry == @expiry_date and instrument_type == 'FUT'")['tradingsymbol'].values[0]
    fut_symbols['NIFTY 50'] = instrument_df.query("name == 'NIFTY' and expiry == @expiry_date and instrument_type == 'FUT'")['tradingsymbol'].values[0]
    return fut_symbols


def get_instrument_token(symbol, instrument_df):
    """
    Get the instrument token for the given symbol.

    Args:
    symbol (str): The trading symbol.
    instrument_df (DataFrame): DataFrame containing instrument information.

    Returns:
    int: The instrument token.
    """
    return instrument_df[instrument_df['tradingsymbol'] == symbol]['instrument_token'].values[0]


def get_historical_data(token, from_date, to_date, interval):
    """
    Get historical data for the given token and time range.

    Args:
    token (int): The instrument token.
    from_date (str): The start date.
    to_date (str): The end date.
    interval (str): The interval for the data.

    Returns:
    DataFrame: Historical data.
    """
    try:
        data = kite.historical_data(token, from_date, to_date, interval)
        return pd.DataFrame(data).iloc[:-1]
    except:
        extract_error_info()


def get_option_signal_candle_low(token, sc_time):
    """
    Get the low price of the candle for the given time.

    Args:
    token (int): The instrument token.
    sc_time (str): The time for the candle.

    Returns:
    float: The low price of the candle.
    """
    from_date = CURRENT_DATE + ' 09:15:00'
    current_time = datetime.datetime.now(IST).strftime("%H:%M:%S")
    to_date = CURRENT_DATE + ' ' + current_time
    interval = '60minute'
    df = get_historical_data(token, from_date, to_date, interval)
    if df is None:
        return None
    return df[df['date'] == str(sc_time)]['low'].values[0]


def get_trade_high(token, buy_time):
    """
    Get the high price of the trade for the given time.

    Args:
    token (int): The instrument token.
    buy_time (str): The time of the trade.

    Returns:
    float: The high price of the trade.
    """
    from_date = buy_time
    current_time = datetime.datetime.now(IST).strftime("%H:%M:%S")
    to_date = CURRENT_DATE + ' ' + current_time
    interval = 'minute'
    try:
        data = kite.historical_data(token, from_date, to_date, interval)
        if len(data) == 0:
            return None
        return pd.DataFrame(data)['high'].max()
    except:
        extract_error_info()


def get_vwap(df):
    """
    Calculate the Volume Weighted Average Price (VWAP).

    Args:
    df (DataFrame): DataFrame containing OHLCV data.

    Returns:
    float: The VWAP.
    """
    tp = (df['high'] + df['low'] + df['close']) / 3



def get_ema(df, period=20, column='close'):
    """
    Calculate Exponential Moving Average (EMA) for a DataFrame.

    Args:
    df (DataFrame): DataFrame containing time series data.
    period (int, optional): Period for EMA calculation. Defaults to 20.
    column (str, optional): Name of the column for which EMA is to be calculated. Defaults to 'close'.

    Returns:
    float: Exponential Moving Average value.
    """
    ema_values = df[column].ewm(span=period, adjust=False).mean()
    return ema_values.values[-1]


def is_hammer(Open, close, high, low):
    """
    Check if the candlestick pattern is a hammer.

    Args:
    Open (float): Opening price.
    close (float): Closing price.
    high (float): Highest price.
    low (float): Lowest price.

    Returns:
    bool: True if the candlestick pattern is a hammer, False otherwise.
    """
    if (close > Open and (Open - low) >= 0.5 * (high-low)) or (close < Open and (close - low) >= 0.5 * (high-low)):
        return True
    return False


def is_bullish(Open, close, high, low):
    """
    Check if the candlestick pattern is bullish.

    Args:
    Open (float): Opening price.
    close (float): Closing price.
    high (float): Highest price.
    low (float): Lowest price.

    Returns:
    bool: True if the candlestick pattern is bullish, False otherwise.
    """
    if close > Open and (close - Open) >= 0.6 * (high-low):
        return True
    return False


def is_shooting_star(Open, close, high, low):
    """
    Check if the candlestick pattern is a shooting star.

    Args:
    Open (float): Opening price.
    close (float): Closing price.
    high (float): Highest price.
    low (float): Lowest price.

    Returns:
    bool: True if the candlestick pattern is a shooting star, False otherwise.
    """
    if (close > Open and (high - close) >= 0.5 * (high-low)) or (close < Open and (high - Open) >= 0.5 * (high-low)):
        return True
    return False


def is_bearish(Open, close, high, low):
    """
    Check if the candlestick pattern is bearish.

    Args:
    Open (float): Opening price.
    close (float): Closing price.
    high (float): Highest price.
    low (float): Lowest price.

    Returns:
    bool: True if the candlestick pattern is bearish, False otherwise.
    """
    if close < Open and (Open - close) >= 0.6 * (high-low):
        return True
    return False


def check_entry_conditions_one(Open, high, low, close, vwap, option_type):
    """
    Check entry conditions for a single candle.

    Args:
    Open (float): Opening price.
    high (float): Highest price.
    low (float): Lowest price.
    close (float): Closing price.
    vwap (float): Volume Weighted Average Price.
    option_type (str): Option type (CE for Call, PE for Put).

    Returns:
    bool: True if entry conditions are met, False otherwise.
    """
    if option_type == 'CE':
        return (is_bullish(Open, close, high, low) or is_hammer(Open, close, high, low)) and low <= vwap and close > vwap
    else:
        return (is_bearish(Open, close, high, low) or is_shooting_star(Open, close, high, low)) and high >= vwap and close < vwap


def check_entry_conditions(low, close, ema3, ema13, ema20, mbb, option_type):
    """
    Check entry conditions based on EMA and Bollinger Bands.

    Args:
    low (float): Lowest price.
    close (list): List of closing prices.
    ema3 (float): Exponential Moving Average over 3 periods.
    ema13 (float): Exponential Moving Average over 13 periods.
    ema20 (float): Exponential Moving Average over 20 periods.
    mbb (func): Function to calculate Middle Bollinger Band.
    option_type (str): Option type (CE for Call, PE for Put).

    Returns:
    bool: True if entry conditions are met, False otherwise.
    """
    if option_type == 'CE':
        return ema3 > ema13 and ema3 > ema20 and low > ema13 and close[-1] > ema3 and close[-1] > mbb(20) and low < ema3
    else:
        return ema3 < ema13 and ema3 < ema20 and low < ema13 and close[-1] < ema3 and close[-1] < mbb(20) and low > ema3
     

def place_order(symbol, transaction_type, quantity, acc):
    """
    Place an order.

    Args:
    symbol (str): Trading symbol.
    transaction_type (str): Type of transaction (BUY or SELL).
    quantity (int): Quantity to buy or sell.
    acc (Account): User's account.

    Returns:
    str: Order ID if successful, None otherwise.
    """
    try:
        order_id = acc.place_order(tradingsymbol=symbol,
                                    exchange=EXCHANGE,
                                    transaction_type=transaction_type,
                                    quantity=quantity,
                                    variety=VARIETY,
                                    order_type=ORDER_TYPE,
                                    product=PRODUCT,
                                    validity=VALIDITY)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        extract_error_info()


def place_gtt_order(trigger_type, trigger_values, limit_prices, last_price, symbol, transaction_type, quantity, acc):
    """
    Place a Good Till Trigger (GTT) order.

    Args:
    trigger_type (str): Type of trigger.
    trigger_values (list): List of trigger values.
    limit_prices (list): List of limit prices.
    last_price (float): Last traded price.
    symbol (str): Trading symbol.
    transaction_type (str): Type of transaction (BUY or SELL).
    quantity (int): Quantity to buy or sell.
    acc (Account): User's account.

    Returns:
    str: Order ID if successful, None otherwise.
    """
    order_json1 = {
        "exchange": "NSE",
        "tradingsymbol": symbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": "LIMIT",
        "product": "NRML",
        "transaction_type": transaction_type
    }
    order_json2 = order_json1.copy()
    orders = []

    order_json1["price"] = limit_prices[0]
    orders.append(order_json1)
    order_json2["price"] = limit_prices[1]
    orders.append(order_json2)

    try:
        order_id = acc.place_gtt(trigger_type=trigger_type,
                                  tradingsymbol=symbol,
                                  exchange=EXCHANGE,
                                  trigger_values=trigger_values,
                                  last_price=last_price,
                                  orders=orders)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        extract_error_info()


def modify_gtt_order(trigger_id, trigger_type, trigger_values, limit_prices, last_price, symbol, transaction_type, quantity, acc):
    """
    Modify a Good Till Trigger (GTT) order.

    Args:
    trigger_id (str): ID of the trigger.
    trigger_type (str): Type of trigger.
    trigger_values (list): List of trigger values.
    limit_prices (list): List of limit prices.
    last_price (float): Last traded price.
    symbol (str): Trading symbol.
    transaction_type (str): Type of transaction (BUY or SELL).
    quantity (int): Quantity to buy or sell.
    acc (Account): User's account.

    Returns:
    str: Order ID if successful, None otherwise.
    """
    order_json1 = {
        "exchange": "NSE",
        "tradingsymbol": symbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": "LIMIT",
        "product": "NRML",
        "transaction_type": transaction_type
    }
    order_json2 = order_json1.copy()
    orders = []

    order_json1["price"] = limit_prices[0]
    orders.append(order_json1)
    order_json2["price"] = limit_prices[1]
    orders.append(order_json2)

    try:
        order_id = acc.modify_gtt(trigger_id=trigger_id,
                                   trigger_type=trigger_type,
                                   tradingsymbol=symbol,
                                   exchange=EXCHANGE,
                                   trigger_values=trigger_values,
                                   last_price=last_price,
                                   orders=orders)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        extract_error_info()


def place_sl_order(symbol, transaction_type, quantity, acc, tsl):
    """
    Place a Stop Loss (SL) order.

    Args:
    symbol (str): Trading symbol.
    transaction_type (str): Type of transaction (BUY or SELL).
    quantity (int): Quantity to buy or sell.
    acc (Account): User's account.
    tsl (float): Trigger price for stop loss.

    Returns:
    str: Order ID if successful, None otherwise.
    """
    try:
        order_id = acc.place_order(tradingsymbol=symbol,
                                    exchange=EXCHANGE,
                                    transaction_type=transaction_type,
                                    quantity=quantity,
                                    variety=VARIETY,
                                    order_type='SL',
                                    price=tsl,
                                    trigger_price=tsl,
                                    product=PRODUCT,
                                    validity=VALIDITY)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        extract_error_info()


def modify_sl_order(quantity, acc, tsl, old_order_id):
    """
    Modify a Stop Loss (SL) order.

    Args:
    quantity (int): New quantity.
    acc (Account): User's account.
    tsl (float): New trigger price for stop loss.
    old_order_id (str): ID of the original order.

    Returns:
    str: Order ID if successful, None otherwise.
    """
    try:
        order_id = acc.modify_order(order_id=old_order_id,
                                    quantity=quantity,
                                    variety=VARIETY,
                                    price=tsl,
                                    trigger_price=tsl,
                                    validity=VALIDITY)

        logging.info("Order placed. ID is: {}".format(order_id))
        return order_id
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))
        extract_error_info()


def get_order_details(user, order_id):
    """
    Get details of an order.

    Args:
    user (str): User identifier.
    order_id (str): ID of the order.

    Returns:
    DataFrame: Details of the order.
    str: Order status.
    str: Status message.
    str: Timestamp of the last update.
    """
    acc = accounts[user]
    while True:
        try:
            orders = pd.DataFrame(acc.orders())
            break
        except Exception as e:
            extract_error_info()
            time.sleep(5)

    order = orders[orders['order_id'] == str(order_id)]
    status = order['status'].values[0]
    status_message = order['status_message'].values[0]
    timestamp = order['exchange_update_timestamp'].values[0]
    return order, status, status_message, timestamp


def get_gtt_order_details(user, order_id):
    """
    Get details of a Good Till Trigger (GTT) order.

    Args:
    user (str): User identifier.
    order_id (str): ID of the order.

    Returns:
    str: Order status.
    str: Timestamp of the last update.
    """
    acc = accounts[user]
    while True:
        try:
            order = acc.get_gtt(order_id)
            break
        except Exception as e:
            extract_error_info()
            time.sleep(5)

    status = order['data']['status']
    timestamp = order['data']['updated_at']
    return status, timestamp
