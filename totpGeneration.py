from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
import json
import pyotp
from xtspythonclientapisdk.Connect import XTSConnect

def interactivelogin():
    # URL="http://122.184.68.130:3008//interactive/thirdparty?appKey=93e98b500aaeb837ead698&returnURL=http://122.184.68.130:3008//interactive/testapi#!/logIn"
    URL="https://strade.shareindia.com//interactive/thirdparty?appKey=a743d238d50923fc2dd127&returnURL=https://strade.shareindia.com/interactive/testapi"
    driver = webdriver.Chrome()
    driver.get(URL)
    time.sleep(2)
    search = driver.find_element(by=By.NAME, value="userID")
    search.send_keys("66BP01")
    search.send_keys(Keys.RETURN)
    time.sleep(1)
    driver.find_element(by=By.ID, value="confirmimage").click()
    search = driver.find_element(by=By.ID, value="login_password_field")
    search.send_keys("Rohit@987")
    driver.find_element("xpath", "/html/body/ui-view/div[1]/div/div/div/div[2]/form/div[4]/div[2]/button").click()
    time.sleep(2)
    totpField = driver.find_element(by=By.NAME, value="efirstPin")
    totp = pyotp.TOTP('OZYCSOBXOIQWSLBJKBYVKNZBNUSX2MD2GRRTKOJEJUYXO5KANNDQ')
    TOTP = totp.now()
    time.sleep(2)
    totpField.send_keys(TOTP)
    driver.find_element(by=By.CLASS_NAME, value="PlaceButton").click()
    time.sleep(3)
    json_list = []
    json_list = driver.find_element(By.TAG_NAME,"pre").get_attribute('innerHTML')
    aDict = json.loads(json_list)
    sDict = json.loads(aDict['session'])
    accessToken=sDict['accessToken']
    print("accessToken:",accessToken)

    driver.close()

    xt = XTSConnect(apiKey="a743d238d50923fc2dd127",secretKey="Yvak100@qS",
                    source="WEBAPI",accessToken=accessToken)
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



 


# interactivelogin()