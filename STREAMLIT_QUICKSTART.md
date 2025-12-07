# Streamlit App Quick Start

## 🚀 Launch the Testing Interface

### Step 1: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 2: Run Streamlit App

```bash
# Option A: Use the run script
bash agents/run_streamlit.sh

# Option B: Direct command
streamlit run agents/streamlit_app.py
```

### Step 3: Open Browser

The app will automatically open at: **http://localhost:8501**

If it doesn't open automatically, click the link in the terminal.

## 📖 Quick Usage Guide

### 1. Initialize Agent (Sidebar)

1. Select **Ticker**: SMH (default)
2. Choose **Date**: Use current date or select historical
3. Select **Model Source**: Local (recommended for testing)
4. Click **"🚀 Initialize Agent"**

Wait 2-3 seconds for initialization.

### 2. Generate Recommendation

1. Click **"🎯 Generate Recommendation"** button
2. Wait 5-10 seconds for processing
3. View results in main area

### 3. Explore Results

- **Strategy**: See predicted strategy and confidence
- **Parameters**: View strikes, DTE, contracts, costs
- **Market Conditions**: Check IV rank, trend, RSI, ADX
- **Risk Validation**: See if trade is approved
- **Download**: Save as JSON or text file

### 4. Test Different Scenarios

- Change date to test historical data
- Try different tickers (SPY, QQQ, IWM)
- Compare strategies across dates
- View recommendation history at bottom

## 🎯 Example Workflow

```
1. Initialize Agent
   ├─ Ticker: SMH
   ├─ Date: Current
   └─ Model: Local
   
2. Generate Recommendation
   └─ Wait 5-10 seconds
   
3. View Results
   ├─ Strategy: Iron Condor (82.5% confidence)
   ├─ Parameters: Strikes, DTE, sizing
   ├─ Market: IV Rank 45%, Weak Up trend
   └─ Risk: APPROVED (1.94 R/R)
   
4. Download
   └─ Save as JSON or text
   
5. Test Another Date
   ├─ Select historical date
   ├─ Generate again
   └─ Compare results
```

## 💡 Tips

- **Start with Local Mode**: Faster for testing
- **Use Historical Dates**: Test backtesting functionality
- **Check Risk Validation**: Ensure trades are approved
- **Download Results**: Save for later analysis
- **Clear History**: Reset when testing new scenarios

## ⚠️ Current Limitations

- Using **mock data** (no real option chains yet)
- Feature extraction will fail without real data
- Need to integrate Massive.com API for full functionality

## 🔧 Troubleshooting

### App won't start
```bash
# Check Streamlit is installed
streamlit --version

# If not, install it
pip install streamlit
```

### Port already in use
```bash
# Use different port
streamlit run agents/streamlit_app.py --server.port 8502
```

### Agent initialization fails
- Check models exist in `models_storage/etfs/SMH/production/`
- Verify virtual environment is activated
- Check error message in terminal

## 📸 What You'll See

```
┌─────────────────────────────────────────────────────────┐
│  📊 Options Trading Recommendation Agent                │
├─────────────────────────────────────────────────────────┤
│  Sidebar:                    Main Area:                  │
│  ⚙️ Configuration           🎯 Strategy Display         │
│  - Ticker: SMH              - Iron Condor (82.5%)       │
│  - Date: Current            - Strikes, DTE, Sizing      │
│  - Model: Local             - Market Conditions         │
│  🚀 Initialize Agent        - Risk Validation           │
│  ✅ Agent Ready             📥 Download Options         │
│                                                          │
│  Bottom:                                                 │
│  📜 Recommendation History                              │
│  - All past recommendations                             │
│  - Timestamp, ticker, strategy, confidence              │
└─────────────────────────────────────────────────────────┘
```

## 🎉 You're Ready!

The Streamlit app provides an interactive way to test the Recommendation Agent without writing code. Perfect for:

- Testing different market conditions
- Backtesting historical dates
- Comparing strategies
- Demonstrating the system
- Debugging recommendations

---

**Next Step:** Integrate Massive.com API for real option chain data

**Documentation:** See `agents/STREAMLIT_README.md` for full details

**Status:** ✅ Ready to use (with mock data)
