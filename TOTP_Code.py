import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
import json
import pyotp
from xtspythonclientapisdk.Connect import XTSConnect

# Read credentials from CSV
cred_df = pd.read_csv('Credentials.csv')
cred_dict = dict(zip(cred_df['Title'], cred_df['Value']))

# INPUTS REQUIRED
APPKEY = cred_dict.get('Interactive_App_Key', '')
SECRET_KEY = cred_dict.get('Interactive_App_Secret', '')
USERID = '66BP01'
PASSWORD = 'Rohit@987'
TOTP_SECRET = 'OZYCSOBXOIQWSLBJKBYVKNZBNUSX2MD2GRRTKOJEJUYXO5KANNDQ'  # <-- Fill in your TOTP secret here
source = "WEBAPI"
URL = f"https://strade.shareindia.com/interactive/thirdparty?appKey=a743d238d50923fc2dd127&returnURL=https://strade.shareindia.com/interactive/testapi"

# driver = webdriver.Chrome()
# driver.get(URL)
# Set up Chrome in headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless') #to disable chrome opening
chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration as it's not needed in headless mode
driver = webdriver.Chrome(options=chrome_options)
driver.get(URL)
time.sleep(1)
search = driver.find_element(by=By.NAME, value="userID")
search.send_keys(USERID)
search.send_keys(Keys.RETURN)
time.sleep(1)
driver.find_element(by=By.ID, value="confirmimage").click()
search = driver.find_element(by=By.ID, value="login_password_field")
search.send_keys(PASSWORD)
driver.find_element("xpath", '//*[@id="loginPart"]/div/div/div/div[2]/form/div[4]/div[2]/button').click()
time.sleep(2)
totpField = driver.find_element(by=By.NAME, value="efirstPin")
totp = pyotp.TOTP(TOTP_SECRET)
TOTP = totp.now()
totpField.send_keys(TOTP)
driver.find_element(by=By.CLASS_NAME, value="PlaceButton").click()
time.sleep(1)
json_list = []
json_list = driver.find_element(By.TAG_NAME,"pre").get_attribute('innerHTML')
aDict = json.loads(json_list)
sDict = json.loads(aDict['session'])
ACCESS_TOKEN = sDict['accessToken']
driver.close()
print(f"AccessToken: {ACCESS_TOKEN}")

# Initialise
print("SECRET_KEY: ", SECRET_KEY)
print("APPKEY: ", APPKEY)

xt = XTSConnect(APPKEY, SECRET_KEY, source, root="https://strade.shareindia.com/interactive", accessToken=ACCESS_TOKEN)
try:
    response = xt.interactive_login()
    print("response: ", response)
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    print("Login: ", response)
    print(f"UserId: {set_muserID}")
    print(f"Token: {set_marketDataToken}")
except Exception as e:
    print("Error during interactive_login:", e)
    import traceback
    traceback.print_exc()