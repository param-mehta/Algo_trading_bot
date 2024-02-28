import datetime
import pytz
import logging
import json
from kiteconnect import KiteConnect
import pandas as pd
from collections import defaultdict
from config import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# General config
USER_ID = [USER_ID_1]
IST = pytz.timezone('Asia/Kolkata')
CURRENT_DATE = datetime.datetime.now(IST).strftime('%Y-%m-%d')
PREVIOUS_DATE = (datetime.datetime.now(IST) - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

# Strategy config
INSTRUMENTS = ['NIFTY 50', 'NIFTY BANK']

# Load access tokens and login details from files
with open('data/access_tokens.json', "r") as f:
    access_tokens = json.load(f)
with open('data/login_details.json', "r") as f:
    LOGIN_DETAILS = json.load(f)

# Initialize KiteConnect object
uid = USER_ID[0]
api_key = LOGIN_DETAILS[uid]['api_key']
acc_token = access_tokens[uid]
kite = KiteConnect(api_key=api_key)
kite.set_access_token(acc_token)

# Fetch and save instrument data
options_instrument_dump = kite.instruments('NFO')
options_instrument_df = pd.DataFrame(options_instrument_dump)
options_instrument_df[options_instrument_df['name'].isin(['NIFTY', 'BANKNIFTY'])].to_csv('data/options_instrument_df.csv', index=False)

equity_instrument_dump = kite.instruments('NSE')
equity_instrument_df = pd.DataFrame(equity_instrument_dump)
equity_instrument_df = equity_instrument_df[equity_instrument_df['tradingsymbol'].isin(INSTRUMENTS)]
equity_instrument_df.to_csv('data/equity_instrument_df.csv', index=False)
print(equity_instrument_df.head())

# Initialize dictionaries for completed orders and condition checks
completed_orders = {'CE': dict(), 'PE': dict()}
for inst in INSTRUMENTS:
    for option_type in ['CE', 'PE']:
        completed_orders[option_type][inst] = 0

condition_checked = defaultdict(int)
with open("data/completed_orders.json", "w") as f:
    json.dump(completed_orders, f)

with open("data/condition_checked.json", "w") as f:
    json.dump(condition_checked, f)

# Create empty DataFrames for trades, failed orders, and runtime errors
trades_history = pd.read_csv('data/trades_history.csv', nrows=1)
failed_orders_history = pd.read_csv('data/failed_orders_history.csv', nrows=1)
runtime_errors_history = pd.read_csv('data/runtime_errors_history.csv', nrows=1)

trades = pd.DataFrame(columns=list(trades_history.columns))
failed_orders = pd.DataFrame(columns=list(failed_orders_history.columns))
runtime_errors = pd.DataFrame(columns=list(runtime_errors_history.columns))

# Save empty DataFrames to CSV files
trades.to_csv('data/trades.csv', index=False)
failed_orders.to_csv('data/failed_orders.csv', index=False)
runtime_errors.to_csv('data/runtime_errors.csv', index=False)
