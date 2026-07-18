import threading
import time
import requests
import pandas as pd
import pandas_ta as ta
import MetaTrader5 as mt5
import customtkinter as ctk
from tkinter import ttk
import queue
import os
import csv

# Professional Financial & Audio Toolkits
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Configuration Settings
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M1

# Global State Management Ledgers
last_alert_time = None
is_running = False
mock_balance = 10000.00
mock_equity = 10000.00

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except Exception as e: print(f"Alert Error: {e}")

# --- BACKEND MULTI-FACTOR ENGINE THREAD ---
def trading_engine_loop(config, data_queue, add_signal_callback, log_callback):
    global last_alert_time, is_running
    
    if not mt5.initialize():
        log_callback(f"❌ MT5 Link Failed: {mt5.last_error()}")
        is_running = False
        return

    log_callback("🚀 Production Multithreaded Core Engine Ingesting Market Blocks.")
    
    while is_running:
        try:
            max_period = max([config['rsi_len'], config['mfi_len'], config['ema_len'], 50]) + 50
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, max_period)
            if rates is None or len(rates) == 0:
                time.sleep(1)
                continue

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'}, inplace=True)
            df.set_index('time', inplace=True)
            
            val_rsi, val_mfi, val_ema = "OFF", "OFF", "OFF"
            
            # 1. Component Multi-Indicator Math Allocations
            if config['use_rsi']:
                df['RSI'] = ta.rsi(df['Close'], length=config['rsi_len'])
                if not df['RSI'].isna().iloc[-2]: val_rsi = round(df['RSI'].iloc[-2], 2)
            if config['use_mfi']:
                df['MFI'] = ta.mfi(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'], length=config['mfi_len'])
                if not df['MFI'].isna().iloc[-2]: val_mfi = round(df['MFI'].iloc[-2], 2)
            if config['use_ema']:
                df['EMA'] = ta.ema(df['Close'], length=config['ema_len'])
                if not df['EMA'].isna().iloc[-2]: val_ema = round(df['EMA'].iloc[-2], 2)

            closed_candle = df.iloc[-2]
            candle_time = df.index[-2]
            close_price = closed_candle['Close']

            # Keep a slice of the tail for charting
            chart_df = df.tail(30).copy()
            
            # Send data frame array across thread queue structures
            data_queue.put((close_price, val_rsi, val_mfi, val_ema, chart_df))

            # 2. Strategy Matrix Evaluation Logic
            if last_alert_time != candle_time:
                overbought = True
                oversold = True
                
                if config['use_rsi']:
                    if val_rsi == "OFF" or val_rsi < config['rsi_ob']: overbought = False
                    if val_rsi == "OFF" or val_rsi > config['rsi_os']: oversold = False
                if config['use_mfi']:
                    if val_mfi == "OFF" or val_mfi < config['mfi_ob']: overbought = False
                    if val_mfi == "OFF" or val_mfi > config['mfi_os']: oversold = False
                if config['use_ema']:
                    if val_ema == "OFF" or close_price <= val_ema: overbought = False
                    if val_ema == "OFF" or close_price >= val_ema: oversold = False

                if (overbought or oversold) and (config['use_rsi'] or config['use_mfi']):
                    condition = "OVERBOUGHT" if overbought else "OVERSOLD"
                    
                    # Target Actions triggered based on runtime configs checkboxes
                    if config['alert_tele']:
                        msg = f"🚨 *{SYMBOL} MATRIX {condition}* \nPx: {close_price}\nRSI: {val_rsi}\nMFI: {val_mfi}"
                        send_telegram_alert(msg)
                    
                    if config['alert_audio']:
                        print('\a') # System standard console hardware beep signal
                        
                    if config['alert_csv']:
                        with open("audit_signals_log.csv", "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([candle_time, condition, close_price, val_rsi, val_mfi])

                    add_signal_callback(candle_time.strftime('%H:%M:%S'), condition, close_price, val_rsi, val_mfi)
                    last_alert_time = candle_time

            seconds_in_minute = time.time() % 60
            time.sleep((60 - seconds_in_minute) + 0.5)

        except Exception as err:
            log_callback(f"⚠️ Core Loop Deviation Exception: {err}")
            time.sleep(2)

    mt5.shutdown()

# --- FOREGROUND MASTER WORKSPACE CLIENT UI ---
class TradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Alpha Engine - Professional Multi-Asset Terminal Workstation")
        self.geometry("1400x820")
        ctk.set_appearance_mode("dark")
        
        self.ui_queue = queue.Queue()
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=26)
        style.map("Treeview", background=[('selected', '#1f538d')])

        # Structural Layout Panels Mappings
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="#18181b")
        self.sidebar.pack(side="left", fill="y")
        
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(side="right", expand=True, fill="both", padx=15, pady=15)

        self.setup_sidebar_controls()
        self.setup_analytical_workspace()
        self.process_queue_feed()

    def setup_sidebar_controls(self):
        # Header Parameter Configurations Panel Label
        ctk.CTkLabel(self.sidebar, text="⚙️ STRATEGY BASE MATRIX", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3a86ff").pack(pady=(15, 5), padx=20, anchor="w")

        # RSI Configuration UI Container Rows
        self.chk_rsi = ctk.CTkCheckBox(self.sidebar, text="Enable RSI Matrix", text_color="white")
        self.chk_rsi.select()
        self.chk_rsi.pack(anchor="w", padx=20, pady=4)
        f_rsi = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        f_rsi.pack(fill="x", padx=20, pady=2)
        self.in_rsi_len = self.add_small_input(f_rsi, "Len", "5")
        self.in_rsi_ob = self.add_small_input(f_rsi, "OB", "70")
        self.in_rsi_os = self.add_small_input(f_rsi, "OS", "20")

        # MFI Configuration UI Container Rows
        self.chk_mfi = ctk.CTkCheckBox(self.sidebar, text="Enable MFI Matrix", text_color="white")
        self.chk_mfi.select()
        self.chk_mfi.pack(anchor="w", padx=20, pady=10)
        f_mfi = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        f_mfi.pack(fill="x", padx=20, pady=2)
        self.in_mfi_len = self.add_small_input(f_mfi, "Len", "5")
        self.in_mfi_ob = self.add_small_input(f_mfi, "OB", "80")
        self.in_mfi_os = self.add_small_input(f_mfi, "OS", "20")

        # EMA Trend Parameters UI Container
        self.chk_ema = ctk.CTkCheckBox(self.sidebar, text="Enable EMA Overlay", text_color="white")
        self.chk_ema.select()
        self.chk_ema.pack(anchor="w", padx=20, pady=10)
        self.in_ema_len = self.add_small_input(self.sidebar, "EMA Analysis Target Period Length", "20", inline=False)

        # 🔔 NOTIFICATION SYSTEM INTEGRATION SETTINGS
        ctk.CTkLabel(self.sidebar, text="🔔 DISPATCH EVENT CONTROLS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ff006e").pack(pady=(15, 5), padx=20, anchor="w")
        self.chk_tele = ctk.CTkCheckBox(self.sidebar, text="Push Telegram Bot Webhooks", text_color="gray")
        self.chk_tele.select()
        self.chk_tele.pack(anchor="w", padx=20, pady=3)
        self.chk_audio = ctk.CTkCheckBox(self.sidebar, text="Trigger System Hardware Beep", text_color="gray")
        self.chk_audio.pack(anchor="w", padx=20, pady=3)
        self.chk_csv = ctk.CTkCheckBox(self.sidebar, text="Write Records to Local CSV Logs", text_color="gray")
        self.chk_csv.pack(anchor="w", padx=20, pady=3)

        # 📊 ACCOUNT MANAGEMENT SIMULATION ORDER EXECUTIONS PANEL
        ctk.CTkLabel(self.sidebar, text="💼 TRANSACTION EXECUTION BLOCK", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2a9d8f").pack(pady=(20, 5), padx=20, anchor="w")
        f_order = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        f_order.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(f_order, text="BUY Market", fg_color="#2a9d8f", hover_color="#1e7166", command=lambda: self.execute_mock_order("BUY"), font=ctk.CTkFont(weight="bold")).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(f_order, text="SELL Market", fg_color="#e63946", hover_color="#b22c36", command=lambda: self.execute_mock_order("SELL"), font=ctk.CTkFont(weight="bold")).pack(side="right", expand=True, padx=2)

        # Primary Master Lifecycle Trigger Action Button
        self.btn_toggle = ctk.CTkButton(self.sidebar, text="LAUNCH TRADING SYSTEM ENGINE", fg_color="#3a86ff", hover_color="#2563eb", font=ctk.CTkFont(size=13, weight="bold"), height=38, command=self.toggle_engine)
        self.btn_toggle.pack(side="bottom", fill="x", padx=20, pady=25)

    def add_small_input(self, parent, label_text, default, inline=True):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left" if inline else "top", expand=True, fill="x", padx=2, pady=1)
        lbl = ctk.CTkLabel(container, text=label_text, font=ctk.CTkFont(size=10), text_color="gray")
        lbl.pack(anchor="w")
        ent = ctk.CTkEntry(container, height=24, width=55 if inline else 200)
        ent.insert(0, default)
        ent.pack(fill="x", pady=1)
        return ent

    def setup_analytical_workspace(self):
        # Expanded Top Metrics Overview Layout Container
        self.cards_frame = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 10))

        self.c_price = self.create_status_card(self.cards_frame, "STREAMING BID PRICE", "$ 0.00", "#3a86ff")
        self.c_rsi = self.create_status_card(self.cards_frame, "ACTIVE COMPUTE RSI", "---", "#ff006e")
        self.c_mfi = self.create_status_card(self.cards_frame, "ACTIVE COMPUTE MFI", "---", "#8338ec")
        self.c_ema = self.create_status_card(self.cards_frame, "DYNAMIC EMA LINE", "---", "#ffbe0b")
        self.c_bal = self.create_status_card(self.cards_frame, "MOCK EQUITY LEDGER", f"$ {mock_balance}", "#2a9d8f")

        # Center Section Dashboard Layout Matrix Allocation Viewport Blocks
        mid_frame = ctk.CTkFrame(self.workspace, fg_color="transparent")
        mid_frame.pack(fill="both", expand=True, pady=5)

        # Multi-axis stacked subplots visual charts rendering workspace
        self.chart_frame = ctk.CTkFrame(mid_frame, fg_color="#212529", corner_radius=8)
        self.chart_frame.pack(side="left", expand=True, fill="both", padx=(0, 8))

        # Realtime Audit Ledger Logs view panel mapping parameters
        self.table_frame = ctk.CTkFrame(mid_frame, width=460, fg_color="#212529", corner_radius=8)
        self.table_frame.pack(side="right", fill="both", padx=(8, 0))
        
        ctk.CTkLabel(self.table_frame, text="📜 CRITERIA BREACH AUDIT TRAIL LOGS", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(pady=6, padx=10, anchor="w")

        self.audit_table = ttk.Treeview(self.table_frame, columns=("time", "signal", "price", "rsi", "mfi"), show="headings")
        self.audit_table.heading("time", text="Timestamp")
        self.audit_table.heading("signal", text="Condition")
        self.audit_table.heading("price", text="Execution Px")
        self.audit_table.heading("rsi", text="RSI")
        self.audit_table.heading("mfi", text="MFI")
        
        self.audit_table.column("time", width=75, anchor="center")
        self.audit_table.column("signal", width=105, anchor="center")
        self.audit_table.column("price", width=85, anchor="e")
        self.audit_table.column("rsi", width=40, anchor="center")
        self.audit_table.column("mfi", width=40, anchor="center")
        self.audit_table.pack(fill="both", expand=True, padx=10, pady=5)

        # Bottom System Standard Console Frame Output Debug View Logging Window Row
        self.log_box = ctk.CTkTextbox(self.workspace, height=130, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#18181b")
        self.log_box.pack(fill="x", pady=(8, 0))

    def create_status_card(self, parent, label, value, highlight):
        card = ctk.CTkFrame(parent, fg_color="#212529", corner_radius=6, border_width=1, border_color="#27272a")
        card.pack(side="left", expand=True, fill="both", padx=4)
        lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=9, weight="bold"), text_color="gray")
        lbl.pack(pady=(6, 1), padx=10, anchor="w")
        val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Consolas", size=16, weight="bold"), text_color=highlight)
        val.pack(pady=(0, 6), padx=10, anchor="w")
        card.v_lbl = val
        return card

    def toggle_engine(self):
        global is_running
        if not is_running:
            try:
                config = {
                    'use_rsi': bool(self.chk_rsi.get()), 'rsi_len': int(self.in_rsi_len.get()), 'rsi_ob': float(self.in_rsi_ob.get()), 'rsi_os': float(self.in_rsi_os.get()),
                    'use_mfi': bool(self.chk_mfi.get()), 'mfi_len': int(self.in_mfi_len.get()), 'mfi_ob': float(self.in_mfi_ob.get()), 'mfi_os': float(self.in_mfi_os.get()),
                    'use_ema': bool(self.chk_ema.get()), 'ema_len': int(self.in_ema_len.get()),
                    'alert_tele': bool(self.chk_tele.get()), 'alert_audio': bool(self.chk_audio.get()), 'alert_csv': bool(self.chk_csv.get())
                }
            except ValueError:
                self.log_message("❌ Error: Verification check parameters validation rejected mismatch typing inputs.")
                return
            
            is_running = True
            self.btn_toggle.configure(text="SHUTDOWN ACTIVE FEED", fg_color="#e63946")
            self.log_message("⏳ Deploying primary analytical background computing sequences frameworks...")
            
            self.thread = threading.Thread(target=trading_engine_loop, args=(config, self.ui_queue, self.safe_insert_table_row, self.log_message), daemon=True)
            self.thread.start()
        else:
            is_running = False
            self.btn_toggle.configure(text="LAUNCH TRADING SYSTEM ENGINE", fg_color="#3a86ff")
            self.log_message("🛑 Dispatched thread cancellation tokens down runtime components loops configurations.")

    def process_queue_feed(self):
        try:
            while True:
                price, rsi, mfi, ema, chart_df = self.ui_queue.get_nowait()
                self.render_advanced_subplots_interface(price, rsi, mfi, ema, chart_df)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue_feed)

    def render_advanced_subplots_interface(self, price, rsi, mfi, ema, chart_df):
        """EXPLICIT THREAD MANAGEMENT SAFE METHOD: Generates multi-axis stacked financial visualizations layout blocks."""
        self.c_price.v_lbl.configure(text=f"$ {price}")
        self.c_rsi.v_lbl.configure(text=str(rsi))
        self.c_mfi.v_lbl.configure(text=str(mfi))
        self.c_ema.v_lbl.configure(text=str(ema))
        
        for w in self.chart_frame.winfo_children(): w.destroy()

        # Styles definition settings configuration blocks maps parsing parameters
        colors = mpf.make_marketcolors(up='#2a9d8f', down='#e63946', wick='inherit', edge='inherit')
        style = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=colors, figcolor='#212529', facecolor='#18181b', gridcolor='#27272a', gridstyle='--')

        # 3. Dynamic secondary layered line data plotting assignments calculations
        additional_plots = []
        if self.chk_ema.get() and 'EMA' in chart_df.columns:
            # Overlap line structures arrays directly over the Candlesticks layout panels grid
            additional_plots.append(mpf.make_addplot(chart_df['EMA'], color='#ffbe0b', width=1.2, panel=0))
            
        if self.chk_rsi.get() and 'RSI' in chart_df.columns:
            # Shift calculations readouts metrics arrays down to distinct secondary lower stacked grids panels
            additional_plots.append(mpf.make_addplot(chart_df['RSI'], color='#ff006e', width=1.0, panel=1, ylabel='RSI (5)'))
            
        # Create structural multi-axis subplot spaces frames sets properties boundaries matching configurations options
        fig, axlist = mpf.plot(
            chart_df, 
            type='candle', 
            style=style, 
            addplot=additional_plots, 
            panel_ratios=(2.5, 1), # Allocates 70% height to price chart and 30% to oscillator line view grid panel
            returnfig=True, 
            figsize=(7.2, 4.6)
        )
        
        # Format bounding limits borders styling coordinates parameters highlights
        axlist[0].set_title(f"Alpha Workstation Core Telemetry: {SYMBOL} Stream", color="white", fontsize=10, weight="bold", pad=8)
        for ax in axlist: ax.tick_params(colors="gray", labelsize=7)
        
        # Add visual horizontal line boundary markers to oscillator views if active
        if len(axlist) > 2:
            axlist[2].axhline(70, color='#e63946', linestyle=':', alpha=0.5, linewidth=0.7)
            axlist[2].axhline(20, color='#2a9d8f', linestyle=':', alpha=0.5, linewidth=0.7)
            axlist[2].set_ylim(0, 100)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        canvas.draw()

    def execute_mock_order(self, direction):
        """Simulates rapid broker order routing directly from user control actions."""
        global mock_balance
        # Capture standard label value texts values dynamically from labels variables bindings checks
        try: current_px = float(self.c_price.v_lbl.cget("text").replace("$","").strip())
        except ValueError: current_px = 0.0
        
        if current_px <= 0:
            self.log_message("❌ Transaction Rejected: Core Engine Stream must be active with real-time ticks data feeds.")
            return

        # Simple execution model simulation balance ledger deductions
        fee = 5.00
        mock_balance -= fee
        self.c_bal.v_lbl.configure(text=f"$ {round(mock_balance, 2)}")
        
        self.log_message(f"📥 Order Routed: {direction} 0.10 Lots {SYMBOL} Filled at Entry execution index: ${current_px} (Fee: ${fee})")
        self.safe_insert_table_row(time.strftime('%H:%M:%S'), f"MANUAL {direction}", current_px, "EXEC", "EXEC")

    def safe_insert_table_row(self, time_str, condition, price, rsi, mfi):
        self.audit_table.insert("", 0, values=(time_str, condition, f"${price}", rsi, mfi))

    def log_message(self, text):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_box.see("end")

if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()