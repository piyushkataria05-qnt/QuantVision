# QuantVision: Multithreaded Algorithmic Trading Workstation

QuantVision is an event-driven, multi-threaded quantitative trading terminal built in Python. It interfaces directly with a running MetaTrader 5 (MT5) core application to pull live tick feeds, execute multi-factor technical analysis strategies (RSI, MFI, EMA), plot synchronized dark-themed candlestick charts, and route automated alert vectors via secure webhooks.

## 🚀 Key Architectural Features
- **Thread-Isolated Engine:** Decoupled data parsing and mathematical matrix computations from the primary UI main loop via an asynchronous queue layer to ensure lag-free visualization rendering.
- **Dynamic Optimization Sandbox:** Runtime user parameters allow custom length period values and multi-factor conditional switches.
- **Automated Alerts Logic:** Direct Webhook configuration pipelines instantly delivering real-time metric breaches straight to mobile devices via Telegram.
- **Localized Ledger Simulation:** Transaction state machinery recording mock transactions directly against an asset stream engine.

## 🛠️ Tech Stack & Dependencies
- **Core Environment:** Python (3.10+)
- **Trading Connectivity:** MetaTrader 5 API (IPC Layer)
- **Data Ingestion & Calculation:** Pandas, Pandas-TA
- **Visualization Component Frameworks:** CustomTkinter, Matplotlib, Mplfinance
- **Networking Protocols:** Requests (Telegram Bot API Webhooks)

## 💻 Installation & Local Launch Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/piyushkataria05-qnt/QuantVision.git](https://github.com/piyushkataria05-qnt/QuantVision.git)
   cd QuantVision
Install Required Libraries:

Bash
pip install -r requirements.txt
Configure Environment Parameters:
Create a .env file in the root folder of the project:

Code snippet
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
Execution:
Ensure your MT5 desktop terminal is logged into a broker account, enable "Allow Algo Trading" in your terminal settings, then run:

Bash
python app.py
