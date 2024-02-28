import logging
import json
import time
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pyotp
from config import *

# Configuring logging
logging.basicConfig(level=logging.DEBUG)

# User login details
login_details = {
    USER_ID_1: {
        'api_key': API_KEY_1,
        'api_secret': API_SECRET_1,
        'user_id': USER_ID_1,
        'password': PASSWORD_1,
        'totp_key': TOTP_KEY_1
    }
}


def login(api_key, api_secret, user_id, user_pwd, totp_key):
    """Function to perform user login"""
    # Start Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Navigate to login page
    driver.get(f'https://kite.trade/connect/login?api_key={api_key}&v=3')

    # Fill in user ID
    login_id = WebDriverWait(driver, 10).until(
        lambda x: x.find_element(by=By.XPATH, value='//*[@id="userid"]'))
    login_id.send_keys(user_id)

    # Fill in password
    pwd = WebDriverWait(driver, 10).until(
        lambda x: x.find_element(by=By.XPATH, value='//*[@id="password"]'))
    pwd.send_keys(user_pwd)

    # Click login button
    submit = WebDriverWait(driver, 10).until(lambda x: x.find_element(
        by=By.XPATH,
        value='//*[@id="container"]/div/div/div[2]/form/div[4]/button'))
    submit.click()

    # Wait for OTP input field
    time.sleep(4)
    totp = WebDriverWait(driver, 100).until(lambda x: x.find_element(
        by=By.XPATH,
        value='//*[@id="container"]/div[2]/div/div[2]/form/div[1]/input'))

    # Generate OTP
    authkey = pyotp.TOTP(totp_key)
    totp.send_keys(authkey.now())
    time.sleep(5)

    # Extract request token from URL
    url = driver.current_url
    initial_token = url.split('request_token=')[1]
    request_token = initial_token.split('&')[0]

    # Close WebDriver
    driver.close()

    # Initialize KiteConnect object
    kite = KiteConnect(api_key=api_key)

    # Generate access token
    data = kite.generate_session(request_token, api_secret=api_secret)
    return data['access_token']


access_tokens = dict()

# Perform login for each user and store access token
for user in login_details.keys():
    creds = login_details[user]
    access_tokens[user] = login(*list(creds.values()))

# Write access tokens and login details to JSON files
with open("data/access_tokens.json", "w") as f:
    json.dump(access_tokens, f)

with open("data/login_details.json", "w") as f:
    json.dump(login_details, f)

# Print access tokens
print(access_tokens)
print('*' * 10)
