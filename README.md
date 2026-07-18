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
   git clone [https://github.com/YOUR_USERNAME/QuantVision.git](https://github.com/YOUR_USERNAME/QuantVision.git)
   cd QuantVision
Install Required Libraries:

Bash
pip install -r requirements.txt
Configure Environment Parameters:
Create a .env file in the root root folder:

Code snippet
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
Execution:
Ensure your MT5 desktop terminal is logged into a broker account, check "Allow Algo Trading", then run:

Bash
python app.py

---

## 🚀 Step 5: Push to GitHub via Terminal

1. Go to [GitHub](https://github.com/), log in, click the **"+"** icon in the top right, and select **New repository**.
2. Name your repository `QuantVision` (or whatever you prefer), leave it as **Public**, do **NOT** check "Add a README" (since we already made one), and click **Create repository**.
3. Open your project terminal on your computer and run these commands sequentially to upload your workspace:

```bash
# Initialize an empty git tracker in your local folder
git init

# Stage all files (except the ones listed in your .gitignore)
git add .

# Save a snapshot of your files locally
git commit -m "feat: Initial commit of multithreaded quantitative dashboard architecture"

# Point your local Git branch to the main branch
git branch -M main

# Link your local folder to your newly created GitHub online repository 
# (Copy this exact line directly from the GitHub setup page instructions)
git remote add origin https://github.com/YOUR_USERNAME/QuantVision.git

# Push the code live to the web!
git push -u origin main