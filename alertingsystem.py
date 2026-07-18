import time
import os
import requests
import pandas as pd
import pandas_ta as ta
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = "8621402220:AAFolpupEIOj24CByIOunB9Y_gmx_YWj8Yc"
TELEGRAM_CHAT_ID = "1210174791"
SYMBOL = "BTCUSD"
TIMEFRAME = mt5.TIMEFRAME_M1  # Explicitly set to 1-Minute Timeframe

# Anti-Spam Tracking State
last_alert_time = None  

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Alert Dispatch Failure: {e}")

def initialize_mt5():
    if not mt5.initialize():
        print(f"MT5 Core Error: {mt5.last_error()}")
        return False
    return True

def analyze_market_state():
    global last_alert_time
    
    # Fetch 100 historical M1 bars to establish strong calculation buffers
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    if rates is None or len(rates) == 0:
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate Math Vectors
    df['RSI'] = ta.rsi(df['close'], length=5)
    df['MFI'] = ta.mfi(high=df['high'], low=df['low'], close=df['close'], volume=df['tick_volume'], length=5)

    # ⚠️ CRITICAL STEP FOR 1-MINUTE ANALYSIS:
    # Index -1 is the live, fluctuating open candle. To avoid false entries from temporary price spikes,
    # professionals analyze Index -2 (the most recently *CLOSED* fully-formed candle).
    closed_candle = df.iloc[-2]
    candle_time = closed_candle['time']
    current_rsi = round(closed_candle['RSI'], 2)
    current_mfi = round(closed_candle['MFI'], 2)
    close_price = closed_candle['close']

    # State Check: If we already evaluated this specific candle timestamp, skip execution
    if last_alert_time == candle_time:
        return candle_time

    print(f"│ Analysing Candle: {candle_time} │ Close: {close_price} │ RSI: {current_rsi} │ MFI: {current_mfi} │")

    # Conditional Execution Triggers
    if current_rsi >= 70 and current_mfi >= 80:
        alert_msg = f"🚨 *{SYMBOL} 1M OVERBOUGHT* 🚨\n\n💰 Close Price: {close_price}\n📈 RSI: {current_rsi} (>=70)\n📊 MFI: {current_mfi} (>=80)\n⏰ Time: {candle_time}"
        send_telegram_alert(alert_msg)
        last_alert_time = candle_time  # Lock state

    elif current_rsi <= 20 and current_mfi <= 20:
        alert_msg = f"🚨 *{SYMBOL} 1M OVERSOLD* 🚨\n\n💰 Close Price: {close_price}\n📉 RSI: {current_rsi} (<=20)\n📊 MFI: {current_mfi} (<=20)\n⏰ Time: {candle_time}"
        send_telegram_alert(alert_msg)
        last_alert_time = candle_time  # Lock state
        
    return candle_time

def main():
    if not initialize_mt5():
        return
    
    print("🚀 Event-Driven Engine Active. Syncing to 1-Minute Clock Cycles...")
    
    try:
        while True:
            analyze_market_state()
            
            # 🏁 DRIFT CORRECTION ENGINE: 
            # Dynamically calculate the precise remaining seconds until the exact next minute mark.
            # If current time is 14:05:42, it will sleep for exactly 18 seconds (60 - 42) to hit 14:06:00 perfectly.
            seconds_in_current_minute = time.time() % 60
            sleep_duration = 60 - seconds_in_current_minute
            
            # Add a minor 0.5s padding to guarantee MT5 terminal has finalized the new candle block
            time.sleep(sleep_duration + 0.5)
            
    except KeyboardInterrupt:
        print("\nShutting down session...")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()