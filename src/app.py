from datetime import date
from datetime import timedelta
import datetime
import numpy as np
import pandas as pd
import streamlit as st


import random
import json
import time
#from utils import *

st. set_page_config(layout="wide") 
if st.button('refresh'):

    st.subheader('Sorted EMAs')

    st.subheader("Now checking")
    
    with open('data/now_checking.json', "r") as f:
        now_checking = json.load(f)
    for option_symbol in list(now_checking.values()):
        st.text(option_symbol)

    st.subheader("Open positions")
    positions = pd.read_csv('data/positions.csv',usecols=['Symbol','Buy_time','Buy_price','Signal_candle','LTP','Trailing_SL'])
    positions['Buy_price'] = positions['Buy_price'].round(2)

    if len(positions) == 0:
        st.text('No open positions')
    else:
        st.dataframe(positions)

    st.subheader("Open SL Orders")
    sl_orders = pd.read_csv('data/sl_orders.csv')

    if len(sl_orders) == 0:
        st.text('No open SL orders')
    else:
        st.dataframe(sl_orders)
    
    st.subheader("Completed Trades")
    trades = pd.read_csv('data/trades.csv',usecols=['User_id','Symbol','Buy_time','Buy_price','Sell_price','Sell_time','Quantity','Signal_candle'])
    if len(trades) == 0:
        st.text('No completed trades yet')
    else:
        trades = trades[trades['User_id'] == 'BS5128']
        trades['Buy_price'] = trades['Buy_price'].round(2)
        st.dataframe(trades)
    
    st.subheader("Failed orders")
    failed_orders = pd.read_csv('data/failed_orders.csv')
    if len(failed_orders) == 0:
        st.text('No failed orders')
    else:
        st.dataframe(failed_orders)

    st.subheader("Runtime errors")
    runtime_errors = pd.read_csv('data/runtime_errors.csv')
    if len(runtime_errors) == 0:
        st.text('No errors yet')
    else:
        st.dataframe(runtime_errors)