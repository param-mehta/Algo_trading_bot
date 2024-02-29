# Algorithmic Trading Bot

## Overview

This repository contains an algorithmic trading strategy implemented using the Zerodha Kite Connect API. The strategy aims to automate trading decisions based on predefined conditions and market data analysis.

## Features

- Automated trading based on predefined conditions. 
- Execute trades across multiple accounts.
- Historical and live data analysis for decision making.
- Supports multiple instruments including futures and options.
- Deploy complex strategies with a trailing stop loss, detect candlestick patterns like hammer and shooting star, place GTT (good till triggered) orders

## Requirements

To run the trading strategy, you need to do the following:

- Get Zerodha Kite Connect API credentials from https://kite.trade/
- Enable TOTP verification in your kite account
- Install the dependencies as shown below

## Installation

1. Make an environment:

    ```bash
    conda create --name algo_trading python=3.11.7
    ```
    
    ```bash
    conda activate algo_trading
    ```
    
2. Clone the repository and install dependencies:
   
    ```bash
    cd algorithmic-trading-strategy
    ```
    
    ```bash
    git clone https://github.com/yourusername/Algo_trading_bot.git
    ```

    ```bash
    pip install -r requirements.txt
    ```


## Usage

1. Run `bash env.sh` to set environment variables
2. Run `setup.py` (do this just once)
3. Every day before the market starts, run `access_tokens.py` and `premarket.py` 
4. Run `strategy.py` to deploy the strategy
5. Run `streamlit run app.py` to monitor your trades


## Guide

`utils.py`: 

This contains helper functions to:
- Place and modify normal orders, stop loss orders or gtt orders
- Calculate technical indicators such as bollinger bands and Volume Weighted Average Price
- Fetch historical data and perform error handling

While the helper functions are using the Kite Connect's python client, the main strategy code has been written in a way that one can switch to another platform's API with minimal changes.

`setup.py`:

This script initializes the data structures and files needed to store trade details and trading parameters relevant to the strategy. 

`access_tokens.py`:

This script uses Selenium to automate the process of logging into the account of kite and fetching the access_tokens for multiple accounts.

`premarket.py`:

This script fetches daily instrument data and initializes files to store trade details and strategy paramters for a single trading session

`strategy.py`:

This script contains the main strategy loop that checks conditions, executes trades and updates the trailing stop loss. The script stops running when either the max no. of cycles is reached or when the trading session concludes. 

`app.py`: 

This contains a simple streamlit dashboard that displays the open positions, completed orders, failer orders and runtime errors.



## Disclaimer

I am not a financial advisor, and the information provided in this repository should not be considered as financial advice or recommendations for trading decisions. Trading in financial markets involves inherent risks, including the risk of substantial losses.

The strategy implemented in this repository is a simple demonstration strategy and may not be suitable for actual trading without further development, testing, and customization. It is not intended to be imitated or used for live trading without thorough understanding, modification, and backtesting.

I am not responsible for any losses incurred as a result of using the information, code, or strategies provided in this repository. Users are solely responsible for their trading decisions and should conduct their own research, analysis, and risk assessment before engaging in any trading activities.

By accessing and using this repository, you agree to release me from any liability for losses or damages that may arise directly or indirectly from the use of the information or code provided herein.

 Happy trading! 📈💼
