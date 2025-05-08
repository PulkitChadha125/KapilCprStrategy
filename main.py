import pandas as pd
import datetime  # full module
import polars as pl
import polars_talib as plta
import json
# from datetime import datetime, timedelta
import time
import traceback
import sys
# Ensure the SDK path is included for import
sys.path.append('.')
# Now import the SDK
from xtspythonclientapisdk.Connect import XTSConnect
instrument_id_list=[]
result_dict = {}
xts_marketdata = None
xt=None




def interactivelogin():
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    import time
    from selenium.webdriver.common.by import By
    import json
    import pyotp
    from xtspythonclientapisdk.Connect import XTSConnect

    global xt
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



 

#  INTERAACTIVE LOGIN ABOVE

def place_order(nfo_ins_id,order_quantity,order_side,price,unique_key):
    val=None
    if order_side == "BUY":
        val=xt.TRANSACTION_TYPE_BUY
    elif order_side == "SELL":
        val=xt.TRANSACTION_TYPE_SELL

        
    response=xt.place_order (
        exchangeSegment=xt.EXCHANGE_NSEFO,
        exchangeInstrumentID=nfo_ins_id,
        productType=xt.PRODUCT_MIS,
        orderType=xt.ORDER_TYPE_LIMIT,
        orderSide=val,
        timeInForce=xt.VALIDITY_DAY,
        disclosedQuantity=0,
        orderQuantity=order_quantity,
        limitPrice=price,
        stopPrice=0,
        apiOrderSource="WEBAPI",
        orderUniqueIdentifier="454845",
        clientID="66BP01" )

    print("Place Order: ", response)
    write_to_order_logs(f"Broker Order Response: [{datetime.datetime.now()}]  {order_side} quantity: {order_quantity} price: {price} response: {response}")
    print("-" * 50) 
    write_to_order_logs("-" * 50)
    

def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')

def get_user_settings():
    global result_dict, instrument_id_list
    try:
        csv_path = 'TradeSettings.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()

        result_dict = {}
        instrument_id_list = []

        for index, row in df.iterrows():
            symbol = row['Symbol']
            expiry = row['EXPIERY']  # Format: 29-05-2025

            # Convert expiry to API format: DDMonYYYY (e.g., 29May2025)
            expiry_api_format = datetime.datetime.strptime(expiry, "%d-%m-%Y").strftime("%d%b%Y")

            # Fetch FUTSTK instrument ID
            fut_response = xts_marketdata.get_future_symbol(
                exchangeSegment=2,      # NSEFO
                series='FUTSTK',
                symbol=symbol,
                expiryDate=expiry_api_format
            )

            # print(f"fut_response: {fut_response}")
            

            if fut_response['type'] == 'success' and 'result' in fut_response:
                result_item = fut_response['result'][0]
                NSEFOinstrument_id = int(result_item['ExchangeInstrumentID'])
                lot_size = int(result_item.get('LotSize', 0))
                # print(f"lot_size: {lot_size}")

            else:
                print(f"[ERROR] Could not get FUTSTK instrument ID for {symbol} {expiry_api_format}")
                NSEFOinstrument_id = None
                lot_size = None

            # Fetch EQ instrument ID (NSECM)
            eq_response = xts_marketdata.get_equity_symbol(
                exchangeSegment=1,      # NSECM
                series='EQ',
                symbol=symbol
            )

            if eq_response['type'] == 'success' and 'result' in eq_response:
                NSECMinstrument_id = int(eq_response['result'][0]['ExchangeInstrumentID'])
            else:
                print(f"[ERROR] Could not get EQ instrument ID for {symbol}")
                NSECMinstrument_id = None

            symbol_dict = {
                "Symbol": symbol,"unique_key" : f"{symbol}_{expiry}",
                "Expiry": expiry,
                "Quantity": int(row['Quantity']),"LotSize": lot_size,
                "Timeframe": int(row['Timeframe']),
                "MA1": int(row['MA1']),"MA2": int(row['MA2']),'RSI_Period':int(row['RSI_Period']),'RSI_Buy':int(row['RSI_Buy']),
                "RSI_Sell":int(row['RSI_Sell']),'TargetBuffer':float(row['TargetBuffer']),
                "StartTime": datetime.datetime.strptime(row["StartTime"], "%H:%M:%S").time(),
                "StopTime": datetime.datetime.strptime(row["Stoptime"], "%H:%M:%S").time(),
                "PercentagePrice": float(row['PercentagePrice']), "PerVal": None, "TakeTrade": None,
                "NSEFOexchangeInstrumentID": NSEFOinstrument_id,
                "NSECMexchangeInstrumentID": NSECMinstrument_id,"PrevOpen": None,"PrevHigh": None,"OrderQuantity":None,
                "PrevLow": None,"PrevClose": None,"ma1Val": None,"ma2Val": None,"RsiVal":None,"last_run_time": None,
                "PvtPoint": None,"BottomRange": None,"TopRange": None,"R1": None,"R2": None,"R3": None,"last_close":None,
                "S1": None,"S2": None,"S3": None,"AllowedDiff":None,"ActualDiff":None,"Trade":None,"TargetExecuted":False,"ltp":None
            }

            result_dict[symbol_dict["unique_key"]] = symbol_dict


            if NSEFOinstrument_id:
                instrument_id_list.append({
                    "exchangeSegment": 2,
                    "exchangeInstrumentID": NSEFOinstrument_id
                })

        print("result_dict: ", result_dict)
        print("instrument_id_list: ", instrument_id_list)

    except Exception as e:
        print("Error happened in fetching symbol", str(e))


def get_api_credentials():
    credentials = {}
    try:
        df = pd.read_csv('Credentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))
    return credentials




def format_date_time(date_time):
    """
    Format datetime object to required format: MMM DD YYYY HHMMSS
    """
    return date_time.strftime("%b %d %Y %H%M%S")

RUN_INTERVAL_SECONDS=None

def login_marketdata_api():
    """
    Login to the Market Data API and return the XTSConnect object.
    """
    global xts_marketdata
    global RUN_INTERVAL_SECONDS
    try:
        credentials = get_api_credentials()
        RUN_INTERVAL_SECONDS = int(credentials.get("RunInterval", 180))
        source = "WEBAPI"
        market_data_app_key = credentials.get("Market_Data_API_App_Key")
        market_data_app_secret = credentials.get("Market_Data_API_App_Secret")
        
        if not market_data_app_key or not market_data_app_secret:
            print("Missing Market Data API credentials in Credentials.csv")
            return None
            
        xts_marketdata = XTSConnect(market_data_app_key, market_data_app_secret, source,accessToken=None)
        response = xts_marketdata.marketdata_login()
        print("Market Data Login Response:", response)
        
        if response and 'result' in response:
            print("Market Data login successful")
            return xts_marketdata
        else:
            print("Market Data login failed")
            return None
            
    except Exception as e:
        print(f"Error during market data login: {str(e)}")
        traceback.print_exc()
        return None



def fetch_historical_ohlc(xts_marketdata, exchangeSegment, exchangeInstrumentID, startTime, endTime, compressionValue):
    """
    Fetch and format historical OHLC data for a given instrument
    Returns a pandas DataFrame with columns: [Timestamp, Open, High, Low, Close, Volume, oi]
    """
    try:
        response = xts_marketdata.get_ohlc(
            exchangeSegment=exchangeSegment,
            exchangeInstrumentID=exchangeInstrumentID,
            startTime=startTime,
            endTime=endTime,
            compressionValue=compressionValue
        )

        if response['type'] == 'success' and 'result' in response:
            raw_data = response['result'].get('dataReponse', '')
            if not raw_data:
                print("No OHLC data found.")
                return None

            data_list = raw_data.strip().split(',')
            split_data = [item.split('|')[:-1] for item in data_list]

            df = pd.DataFrame(split_data, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])

            # Convert data types
            df = df.astype({
                'Timestamp': int,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int,
                'oi': int
            })

            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')

            # print(df.head())  # Display first few rows
            return df

        else:
            print("OHLC API returned no data or an error.")
            return None

    except Exception as e:
        print(f"Error fetching OHLC data: {str(e)}")
        traceback.print_exc()
        return None

def get_previous_day_ohlc(symbol, instrument_id):
    try:
        today = datetime.datetime.now().date()
        start = datetime.datetime.now() - datetime.timedelta(days=10)
        end = datetime.datetime.now()

        df = fetch_historical_ohlc(
            xts_marketdata,
            exchangeSegment="NSECM",
            exchangeInstrumentID=instrument_id,
            startTime=format_date_time(start),
            endTime=format_date_time(end),
            compressionValue=60 # 1-min data
        )
        if df is None or df.empty:
            print(f"No historical data available for {symbol}")
            return None, None, None, None
        
        
        df.columns = [col.lower() for col in df.columns]
        # Reverse the dataframe
        df_reversed = df.iloc[::-1]

        # Find first row whose date is not today
        for idx, row in df_reversed.iterrows():
            row_date = row['timestamp'].date()
            if row_date != today:
                target_date = row_date
                break
        else:
            print(f"No previous day data found for {symbol}")
            return None, None, None, None

        # Extract all rows for the target_date
        df_day = df[df['timestamp'].dt.date == target_date]

        if df_day.empty:
            print(f"No rows found for previous day {target_date}")
            return None, None, None, None

        open_ = df_day.iloc[0]['open']
        high = df_day['high'].max()
        low = df_day['low'].min()
        close = df_day.iloc[-1]['close']

        print(f"[{symbol}] Previous day ({target_date}) OHLC => O:{open_}, H:{high}, L:{low}, C:{close}")
        return open_, high, low, close

    except Exception as e:
        print(f"Failed fetching previous OHLC for {symbol}: {str(e)}")
        traceback.print_exc()
        return None, None, None, None


def chunk_instruments(instrument_list, chunk_size=50):
    for i in range(0, len(instrument_list), chunk_size):
        yield instrument_list[i:i + chunk_size]

    


def fetch_MarketQuote(xts_marketdata):
    global instrument_id_list, result_dict

    if not instrument_id_list:
        print("Instrument list is empty, skipping quote fetch.")
        return

    # Mapping: InstrumentID → Symbol
    symbol_by_id = {
    params.get("NSEFOexchangeInstrumentID"): (symbol, params)
    for symbol, params in result_dict.items()
    if params.get("NSEFOexchangeInstrumentID") and params.get("TakeTrade") == True
        }



    for chunk in chunk_instruments(instrument_id_list, 50):
        try:
            response = xts_marketdata.get_quote(
                Instruments=chunk,
                xtsMessageCode=1501,
                publishFormat='JSON'
            )

            if response and response.get("type") == "success":
                quote_strings = response["result"].get("listQuotes", [])

                for quote_str in quote_strings:
                    try:
                        item = json.loads(quote_str)
                        instrument_id = item.get("ExchangeInstrumentID")

                        if instrument_id in symbol_by_id:
                            symbol, params = symbol_by_id[instrument_id]
                            ltp = item.get("LastTradedPrice")
                            params["ltp"] = int(ltp)  # ✅ Now valid and consistent
                            print(f"[params[ltp]] {symbol}: {params["ltp"]}")

                    except Exception as inner_err:
                        print(f"[WARN] Skipping malformed quote: {inner_err}")
                        continue
            else:
                print(f"[ERROR] Unexpected quote response: {response}")

        except Exception as e:
            print(f"[ERROR] While fetching quote chunk: {e}")
            traceback.print_exc()




allowed_trades_saved = False


def main_strategy():
    global allowed_trades_saved
    try:
        global xts_marketdata
        
        if not xts_marketdata:
            print("Market Data API not initialized")
            return
            
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=10)

        start_time_str = start_date.strftime("%b %d %Y 090000")
        end_time_str = end_date.strftime("%b %d %Y 153000")

        now = datetime.datetime.now()
        now_time = now.time()
        
        # print(f"\nFetching data from {start_time_str} to {end_time_str}")
        
        # Process each symbol from TradeSettings.csv
        for unique_key, params in result_dict.items():
            # initialize loop-specific variables to avoid UnboundLocalError
            symbol_name = params["Symbol"]
            last_close = None
            fetch_duration = 0.0
            
            # if not (params["StartTime"] <= now_time <= params["StopTime"]):
            #     continue

            if params.get("PrevOpen") is None:
                try:
                    start_time = datetime.datetime.now()
                    o, h, l, c = get_previous_day_ohlc(symbol_name, params["NSECMexchangeInstrumentID"])
                    if None in (o, h, l, c):
                        print(f"[WARN] Incomplete OHLC data for {symbol_name}. Retrying in 1 second...")
                        time.sleep(1)
                        o, h, l, c = get_previous_day_ohlc(symbol_name, params["NSECMexchangeInstrumentID"])

                        if None in (o, h, l, c):
                            print(f"[ERROR] OHLC data still missing for {symbol_name}. Skipping...")
                            with open("OrderLog.txt", "a") as log_file:
                                log_file.write(f"[{datetime.datetime.now()}] OHLC data not found for {symbol_name}\n")
                            continue  # move to next symbol

                     # Store OHLC
                    params["PrevOpen"] = o
                    params["PrevHigh"] = h
                    params["PrevLow"] = l
                    params["PrevClose"] = c

                    # Calculated values
                    close = c
                    allowed_diff = close * params["PercentagePrice"] / 100
                    pivot = (h + l + c) / 3
                    top = (h + l) / 2
                    bottom = (pivot - top) + pivot
                    diff_c_b = abs(pivot - bottom)
                    diff_t_c = abs(top - pivot)

                    params["ActualDiff_Pivot_Bottom"] = diff_c_b
                    params["ActualDiff_Top_Pivot"] = diff_t_c
                    params["PvtPoint"] = pivot
                    params["BottomRange"] = bottom
                    params["TopRange"] = top
                    params["AllowedDiff"] = allowed_diff

                # TakeTrade condition
                    params["TakeTrade"] = diff_c_b < allowed_diff and diff_t_c < allowed_diff

                # Support/Resistance
                    params["R1"] = (2 * pivot) - l
                    params["R2"] = pivot + (h - l)
                    params["R3"] = h + 2 * (pivot - l)
                    params["S1"] = (2 * pivot) - h
                    params["S2"] = pivot - (h - l)
                    params["S3"] = l - 2 * (h - pivot)

                    endtime=datetime.datetime.now()
                    latency=endtime-start_time
                    print(f"Latency for {symbol_name}: {latency}")

                except Exception as e:
                    print(f"Error fetching previous OHLC for {symbol_name}: {str(e)}")
                    traceback.print_exc()
                    continue
            
            
            # Skip if not yet time to run based on timeframe
            # last_run = params.get("last_run_time")
            # if last_run and (now - last_run).total_seconds() < timeframe:
            #     continue

        fetch_MarketQuote(xts_marketdata)   
        fetch_start = time.time()

        
        for unique_key, params in result_dict.items():
            if not (params["StartTime"] <= now_time <= params["StopTime"]):
                continue

            if params.get("TakeTrade") != True:
                continue    

            

            #               Run only if the current time has crossed the next scheduled fetch time
           
            if params.get("last_run_time") is None or datetime.datetime.now() >= params["last_run_time"]:
                try:
                    symbol_name = params["Symbol"]
                    NSECMinstrument_id = params["NSECMexchangeInstrumentID"]
                    timeframe = params["Timeframe"]
                    # params["last_run_time"] = now
                    # Fetch historical data
                    if params["TakeTrade"] == True:
                        ohlc_data = fetch_historical_ohlc(
                                xts_marketdata=xts_marketdata,
                            exchangeSegment="NSECM",
                        exchangeInstrumentID=NSECMinstrument_id,
                        startTime=start_time_str,
                        endTime=end_time_str,
                        compressionValue=timeframe
                        )

                        
                    

                except Exception as e:
                    print(f"Error fetching OHLC data for {symbol_name}: {str(e)}")
                    traceback.print_exc()
                    continue
                    
                if ohlc_data is not None and not ohlc_data.empty:
                    print(f"Successfully fetched OHLC data for {symbol_name}:")
                    # print("ohlc_data: ", ohlc_data)
                    
                else:
                    print(f"Failed to fetch data for {symbol_name}")

                ohlc_data.columns = [col.lower() for col in ohlc_data.columns]
                    # Convert pandas OHLC to polars
                pl_df = pl.from_pandas(ohlc_data)

                    # Calculate EMA using values from settings (MA1 and MA2)
                pl_df = pl_df.with_columns([
                        pl.col("close").ta.ema(int(params["MA1"])).alias(f"ema_{params['MA1']}"),
                        pl.col("close").ta.ema(int(params["MA2"])).alias(f"ema_{params['MA2']}"),
                        pl.col("close").ta.rsi(int(params["RSI_Period"])).alias("rsi_14")
                    ])
                
                    # Save last EMA values into result_dict
                params["ma1Val"] = pl_df.select(f"ema_{params['MA1']}")[-1, 0]
                params["ma2Val"] = pl_df.select(f"ema_{params['MA2']}")[-1, 0]
                params["RsiVal"] = pl_df.select("rsi_14")[-1, 0]
                params["last_close"] = pl_df.select("close")[-2, 0]
                 
                    # Show first few rows
                fetch_end = time.time()
                fetch_duration = fetch_end - fetch_start
                params["last_run_time"] = datetime.datetime.now() + datetime.timedelta(seconds=(params["Timeframe"] - (fetch_end - fetch_start)))
                # print fetch timing and last close right after fetch
                print(f"Symbol: {symbol_name}, Next run time: {params['last_run_time']}, Total Time taken by api to fetch data: {fetch_duration:.2f} seconds")
                print(f"last_close: {params['last_close']}")
            
            

            # Get required values
            # ✅ Last candle close
            ema1 = params["ma1Val"]       # ✅ EMA1 value
            ema2 = params["ma2Val"]       # ✅ EMA2 value
            rsi_val = params["RsiVal"]
            prev_high = params["PrevHigh"]
            prev_low = params["PrevLow"]
            r1 = params["R1"]
            r2 = params["R2"]
            s1 = params["S1"]
            s2 = params["S2"]

            target_buffer = params["TargetBuffer"] 
            buytargetvalue = r2 * target_buffer*0.01 
            buytargetvalue = r2-buytargetvalue

            selltargetvalue = s2 * target_buffer*0.01 
            selltargetvalue = s2+selltargetvalue
            params["OrderQuantity"]= int(params["Quantity"]*params["LotSize"])


            print(f"""
                    Symbol: {params['Symbol']}
                    Order Quantity: {params['OrderQuantity']}
                    EMA1: {ema1}
                    EMA2: {ema2}
                    RSI Value: {rsi_val}
                    Previous High: {prev_high}
                    Previous Low: {prev_low}
                    Resistance 1 (R1): {r1}
                    Resistance 2 (R2): {r2}
                    Support 1 (S1): {s1}
                    Support 2 (S2): {s2}
                    Target Buffer: {target_buffer}
                    Buy Target Value: {buytargetvalue}
                    Sell Target Value: {selltargetvalue}
                    Last Close: {params["last_close"]}
                    LTP: {params['ltp']}
                    """)
            print("-" * 50)  # dashed line separator


                # Target
            if( params["ltp"] is not None and 
               (params['ltp']>=buytargetvalue or params["last_close"]>=buytargetvalue ) and 
               params["TargetExecuted"] == None):
                print(f"[{params['Symbol']}] price reached buytargetvalue {buytargetvalue}")
                params["TargetExecuted"] = True
                write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} buytargetvalue REACHED close: {params["last_close"]}, buytargetvalue: {buytargetvalue}")
                if params["Trade"] == "BUY":
                    print(f"[{params['Symbol']}] Buy Target  executed")
                    params["Trade"] = "TAKENOMORETRADES"
                    # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="SELL",price=params["ltp"],unique_key="1234")
                    write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} BUY TARGET REACHED clos: {params["last_close"]}, buytargetvalue: {buytargetvalue}")

            if (params["ltp"] is not None and
            (params['ltp']<=selltargetvalue or params["last_close"]<=selltargetvalue) and 
            params["TargetExecuted"] == None):
                print(f"[{params['Symbol']}] price reached selltargetvalue")
                params["TargetExecuted"] = True
                write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} selltargetvalue REACHED close: {params["last_close"]}, selltargetvalue: {selltargetvalue}")
                if params["Trade"] == "SELL":
                    print(f"[{params['Symbol']}] Sell Target  executed")
                    params["Trade"] = "TAKENOMORETRADES"
                    # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="BUY",price=params["ltp"],unique_key="1234")
                    
                    write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} SELL TARGET REACHED close: {params["last_close"]}, selltargetvalue: {selltargetvalue}")
                
                
                
            if params["TargetExecuted"] == False:
                    #  buy condition
                if (params["TakeTrade"] == True and params["last_close"] > ema1 and
                    params["last_close"] > ema2 and params["last_close"] > r1 and
                    params["last_close"]>prev_high and ema1>ema2) and params["Trade"] == None:
                    print(f"[{params['Symbol']}] Buy condition met")
                    params["Trade"] = "BUY"
                    # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="BUY",price=params["ltp"],unique_key="1234")
                    write_to_order_logs(f"[{datetime.datetime.now()}] BUY @ {params['Symbol']}  {params["last_close"]}")

                    # sell condition
                if (params["TakeTrade"] == True and params["last_close"] < ema1 and params["last_close"] < ema2 and
                    params["last_close"] < s1 and params["last_close"]<prev_low and ema1<ema2) and params["Trade"] == None:
                    print(f"[{params['Symbol']}] Sell condition met")
                    params["Trade"] = "SELL"
                    # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="SELL",price=params["ltp"],unique_key="1234")
                    write_to_order_logs(f"[{datetime.datetime.now()}] SELL @ {params['Symbol']}  {params["last_close"]}")

                # REENTRY TRIGGERED LOGIC
            if params["Trade"] == "BUYSTOPLOSS":
                if (params["TakeTrade"] == True and params["last_close"] > ema1 and params["last_close"] > ema2 and
                    params["last_close"] > r1 and params["last_close"]>prev_high and ema1>ema2) :
                        print(f"[{params['Symbol']}] Buy re-entry condition met")
                        params["Trade"] = "BUY"
                        # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="BUY",price=params["ltp"],unique_key="1234")
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} BUY re-entry {params['last_close']}")
                    
                if params["Trade"] == "SELLSTOPLOSS":
                    if (params["TakeTrade"] == True and params["last_close"] < ema1 and params["last_close"] < ema2 and
                        params["last_close"] < s1 and params["last_close"]<prev_low and ema1<ema2) :
                        print(f"[{params['Symbol']}] Sell re-entry condition met")
                        params["Trade"] = "SELL"
                        # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="SELL",price=params["ltp"],unique_key="1234")
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} SELL re-entry {params["last_close"]}")


                    # Stoploss  
                if params["Trade"] == "BUY":
                    if params["last_close"] < ema1 and rsi_val <= params["RSI_Buy"]:
                        print(f"[{params['Symbol']}]Buy Stoploss executed")
                        params["Trade"] = "BUYSTOPLOSS"
                        # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="SELL",
                        #             price=params["ltp"],unique_key="1234")  
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} BUY Stoploss {params["last_close"]}")


                if params["Trade"] == "SELL":
                    if params["last_close"] > ema1 and rsi_val >= params["RSI_Sell"]:
                        print(f"[{params['Symbol']}]Sell Stoploss executed")
                        params["Trade"] = "SELLSTOPLOSS"
                        # place_order(nfo_ins_id=params["NSEFOexchangeInstrumentID"],order_quantity=params["OrderQuantity"],order_side="BUY",price=params["ltp"],unique_key="1234")
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} SELL Stoploss {params["last_close"]}")


                    # REENTERY LOGIC
                if params["Trade"] == "BUYSTOPLOSS":
                    if params["last_close"] > min(prev_high,r1):
                        print(f"[{params['Symbol']}]Price below both prev_day_high and r1, checking for buy re-entry")
                        params["Trade"] = "BUY"
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} BUY Reentry {params["last_close"]}")

                if params["Trade"] == "SELLSTOPLOSS":
                    if params["last_close"] < max(prev_low,s1):
                        print(f"[{params['Symbol']}]Price above both prev_day_low and s1, checking for sell re-entry")
                        params["Trade"] = "SELL"
                        write_to_order_logs(f"[{datetime.datetime.now()}] {params['Symbol']} SELL Reentry {params["last_close"]}")

                    
        



                # Optional: print last row with EMAs
                # print(pl_df.tail(5))
                # pl_df.write_csv(f"{symbol_name}.csv")

                # ltp= fetch_MarketQuote(xts_marketdata)
                # print(f"ltp {symbol_name}: ", ltp)
            
            # print("result_dict: ", result_dict)
        if not allowed_trades_saved:
            allowed_trades = []

            for symbol, params in result_dict.items():
                if params.get("TakeTrade") == True:
                    allowed_trades.append({
                    "Symbol":params["Symbol"],
                    "PrevOpen" : params["PrevOpen"],
                    "PrevHigh": params["PrevHigh"],
                    "PrevLow": params["PrevLow"],
                    "PrevClose": params["PrevClose"],
                    # "PerVal": params["PerVal"],
                    "PvtPoint": params["PvtPoint"],
                    "BottomRange": params["BottomRange"],
                    "TopRange": params["TopRange"],
                    "ActualDiff_Pivot_Bottom": params["ActualDiff_Pivot_Bottom"],
                    "ActualDiff_Top_Pivot": params["ActualDiff_Top_Pivot"],
                    "AllowedDiff": params["AllowedDiff"],
                    "R1": params["R1"],
                    "R2": params["R2"],
                    "R3": params["R3"],
                    "S1": params["S1"],
                    "S2": params["S2"],
                    "S3": params["S3"]
                })

            if allowed_trades:
                df = pd.DataFrame(allowed_trades)
                df.to_csv("AllowedTrades.csv", index=False)
                print("[✅] AllowedTrades.csv saved with tradeable symbols.")
                allowed_trades_saved = True  # ✅ Prevent saving again
            else:
                # allowed_trades_saved = True
                print("[ℹ️] No TakeTrade=True found. Skipping AllowedTrades.csv.")
            
    except Exception as e:
        print("Error in main strategy:", str(e))
        traceback.print_exc()

if __name__ == "__main__":
    # # Initialize settings and credentials
    #   # <-- Add this line
    
    get_api_credentials()
    xts_marketdata = login_marketdata_api()
    interactivelogin()
    

    get_user_settings()
    # fetch_MarketQuote(xts_marketdata)

    
    # Initialize Market Data API
    
    if xts_marketdata:
        while True:
            now = datetime.datetime.now()
            print(f"\nStarting main strategy at {datetime.datetime.now()}")
            main_strategy()
            time.sleep(2)
    else:
        print("Failed to initialize Market Data API. Exiting...")
