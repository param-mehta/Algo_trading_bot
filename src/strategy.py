import datetime
import pytz
import calendar
import logging
import json
import time
import traceback
import sys
from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
from math import ceil,floor
import os
from config import *
from utils import *


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# General config
USER_ID = [USER_ID_1]
HIST_USER_ID = USER_ID_1  # Account with historical API subscription
IST = pytz.timezone('Asia/Kolkata')
CURRENT_DATE = datetime.datetime.now(IST).strftime('%Y-%m-%d')
PREVIOUS_DATE = (datetime.datetime.now(IST) - datetime.timedelta(days=14)).strftime('%Y-%m-%d')

# Strategy config
INSTRUMENTS = ['NIFTY 50', 'NIFTY BANK']
OPTION_NAME = {'NIFTY 50': 'NIFTY', 'NIFTY BANK': 'BANKNIFTY'}
STRIKE_INTERVAL = {'NIFTY 50': 50, 'NIFTY BANK': 100}
DESIRED_STRIKE = {'NIFTY 50': 4, 'NIFTY BANK': 4}
OFFSET = {'CE': dict(), 'PE': dict()}
for inst in INSTRUMENTS:
    OFFSET['CE'][inst] = STRIKE_INTERVAL[inst] * -DESIRED_STRIKE[inst]
    OFFSET['PE'][inst] = STRIKE_INTERVAL[inst] * DESIRED_STRIKE[inst]

TRAILING_STOP_LOSS = {'NIFTY 50': 0.18, 'NIFTY BANK': 0.18}
MAIN_STOP_LOSS = {'NIFTY 50': 0.27, 'NIFTY BANK': 0.27}
TARGET = {'NIFTY 50': 5, 'NIFTY BANK': 5}

NO_OF_CYCLES = 3
SQUARE_OFF_TIME = datetime.datetime.combine(datetime.datetime.now(IST), datetime.time(15, 25))
LOTS = 1

# Order config
EXCHANGE = 'NFO'
VARIETY = 'regular'  # amo, co, iceberg, auction
ORDER_TYPE = 'MARKET'  # LIMIT, SL, SL-M
PRODUCT = 'NRML'  # CNC, MIS, NORMAL
VALIDITY = 'DAY'  # IOC, TTL

# Login details
with open('data/access_tokens.json', "r") as f:
    access_tokens = json.load(f)
with open('data/login_details.json', "r") as f:
    LOGIN_DETAILS = json.load(f)



# Create dictionary to store KiteConnect instances for each user
accounts = dict()

# Initialize KiteConnect instances for each user and store them in the dictionary
for user in USER_ID:
    api_key = LOGIN_DETAILS[user]['api_key']
    kc = KiteConnect(api_key=api_key)
    kc.set_access_token(access_tokens[user])
    accounts[user] = kc

# Set kite variable to the KiteConnect instance for the account with historical API subscription
kite = accounts[HIST_USER_ID]


# Loading data from CSV and JSON files
entry_history = pd.read_csv('data/entry_history.csv')
positions = pd.read_csv('data/positions.csv')
trades_history = pd.read_csv('data/trades_history.csv')
trades = pd.read_csv('data/trades.csv')
failed_orders = pd.read_csv('data/failed_orders.csv')
failed_orders_history = pd.read_csv('data/failed_orders.csv')
runtime_errors = pd.read_csv('data/runtime_errors.csv')
runtime_errors_history = pd.read_csv('data/runtime_errors_history.csv')
sl_orders = pd.read_csv('data/sl_orders.csv')

# Define column names
entry_cols = list(positions.columns)
exit_cols = ['Position_id', 'User_id', 'Sell_order_id', 'Sell_time', 'Sell_price', 'Exit_type']

# Load instrument data from CSV files
options_instrument_df = pd.read_csv('data/options_instrument_df.csv')
equity_instrument_df = pd.read_csv('data/equity_instrument_df.csv')

# Load miscellaneous data from JSON files
with open("data/misc.json", "r") as f:
    misc = json.load(f)
with open("data/crossover.json", "r") as f:
    crossover = json.load(f)
with open("data/tsl.json", "r") as f:
    tsl = json.load(f)
with open("data/tsl_increment.json", "r") as f:
    tsl_increment = json.load(f)
with open("data/target.json", "r") as f:
    target = json.load(f)
with open("data/prev_high.json", "r") as f:
    prev_high = json.load(f)
with open("data/completed_orders.json", "r") as f:
    completed_orders = json.load(f)


position_id = misc['position_id']
fut_symbols = get_indices_future_symbol(options_instrument_df)
fut_symbols


#main strategy loop
while(True):
    #check conditions for each instrument
    
    with open("data/condition_checked.json", "r") as f:
            condition_checked = json.load(f)
    
    hour_no = datetime.datetime.now(IST).hour
    if not condition_checked[hour_no]:
        condition_checked[hour_no] = 1
        with open("data/condition_checked.json", "w") as f:
            json.dump(condition_checked, f)
        
        for inst in INSTRUMENTS:
            if inst in positions['Instrument'].unique():
                continue       
            
            token_inst = fut_symbols[inst]
            instrument_df = options_instrument_df.copy()
            
            token = get_instrument_token(token_inst,instrument_df)
            current_time = datetime.datetime.now(IST).strftime("%H:%M:%S")
            to_date = CURRENT_DATE + ' ' + current_time
            from_date = PREVIOUS_DATE + ' 09:15:00'
            interval = '60minute'
            df = get_historical_data(token,from_date,to_date,interval)
            if df is None:
                continue

            ema3 = get_ema(df,3)
            ema13 = get_ema(df,13)
            ema20 = get_ema(df,20)
            current = df.iloc[-1]
            low = current['low']
            high = current['high']
            close = current['close']
            Open = current['open']
            sc_time = current['date']

            for option_type in ['CE','PE']:
                if completed_orders[option_type][inst] < NO_OF_CYCLES and check_entry_conditions(low,close,ema3,ema13,ema20,mbb,option_type):
                    symbol = get_trading_symbol(inst,option_type,options_instrument_df)
                    if symbol is None:
                        continue
                    token = get_instrument_token(symbol,options_instrument_df)
                    lot_size = options_instrument_df[options_instrument_df['tradingsymbol'] == symbol]['lot_size'].values[0]

                    position_id += 1
                    misc['position_id'] = position_id
                    placed_orders = {}

                    for user in USER_ID:
                        acc = accounts[user]
                        order_id = place_order(symbol,'BUY',LOTS * lot_size,acc)
                        if order_id:
                            placed_orders[user] = order_id

                    time.sleep(5)
                    successful_orders = []
                    for user, order_id in placed_orders.items():
                        order,status,status_message,timestamp = get_order_details(user,order_id)
                        if status == 'COMPLETE':
                            successful_orders.append(user)
                            buy_price = order['average_price'].values[0]
                            entry_data = [position_id,user,order_id,inst+option_type,inst,symbol,option_type,token,timestamp,buy_price,buy_price,LOTS * lot_size,0] + current.to_list()[:-1]
                            entry_data = pd.DataFrame([entry_data],columns = entry_cols)   
                            entry_history = entry_history.append(entry_data).reset_index(drop=True)
                        else:
                            failed_data = [position_id,user,order_id,symbol,'BUY',timestamp,status,status_message]
                            failed_data = pd.DataFrame([failed_data],columns = list(failed_orders.columns))
                            failed_orders = failed_orders.append(failed_data).reset_index(drop=True)
                            failed_orders.to_csv('data/failed_orders.csv',index=False)

                    if len(successful_orders) == 0:
                        position_id -= 1
                        misc['position_id'] = position_id
                        continue

                    positions = positions.append(entry_data).reset_index(drop=True)
                    entry_history.to_csv('data/entry_history.csv',index=False)

                    prev_high[option_type][inst] = buy_price
                    tsl_increment[option_type][inst] = TRAILING_STOP_LOSS[inst] * buy_price
                    tsl[option_type][inst] = buy_price - MAIN_STOP_LOSS[inst] * buy_price
                    target[option_type][inst] = buy_price + TARGET[inst] * buy_price
                    
                    
                    # Placing OCO gtt orders (tsl and target) for all the successful buy orders
                    quantity = LOTS * lot_size
                    limit_prices = [tsl[option_type][inst],target[option_type][inst]]
                    

                    try:
                        last_price = float(kite.ltp('NFO:'+symbol)['NFO:'+symbol]['last_price'])
                    except Exception as e:
                        last_price = buy_price
                        extract_error_info()
                    

                    placed_sl_orders = {}
                    for user in successful_orders:
                        acc = accounts[user]
                        order_id = place_gtt_order('two-leg',limit_prices,limit_prices,last_price,symbol,'SELL',quantity,acc)
                        if order_id:
                            placed_sl_orders[user] = order_id
                    time.sleep(2)
                    for user, order_id in placed_sl_orders.items():
                        status,timestamp = get_gtt_order_details(user,order_id)
                        status_message = 'None'
                        if status in ['triggered','active']:
                            entry_data = pd.DataFrame([[position_id,user,order_id,symbol]],columns = list(sl_orders.columns)) 
                            sl_orders = sl_orders.append(entry_data).reset_index(drop=True)
                        else:
                            failed_data = [position_id,user,order_id,symbol,'SELL',timestamp,status,status_message]
                            failed_data = pd.DataFrame([failed_data],columns = list(failed_orders.columns))
                            failed_orders = failed_orders.append(failed_data).reset_index(drop=True)
                            failed_orders.to_csv('data/failed_orders.csv',index=False)

                    sl_orders.to_csv('data/sl_orders.csv',index=False)
                    positions.loc[len(positions)-1,'Trailing_SL'] = tsl[option_type][inst]
                    positions.to_csv('data/positions.csv',index=False)

                    with open("data/prev_high.json", "w") as f:
                        json.dump(prev_high, f)

                    with open("data/tsl.json", "w") as f:
                        json.dump(tsl, f)

                    with open("data/tsl_increment.json", "w") as f:
                        json.dump(tsl_increment, f)

                    with open("data/target.json", "w") as f:
                        json.dump(target, f)

                    with open("data/misc.json", "w") as f:
                        json.dump(misc, f)            
        
    #track open positions
    if len(positions) > 0:
        

        #updating the ltp for every position and if tsl has changed, modifying the slm order
        for i,row in positions.iterrows():
            symbol = row['Symbol']
            option = row['Option']
            inst = row['Instrument']
            position = row['Position_id']
            token = row['Token']
            buy_time = row['Buy_time']
            quantity = row['Quantity']
            last_price = row['LTP']
                
            try:
                last_price = float(kite.ltp('NFO:'+symbol)['NFO:'+symbol]['last_price'])
                positions.loc[i,'LTP'] = last_price
                positions.to_csv('data/positions.csv',index=False)     
            except Exception as e:
                extract_error_info()
                        
            trade_high = get_trade_high(token,buy_time)
            if trade_high is None:
                continue
            
            if trade_high - prev_high[option][inst] >= tsl_increment[option][inst]:
                prev_high[option][inst] += tsl_increment[option][inst]
                tsl[option][inst] += tsl_increment[option][inst]
                positions.loc[i,'Trailing_SL'] = tsl[option][inst]
                positions.to_csv('data/positions.csv',index=False)
                
                with open("data/prev_high.json", "w") as f:
                    json.dump(prev_high, f)

                with open("data/tsl.json", "w") as f:
                    json.dump(tsl, f)
                    
                limit_prices = [tsl[option_type][inst],target[option_type][inst]]

                for i,row in sl_orders[sl_orders['Position_id'] == position].iterrows():
                    old_order_id = row['Order_id']
                    user = row['User_id']
                    acc = accounts[user]
                    order_id = modify_gtt_order(old_order_id,'two-leg',limit_prices,limit_prices,last_price,symbol,'SELL',quantity,acc)
                    if order_id:
                        sl_orders.loc[i,'Order_id'] = order_id
            
        remove_orders = []
        for i,row in sl_orders.iterrows():
            user = row['User_id']
            order_id = row['Order_id']
            position = row['Position_id']
            symbol = row['Symbol']
            acc = accounts[user]
            try:
                orders = pd.DataFrame(acc.orders())
            except Exception as e:
                extract_error_info()
                continue

            order = orders[(orders['tradingsymbol'] == symbol) & (orders['transaction_type'] == 'SELL')].iloc[-1]
            if order['status'] == 'COMPLETE':
                sell_price = order['average_price']
                timestamp = order['exchange_update_timestamp']
                exit_data = [position,user,order_id,timestamp,sell_price,'Trailing_SL']
                exit_data = pd.DataFrame([exit_data],columns = exit_cols)
                temp_df = entry_history.merge(exit_data,how='inner',on=['Position_id','User_id'])
                trades = trades.append(temp_df).reset_index(drop=True)
                remove_orders.append(i)
        sl_orders = sl_orders.drop(remove_orders).reset_index(drop=True)
        sl_orders.to_csv('data/sl_orders.csv',index=False)
        trades.to_csv('data/trades.csv',index=False)

        #removing positions from entry history and positions table
        for pos in positions['Position_id'].unique():
            if pos not in sl_orders['Position_id'].values:
                inst = positions[positions['Position_id'] == pos]['Instrument'].values[0]
                option = positions[positions['Position_id'] == pos]['Option'].values[0]
                positions = positions[positions['Position_id'] != pos].reset_index(drop=True)
                entry_history = entry_history[entry_history['Position_id'] != pos].reset_index(drop=True)
                positions.to_csv('data/positions.csv',index=False)
                entry_history.to_csv('data/entry_history.csv',index=False)
                tsl[option][inst] = 0
                prev_high[option][inst] = 0
                completed_orders[option][inst] += 1
                
                with open("data/prev_high.json", "w") as f:
                    json.dump(prev_high, f)

                with open("data/tsl.json", "w") as f:
                    json.dump(tsl, f)
                
                with open("data/completed_orders.json", "w") as f:
                    json.dump(completed_orders, f)


    #if strategy cycle has completed for all instruments, stop the strategy
    order_freq = list(completed_orders['CE'].values()) + list(completed_orders['PE'].values())
    if all(x == NO_OF_CYCLES for x in order_freq):
        break
    if datetime.datetime.now(IST) > SQUARE_OFF_TIME:
        break



trades_history = trades_history.append(trades).reset_index(drop=True)
failed_orders_history = failed_orders_history.append(failed_orders).reset_index(drop=True)
runtime_errors_history = runtime_errors_history.append(runtime_errors).reset_index(drop=True)

trades_history.to_csv('data/trades_history.csv',index=False)
failed_orders_history.to_csv('data/failed_orders_history.csv',index=False)
runtime_errors_history.to_csv('data/runtime_errors_history.csv',index=False)