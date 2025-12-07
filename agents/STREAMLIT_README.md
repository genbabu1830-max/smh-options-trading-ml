# Streamlit Testing App for Recommendation Agent

Interactive web interface for testing the Options Trading Recommendation Agent.

## Features

### 📊 Interactive UI
- Clean, professional interface
- Real-time recommendation generation
- Visual metrics and charts
- Responsive design

### ⚙️ Configuration Options
- **Ticker Selection**: SMH, SPY, QQQ, IWM
- **Date Selection**: Current date or historical date for backtesting
- **Model Source**: Local storage (fast) or S3 (production)

### 🎯 Recommendation Display
- Strategy name and confidence
- Complete trade parameters
- Market conditions analysis
- Risk validation results
- Alternative strategies
- Formatted output
- Raw JSON data

### 📜 History Tracking
- Track all generated recommendations
- View past predictions
- Compare strategies over time

## Installation

### Prerequisites

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install Streamlit (if not already installed)
pip install streamlit
```

### Dependencies

The app requires:
- streamlit
- pandas
- All agent dependencies (already installed)

## Usage

### Option 1: Run Script

```bash
# From agents/ directory
bash run_streamlit.sh
```

### Option 2: Direct Command

```bash
# From agents/ directory
streamlit run streamlit_app.py
```

### Option 3: From Project Root

```bash
# From project root
streamlit run agents/streamlit_app.py
```

## How to Use

### 1. Initialize Agent

1. Select ticker (SMH, SPY, QQQ, IWM)
2. Choose date (current or historical)
3. Select model source (Local or S3)
4. Click "Initialize Agent"

### 2. Generate Recommendation

1. Click "Generate Recommendation"
2. Wait for processing (5-10 seconds)
3. View results

### 3. Explore Results

- **Strategy Overview**: See predicted strategy and confidence
- **Trade Parameters**: View specific strikes, DTE, sizing
- **Market Conditions**: Check IV rank, trend, RSI, ADX
- **Risk Validation**: See if trade is approved
- **Alternatives**: View other possible strategies
- **Download**: Save recommendation as JSON or text

### 4. Test Different Scenarios

- Change date to test historical data
- Try different tickers
- Compare strategies across dates
- Build recommendation history

## Interface Sections

### Sidebar (Left)
- Configuration options
- Agent initialization
- Status indicators
- Clear history button

### Main Area (Center)
- Recommendation generation
- Strategy display
- Trade parameters
- Market conditions
- Risk validation
- Download options

### History (Bottom)
- Table of all recommendations
- Timestamp, ticker, date, strategy, confidence

## Screenshots

### Main Interface
```
┌─────────────────────────────────────────────────────────┐
│  📊 Options Trading Recommendation Agent                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🎯 Recommended Strategy                                │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ Strategy │Confidence│ Accuracy │ Version  │        │
│  │Iron Cond.│  82.5%   │  84.21%  │  v1.0    │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│                                                          │
│  💰 Trade Parameters                                    │
│  Put Spread: $230 / $235                                │
│  Call Spread: $245 / $250                               │
│  DTE: 21 days | Contracts: 2                            │
│  Net Credit: $340 | Max Profit: $340 | Max Loss: -$660 │
│                                                          │
│  📈 Market Conditions                                   │
│  Price: $236.80 | IV Rank: 45.2% | Trend: Weak Up      │
│  ADX: 18.5 | RSI: 52.3                                  │
│                                                          │
│  ✅ Risk Validation: APPROVED                           │
│  Risk/Reward: 1.94 | Risk %: 1.32% | Size: $660        │
└─────────────────────────────────────────────────────────┘
```

## Testing Scenarios

### Scenario 1: Current Market Conditions
```
Ticker: SMH
Date: Current
Model: Local
Expected: Real-time recommendation
```

### Scenario 2: Historical Backtesting
```
Ticker: SMH
Date: 2024-06-15
Model: Local
Expected: Historical recommendation for that date
```

### Scenario 3: Different Tickers
```
Ticker: SPY, QQQ, IWM
Date: Current
Model: Local
Expected: Recommendations for different ETFs
```

### Scenario 4: Production Mode
```
Ticker: SMH
Date: Current
Model: S3
Expected: Load models from S3, slower but production-ready
```

## Troubleshooting

### Issue: "Agent not initialized"
**Solution:** Click "Initialize Agent" in sidebar

### Issue: "Failed to generate recommendation"
**Solution:** 
- Check that models exist in `models_storage/`
- Verify virtual environment is activated
- Check error message for details

### Issue: "Module not found"
**Solution:**
```bash
source venv/bin/activate
pip install streamlit pandas
```

### Issue: Port already in use
**Solution:**
```bash
# Use different port
streamlit run streamlit_app.py --server.port 8502
```

### Issue: Slow performance
**Solution:**
- Use local models (not S3)
- Close other applications
- Check system resources

## Development

### Customize UI

Edit `streamlit_app.py`:
- Modify CSS in `st.markdown()` section
- Add new metrics or charts
- Change layout and colors

### Add Features

```python
# Add new sidebar option
new_option = st.sidebar.selectbox("New Option", ["A", "B", "C"])

# Add new metric
st.metric("New Metric", value)

# Add new chart
st.line_chart(data)
```

### Debug Mode

```bash
# Run with debug logging
streamlit run streamlit_app.py --logger.level=debug
```

## Performance

### Load Times
- Agent initialization: 2-3 seconds (local), 5-8 seconds (S3)
- Recommendation generation: 5-10 seconds
- UI rendering: <1 second

### Resource Usage
- Memory: ~500MB
- CPU: Low (spikes during generation)
- Network: Minimal (only for S3 mode)

## Security

### Local Mode
- No external connections
- Models loaded from local storage
- Safe for testing

### S3 Mode
- Requires AWS credentials
- Connects to S3 bucket
- Use IAM roles with minimal permissions

### Data Privacy
- No data sent to external services
- All processing local
- Recommendations not stored externally

## Tips

1. **Start with Local Mode**: Faster for testing
2. **Use Historical Dates**: Test backtesting functionality
3. **Compare Strategies**: Generate multiple recommendations
4. **Check Risk Validation**: Ensure trades are approved
5. **Download Results**: Save for later analysis
6. **Clear History**: Reset when testing new scenarios

## Keyboard Shortcuts

- `Ctrl+C`: Stop server
- `R`: Rerun app
- `C`: Clear cache
- `?`: Show keyboard shortcuts

## Browser Compatibility

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

## Mobile Support

The app is responsive and works on mobile devices, but desktop is recommended for best experience.

## Next Steps

1. **Integrate Massive.com API**: Replace mock data with real option chains
2. **Add Charts**: Visualize profit/loss diagrams
3. **Add Backtesting**: Test strategies on historical data
4. **Add Comparison**: Compare multiple strategies side-by-side
5. **Add Export**: Export to CSV, Excel, PDF

## Support

**Issues:** Use GitHub Issues for bug reports

**Documentation:** See `agents/README.md` for agent details

**Questions:** Check `AGENT_IMPLEMENTATION_STATUS.md` for status

---

**Status:** ✅ Ready to use  
**Version:** 1.0  
**Last Updated:** December 6, 2024
