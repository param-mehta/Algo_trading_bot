# Algorithmic Trading Bot

## Overview

This repository contains an algorithmic trading strategy implemented using the Zerodha Kite Connect API. The strategy aims to automate trading decisions based on predefined conditions and market data analysis.

## Features

- Automated trading based on predefined conditions.
- Integration with Zerodha Kite Connect API for executing trades across multiple accounts.
- Historical data analysis for decision making.
- Supports multiple instruments including futures and options.

## Requirements

To run the algorithmic trading strategy, you need the following:

- Python 3.x
- Zerodha Kite Connect API credentials
- Enable TOTP verification in your kite account
- Required Python packages (specified in `requirements.txt`)

## Installation

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/yourusername/Algo_trading_bot.git
    ```

2. Navigate to the project directory:

    ```bash
    cd algorithmic-trading-strategy
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Configure your Zerodha Kite Connect API credentials in the appropriate configuration files.

## Usage

1. Set up your Zerodha Kite Connect API credentials from https://kite.trade/
2. Enable TOTP verification for your kite account
3. After setting up the environment, run setup.py (do this just once)
4. Every day before the market starts, run access_tokens.py and premarket.py 
5. Run strategy.ipynb to initiate the strategy.


## Configuration

 `config.py`:
- Contains configuration settings such as API keys, account credentials.
 `utils.py`:
- Contains helper functions to place and modify orders, place gtt orders, calculate technical indicators such as bollinger bands and Volume Weighted Average Price.
- It also has functions to fetch historical data and perform error handling.
- While the helper functions are using the Kite Connect's python client, the main strategy code has been written in a way that one can switch to another platform's API with minimal changes.
 `access_tokens.py`:
- This script uses Selenium to automate the process of logging into the account of kite and fetching the access_tokens for multiple accounts.

## Documentation

- Detailed documentation on the implementation of the trading strategy and usage instructions can be found in the `docs` directory.

## Disclaimer

I am not a financial advisor, and the information provided in this repository should not be considered as financial advice or recommendations for trading decisions. Trading in financial markets involves inherent risks, including the risk of substantial losses.

The strategy implemented in this repository is a simple demonstration strategy and may not be suitable for actual trading without further development, testing, and customization. It is not intended to be imitated or used for live trading without thorough understanding, modification, and backtesting.

I am not responsible for any losses incurred as a result of using the information, code, or strategies provided in this repository. Users are solely responsible for their trading decisions and should conduct their own research, analysis, and risk assessment before engaging in any trading activities.

By accessing and using this repository, you agree to release me from any liability for losses or damages that may arise directly or indirectly from the use of the information or code provided herein.

 Happy trading! 📈💼
