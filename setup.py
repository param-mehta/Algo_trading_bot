import json
import pandas as pd

# Define list of instruments
INSTRUMENTS = ['NIFTY 50', 'NIFTY BANK']

# Initialize DataFrames for entry, positions, exit, SL orders, failed orders, and runtime errors
entry_history = pd.DataFrame(columns=['Position_id', 'User_id', 'Buy_order_id', 'Inst_option', 'Instrument', 'Symbol', 'Option', 'Token', 'Buy_time', 'Buy_price', 'LTP', 'Quantity', 'Trailing_SL', 'Signal_candle', 'open', 'high', 'low', 'close'])
positions = entry_history.copy()
exit_history = pd.DataFrame(columns=['Position_id', 'User_id', 'Sell_order_id', 'Sell_time', 'Sell_price', 'Exit_type'])
failed_orders_history = pd.DataFrame(columns=['Position_id', 'User_id', 'Order_id', 'Symbol', 'Transaction_type', 'Timestamp', 'Status', 'Status_message'])
runtime_errors_history = pd.DataFrame(columns=['Timestamp', 'Line_no', 'Code', 'Error_message'])

# Save DataFrames to CSV files
entry_history.to_csv('data/entry_history.csv', index=False)
positions.to_csv('data/positions.csv', index=False)
exit_history.to_csv('data/trades_history.csv', index=False)
failed_orders_history.to_csv('data/failed_orders_history.csv', index=False)
runtime_errors_history.to_csv('data/runtime_errors_history.csv', index=False)

# Initialize dictionaries for crossover, tsl, previous high, tsl increment, target, and miscellaneous data
crossover = {'CE': dict(), 'PE': dict()}
tsl = {'CE': dict(), 'PE': dict()}
prev_high = {'CE': dict(), 'PE': dict()}
tsl_increment = {'CE': dict(), 'PE': dict()}
target = {'CE': dict(), 'PE': dict()}
misc = {'position_id': 0}

# Initialize dictionaries for each instrument
for inst in INSTRUMENTS:
    for dict_obj in [crossover, tsl, prev_high, tsl_increment, target]:
        dict_obj['CE'][inst] = 0
        dict_obj['PE'][inst] = 0

# Write dictionaries to JSON files
with open("data/crossover.json", "w") as f:
    json.dump(crossover, f)

with open("data/tsl.json", "w") as f:
    json.dump(tsl, f)

with open("data/prev_high.json", "w") as f:
    json.dump(prev_high, f)

with open("data/tsl_increment.json", "w") as f:
    json.dump(tsl_increment, f)

with open("data/target.json", "w") as f:
    json.dump(target, f)

with open("data/misc.json", "w") as f:
    json.dump(misc, f)
