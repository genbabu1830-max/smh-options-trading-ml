# Model Prediction Input/Output Guide
## How to Use the Trained SMH Options Model for Daily Predictions

---

## Overview

This document explains how to prepare input data for the trained ML model and interpret its predictions. The model does NOT take raw option chains as input. Instead, it takes 80 aggregated features that describe current market conditions.

**Process Summary:**
1. Collect raw market data (option chain, prices, etc.)
2. Calculate 80 features from raw data
3. Format features as model input
4. Get model prediction
5. Use prediction to execute trade with actual options

---

## Daily Prediction Workflow

### Timeline: Every Trading Day at 9:05 AM ET

```
9:00 AM - Market Opens
   ↓
9:05 AM - Start Prediction Process
   ↓
Step 1: Collect Raw Data (5 minutes)
   ↓
Step 2: Calculate 80 Features (2 minutes)
   ↓
Step 3: Format Model Input (1 minute)
   ↓
Step 4: Get Model Prediction (Instant)
   ↓
Step 5: Execute Trade (5-10 minutes)
   ↓
9:15 AM - Position Opened
```

---

## Step 1: Collect Raw Market Data

### What You Need to Gather

**Data Source 1: SMH Price History (Last 50 Trading Days)**
```
Date         | Open    | High    | Low     | Close   | Volume
-------------|---------|---------|---------|---------|----------
2024-10-15   | 228.50  | 230.20  | 227.80  | 229.45  | 42000000
2024-10-16   | 229.50  | 231.10  | 229.00  | 230.85  | 45000000
2024-10-17   | 230.90  | 232.50  | 230.20  | 231.20  | 48000000
...
2024-12-04   | 234.20  | 236.50  | 233.80  | 235.50  | 51000000
2024-12-05   | 235.60  | 237.20  | 235.10  | 236.80  | Current
```

**Data Source 2: Today's Option Chain (All Liquid Options)**
```
Filter Criteria:
- Strikes: ±15% from current price (e.g., if SMH = $236, get strikes $200-272)
- DTE: 7-90 days
- Volume: > 10 contracts
- Open Interest: > 100 contracts

Expected: 100-150 option contracts
```

**Sample Option Chain (Showing 10 of ~150):**
```
Ticker                    | Strike | Type | Exp Date   | DTE | Bid   | Ask   | Volume | OI    | IV    | Delta | Gamma | Theta  | Vega
--------------------------|--------|------|------------|-----|-------|-------|--------|-------|-------|-------|-------|--------|------
O:SMH241213P00220000     | 220    | put  | 2024-12-13 | 8   | 0.45  | 0.48  | 250    | 3200  | 0.28  | -0.18 | 0.08  | -0.06  | 0.12
O:SMH241213P00225000     | 225    | put  | 2024-12-13 | 8   | 0.82  | 0.86  | 580    | 5100  | 0.26  | -0.28 | 0.11  | -0.09  | 0.16
O:SMH241213P00230000     | 230    | put  | 2024-12-13 | 8   | 1.45  | 1.52  | 920    | 8500  | 0.24  | -0.42 | 0.13  | -0.13  | 0.19
O:SMH241213P00235000     | 235    | put  | 2024-12-13 | 8   | 2.58  | 2.68  | 1450   | 12000 | 0.23  | -0.55 | 0.14  | -0.17  | 0.21
O:SMH241213C00235000     | 235    | call | 2024-12-13 | 8   | 3.85  | 3.95  | 1680   | 15000 | 0.22  | 0.58  | 0.14  | -0.19  | 0.22
O:SMH241213C00240000     | 240    | call | 2024-12-13 | 8   | 2.20  | 2.28  | 1120   | 10500 | 0.24  | 0.44  | 0.13  | -0.15  | 0.19
O:SMH241213C00245000     | 245    | call | 2024-12-13 | 8   | 1.15  | 1.22  | 680    | 6800  | 0.26  | 0.30  | 0.11  | -0.11  | 0.16
O:SMH241213C00250000     | 250    | call | 2024-12-13 | 8   | 0.55  | 0.60  | 420    | 4200  | 0.28  | 0.18  | 0.08  | -0.07  | 0.12
... (142 more options with different strikes and expirations)
```

**Data Source 3: Market Context Data**
```
Current Market Data (December 5, 2024):
- SPY Close: $589.20
- VIX Close: $16.25
- Treasury 10Y Yield: 4.35%
- Market Breadth (Advance/Decline): 0.62
```

**Data Source 4: Historical IV Data (52 Weeks)**
```
For IV Rank Calculation:
- 52-Week IV Low: 0.18
- 52-Week IV High: 0.42
- Used to calculate: IV Rank = (current_iv - low) / (high - low) × 100
```

---

## Step 2: Calculate 80 Features

### Feature Calculation Process

**You must calculate the same 80 features used during training.**

### Category 1: Price Features (20 features)

**From SMH Price History:**

**Returns:**
```
current_price = 236.80 (today's close)
yesterday_price = 235.50

return_1d = (236.80 - 235.50) / 235.50 = 0.0055

For multi-day returns, look back:
return_3d = (236.80 - price_3_days_ago) / price_3_days_ago
return_5d = (236.80 - price_5_days_ago) / price_5_days_ago
return_10d = (236.80 - price_10_days_ago) / price_10_days_ago
return_20d = ...
return_50d = ...
```

**Moving Averages:**
```
sma_5 = average(last 5 closing prices)
sma_10 = average(last 10 closing prices)
sma_20 = average(last 20 closing prices)
sma_50 = average(last 50 closing prices)
sma_200 = average(last 200 closing prices)

Example calculation:
Last 5 closes: [235.50, 234.20, 236.10, 235.80, 236.80]
sma_5 = (235.50 + 234.20 + 236.10 + 235.80 + 236.80) / 5 = 235.68

price_vs_sma_5 = (236.80 - 235.68) / 235.68 = 0.0047
price_vs_sma_10 = (236.80 - sma_10) / sma_10
... similarly for all SMAs
```

**Bollinger Bands:**
```
bb_middle = sma_20 = 233.45
bb_std = standard_deviation(last 20 closes) = 2.85
bb_upper = bb_middle + (2 × bb_std) = 233.45 + 5.70 = 239.15
bb_lower = bb_middle - (2 × bb_std) = 233.45 - 5.70 = 227.75

bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
bb_position = (236.80 - 227.75) / (239.15 - 227.75) = 0.7939
```

**SMA Alignment:**
```
Check if: sma_5 > sma_10 > sma_20 > sma_50 > sma_200
If true: sma_alignment = 1 (bullish alignment)
If false: sma_alignment = 0
```

---

### Category 2: Technical Indicators (15 features)

**RSI (14-period):**
```
Calculate from last 14 days of price changes
Result: rsi_14 = 58.35
```

**MACD:**
```
macd = 2.458
macd_signal = 2.185
macd_histogram = 0.273
```

**ADX (14-period):**
```
Measures trend strength
Result: adx_14 = 22.45
```

**ATR (14-period):**
```
Average True Range (volatility measure)
Result: atr_14 = 3.825
```

**Volume Metrics:**
```
volume_20d_avg = average(last 20 days volumes) = 46500000
current_volume = 51000000
volume_vs_avg = 51000000 / 46500000 = 1.097
```

**Other Indicators:**
```
obv (On-Balance Volume) = 8450000000
stochastic_k = 68.5
stochastic_d = 65.8
cci (Commodity Channel Index) = 145.2
williams_r = -28.5
mfi (Money Flow Index) = 62.3
```

---

### Category 3: Volatility Features (15 features)

**From Option Chain - IV Metrics:**

**ATM Implied Volatility:**
```
Find ATM options (strikes closest to current price 236.80):
- 235 Put: IV = 0.23
- 235 Call: IV = 0.22
- 240 Put: IV = 0.24
- 240 Call: IV = 0.24

iv_atm = average(0.23, 0.22, 0.24, 0.24) = 0.2325
```

**IV Rank and Percentile:**
```
Current IV: 0.2325
52-Week Low: 0.18
52-Week High: 0.42

iv_rank = (0.2325 - 0.18) / (0.42 - 0.18) × 100 = 21.88
iv_percentile = 45.5 (percentage of days in last year with lower IV)
```

**Historical Volatility:**
```
Calculate from price returns over last 20 days
hv_20d = 0.248
```

**HV/IV Ratio:**
```
hv_iv_ratio = 0.248 / 0.2325 = 1.067
(HV is higher than IV - IV may be underpriced)
```

**IV Skew:**
```
Find 10% OTM options:
- 10% OTM Put (strike ~213): IV = 0.28
- 10% OTM Call (strike ~260): IV = 0.25

iv_skew = 0.28 - 0.25 = 0.03 (put skew)
```

**IV Term Structure:**
```
Near-term IV (options expiring in 7-14 days): 0.24
Longer-term IV (options expiring in 45-60 days): 0.22

iv_term_structure = 0.24 - 0.22 = 0.02 (contango)
```

**VIX Metrics:**
```
vix_level = 16.25
vix_change = 16.25 - yesterday_vix = 0.15
vix_ma20 = 15.85
vix_vs_ma20 = 16.25 / 15.85 = 1.025
```

**Other Volatility Metrics:**
```
volatility_trend = 0 (stable, not increasing/decreasing)
parkinson_vol = 0.252 (high-low estimator)
garman_klass_vol = 0.245 (OHLC estimator)
vol_of_vol = 0.032 (volatility of volatility)
```

---

### Category 4: Options Metrics (15 features)

**From Option Chain - Volume and OI:**

**Put/Call Ratios:**
```
Sum all put volumes today: 45,280 contracts
Sum all call volumes today: 58,920 contracts
put_call_volume_ratio = 45,280 / 58,920 = 0.768

Sum all put open interest: 385,000 contracts
Sum all call open interest: 448,000 contracts
put_call_oi_ratio = 385,000 / 448,000 = 0.860
```

**Total Metrics:**
```
total_option_volume = 45,280 + 58,920 = 104,200
total_open_interest = 385,000 + 448,000 = 833,000
```

**ATM Greeks (Aggregated):**
```
From ATM options (strikes 235-240):
atm_delta_call = average(0.58, 0.54, 0.50) = 0.54
atm_delta_put = average(-0.55, -0.52, -0.48) = -0.52
atm_gamma = average(0.14, 0.14, 0.13) = 0.137
atm_theta = average(-0.19, -0.17, -0.15) = -0.170
atm_vega = average(0.22, 0.21, 0.19) = 0.207
```

**Max Pain:**
```
Calculate max pain strike (where most options expire worthless)
max_pain_strike = 235.0

distance_to_max_pain = (236.80 - 235.0) / 236.80 = 0.0076
```

**Gamma and Delta Exposure:**
```
Aggregate market maker positions:
gamma_exposure = 0.285 (aggregate gamma weighted by OI)
delta_exposure = -0.092 (net delta position)
```

**Activity Flags:**
```
unusual_activity = 0 (no unusual volume spikes today)
options_flow_sentiment = 0.18 (slightly bullish based on order flow)
```

---

### Category 5: Support/Resistance (10 features)

**From Price History:**

**Resistance Levels:**
```
Look back 30 days for recent highs:
resistance_1 = 245.50 (recent high)
resistance_2 = 248.20 (secondary resistance)
```

**Support Levels:**
```
Look back 30 days for recent lows:
support_1 = 225.80 (recent low)
support_2 = 223.50 (secondary support)
```

**Distance Calculations:**
```
current_price = 236.80

distance_to_resistance_1 = (245.50 - 236.80) / 236.80 = 0.0367
distance_to_support_1 = (236.80 - 225.80) / 236.80 = 0.0465
```

**Range Metrics:**
```
range_high = 245.50
range_low = 225.80
range_width = (245.50 - 225.80) / 236.80 = 0.0832

position_in_range = (236.80 - 225.80) / (245.50 - 225.80)
position_in_range = 0.558 (mid-range)

days_in_range = 15 (days since breakout)
breakout_probability = 0.25 (estimated probability of breaking out)
```

---

### Category 6: Market Context (10 features)

**Correlation with SPY:**
```
Calculate 30-day rolling correlation between SMH and SPY returns
spy_correlation = 0.82
```

**SPY Performance:**
```
spy_return_1d = (589.20 - 587.85) / 587.85 = 0.0023
spy_return_5d = (589.20 - 582.40) / 582.40 = 0.0117
```

**Relative Performance:**
```
smh_return_5d = 0.0185
spy_return_5d = 0.0117

smh_vs_spy = 0.0185 - 0.0117 = 0.0068 (SMH outperforming)
```

**Sector and Market Metrics:**
```
sector_rotation = 0.68 (rotation score into tech)
market_breadth = 0.62 (62% of stocks advancing)
treasury_yield = 4.35 (10-year yield)
yield_curve_slope = 0.82 (10Y - 2Y spread)
risk_on_off = 0.75 (risk-on environment)
```

---

### Category 7: Regime Classification (5 features)

**Trend Regime:**
```
Based on: ADX=22.45, MACD positive, price above SMAs

Classification: "weak_up"
Encoded: trend_regime = 3

Scale:
0 = strong_down
1 = weak_down
2 = ranging
3 = weak_up
4 = strong_up
```

**Volatility Regime:**
```
Based on: IV Rank=21.88, HV/IV=1.067

Classification: "low"
Encoded: volatility_regime = 1

Scale:
0 = very_low
1 = low
2 = normal
3 = elevated
4 = very_high
```

**Volume Regime:**
```
Based on: volume_vs_avg = 1.097

Classification: "normal"
Encoded: volume_regime = 1

Scale:
0 = low
1 = normal
2 = high
```

**Combined State:**
```
Combination of trend + volatility + volume
combined_state = 7 (encoded combination)

Possible range: 0-24 (5 × 5 × 3 possibilities)
```

**Regime Stability:**
```
days_since_regime_change = 8 (days in current regime)
```

---

## Step 3: Format Model Input

### Input Structure

**The model expects ONE ROW with 80 features in specific order.**

### Input Format Option 1: CSV Format

**File:** `prediction_input.csv`

```csv
current_price,return_1d,return_3d,return_5d,return_10d,return_20d,return_50d,sma_5,sma_10,sma_20,sma_50,sma_200,price_vs_sma_5,price_vs_sma_10,price_vs_sma_20,price_vs_sma_50,price_vs_sma_200,sma_alignment,bb_upper,bb_middle,bb_lower,bb_position,rsi_14,macd,macd_signal,macd_histogram,adx_14,atr_14,obv,stochastic_k,stochastic_d,cci,williams_r,mfi,hv_20d,iv_atm,iv_rank,iv_percentile,hv_iv_ratio,iv_skew,iv_term_structure,vix_level,vix_change,vix_vs_ma20,volatility_trend,parkinson_vol,garman_klass_vol,vol_of_vol,put_call_volume_ratio,put_call_oi_ratio,total_option_volume,total_open_interest,atm_delta_call,atm_delta_put,atm_gamma,atm_theta,atm_vega,max_pain_strike,distance_to_max_pain,gamma_exposure,delta_exposure,unusual_activity,options_flow_sentiment,resistance_1,resistance_2,support_1,support_2,distance_to_resistance_1,distance_to_support_1,position_in_range,range_width,days_in_range,breakout_probability,spy_correlation,spy_return_1d,spy_return_5d,smh_vs_spy,sector_rotation,market_breadth,treasury_yield,yield_curve_slope,risk_on_off,trend_regime,volatility_regime,volume_regime,combined_state,days_since_regime_change
236.80,0.0055,0.0125,0.0185,0.0095,0.0420,0.0385,235.68,234.85,233.45,231.25,218.50,0.0047,0.0083,0.0143,0.0240,0.0838,1,239.15,233.45,227.75,0.7939,58.35,2.458,2.185,0.273,22.45,3.825,8450000000,68.5,65.8,145.2,-28.5,62.3,0.248,0.2325,21.88,45.5,1.067,0.03,0.02,16.25,0.15,1.025,0,0.252,0.245,0.032,0.768,0.860,104200,833000,0.54,-0.52,0.137,-0.170,0.207,235.0,0.0076,0.285,-0.092,0,0.18,245.50,248.20,225.80,223.50,0.0367,0.0465,0.558,0.0832,15,0.25,0.82,0.0023,0.0117,0.0068,0.68,0.62,4.35,0.82,0.75,3,1,1,7,8
```

### Input Format Option 2: JSON Format

**File:** `prediction_input.json`

```json
{
  "date": "2024-12-05",
  "features": {
    "current_price": 236.80,
    "return_1d": 0.0055,
    "return_3d": 0.0125,
    "return_5d": 0.0185,
    "return_10d": 0.0095,
    "return_20d": 0.0420,
    "return_50d": 0.0385,
    "sma_5": 235.68,
    "sma_10": 234.85,
    "sma_20": 233.45,
    "sma_50": 231.25,
    "sma_200": 218.50,
    "price_vs_sma_5": 0.0047,
    "price_vs_sma_10": 0.0083,
    "price_vs_sma_20": 0.0143,
    "price_vs_sma_50": 0.0240,
    "price_vs_sma_200": 0.0838,
    "sma_alignment": 1,
    "bb_upper": 239.15,
    "bb_middle": 233.45,
    "bb_lower": 227.75,
    "bb_position": 0.7939,
    "rsi_14": 58.35,
    "macd": 2.458,
    "macd_signal": 2.185,
    "macd_histogram": 0.273,
    "adx_14": 22.45,
    "atr_14": 3.825,
    "obv": 8450000000,
    "stochastic_k": 68.5,
    "stochastic_d": 65.8,
    "cci": 145.2,
    "williams_r": -28.5,
    "mfi": 62.3,
    "hv_20d": 0.248,
    "iv_atm": 0.2325,
    "iv_rank": 21.88,
    "iv_percentile": 45.5,
    "hv_iv_ratio": 1.067,
    "iv_skew": 0.03,
    "iv_term_structure": 0.02,
    "vix_level": 16.25,
    "vix_change": 0.15,
    "vix_vs_ma20": 1.025,
    "volatility_trend": 0,
    "parkinson_vol": 0.252,
    "garman_klass_vol": 0.245,
    "vol_of_vol": 0.032,
    "put_call_volume_ratio": 0.768,
    "put_call_oi_ratio": 0.860,
    "total_option_volume": 104200,
    "total_open_interest": 833000,
    "atm_delta_call": 0.54,
    "atm_delta_put": -0.52,
    "atm_gamma": 0.137,
    "atm_theta": -0.170,
    "atm_vega": 0.207,
    "max_pain_strike": 235.0,
    "distance_to_max_pain": 0.0076,
    "gamma_exposure": 0.285,
    "delta_exposure": -0.092,
    "unusual_activity": 0,
    "options_flow_sentiment": 0.18,
    "resistance_1": 245.50,
    "resistance_2": 248.20,
    "support_1": 225.80,
    "support_2": 223.50,
    "distance_to_resistance_1": 0.0367,
    "distance_to_support_1": 0.0465,
    "position_in_range": 0.558,
    "range_width": 0.0832,
    "days_in_range": 15,
    "breakout_probability": 0.25,
    "spy_correlation": 0.82,
    "spy_return_1d": 0.0023,
    "spy_return_5d": 0.0117,
    "smh_vs_spy": 0.0068,
    "sector_rotation": 0.68,
    "market_breadth": 0.62,
    "treasury_yield": 4.35,
    "yield_curve_slope": 0.82,
    "risk_on_off": 0.75,
    "trend_regime": 3,
    "volatility_regime": 1,
    "volume_regime": 1,
    "combined_state": 7,
    "days_since_regime_change": 8
  }
}
```

### Input Format Option 3: Array (For Direct Model Feed)

```
[236.80, 0.0055, 0.0125, 0.0185, 0.0095, 0.0420, 0.0385, 235.68, 234.85, 233.45, 231.25, 218.50, 0.0047, 0.0083, 0.0143, 0.0240, 0.0838, 1, 239.15, 233.45, 227.75, 0.7939, 58.35, 2.458, 2.185, 0.273, 22.45, 3.825, 8450000000, 68.5, 65.8, 145.2, -28.5, 62.3, 0.248, 0.2325, 21.88, 45.5, 1.067, 0.03, 0.02, 16.25, 0.15, 1.025, 0, 0.252, 0.245, 0.032, 0.768, 0.860, 104200, 833000, 0.54, -0.52, 0.137, -0.170, 0.207, 235.0, 0.0076, 0.285, -0.092, 0, 0.18, 245.50, 248.20, 225.80, 223.50, 0.0367, 0.0465, 0.558, 0.0832, 15, 0.25, 0.82, 0.0023, 0.0117, 0.0068, 0.68, 0.62, 4.35, 0.82, 0.75, 3, 1, 1, 7, 8]
```

**This is exactly 80 numeric values in the same order as training.**

---

## Step 4: Get Model Prediction

### Model Processing

**The model receives the 80 features and:**
1. Determines which strategy is optimal
2. Predicts optimal parameters for that strategy
3. Provides confidence metrics

### Model Output Format

**Output Format Option 1: Detailed JSON**

```json
{
  "prediction_date": "2024-12-05",
  "prediction_time": "2024-12-05T09:07:23Z",
  "model_version": "v1.2.5",
  
  "strategy": {
    "type": "BULL_CALL_SPREAD",
    "confidence": 0.82
  },
  
  "parameters": {
    "long_strike": 235.0,
    "short_strike": 245.0,
    "dte": 21,
    "contracts": 1
  },
  
  "expected_performance": {
    "expected_return": 0.0325,
    "win_probability": 0.64,
    "max_profit": 680.0,
    "max_loss": -320.0,
    "risk_reward_ratio": 2.125,
    "avg_days_to_exit": 12.5
  },
  
  "market_conditions_summary": {
    "trend": "weak_up",
    "volatility": "low", 
    "iv_rank": 21.88,
    "current_price": 236.80
  },
  
  "alternative_strategies": [
    {
      "strategy": "LONG_CALL",
      "confidence": 0.75,
      "expected_return": 0.0285
    },
    {
      "strategy": "IRON_CONDOR",
      "confidence": 0.68,
      "expected_return": 0.0215
    }
  ]
}
```

**Output Format Option 2: Simple CSV**

```csv
date,strategy,long_strike,short_strike,dte,expected_return,win_probability,max_profit,max_loss
2024-12-05,BULL_CALL_SPREAD,235.0,245.0,21,0.0325,0.64,680.0,-320.0
```

**Output Format Option 3: Text Summary**

```
=================================================
SMH OPTIONS STRATEGY RECOMMENDATION
Date: December 5, 2024, 9:07 AM ET
=================================================

RECOMMENDED STRATEGY: Bull Call Spread
Confidence: 82%

PARAMETERS:
  Buy:  235 Call
  Sell: 245 Call
  Expiration: ~21 days (Dec 26, 2024)
  
EXPECTED PERFORMANCE:
  Expected Return: 3.25% of capital
  Win Probability: 64%
  Max Profit: $680 per spread
  Max Loss: $320 per spread
  Risk/Reward: 2.13:1
  Avg Holding Period: 12-13 days
  
MARKET CONDITIONS:
  SMH Price: $236.80
  Trend: Weak Uptrend
  IV Rank: 21.88% (Low)
  Volatility: Below average
  
RATIONALE:
  - Low IV favors buying options
  - Weak uptrend supports bullish bias
  - Defined risk through spread structure
  - Good risk/reward profile
  
EXECUTION INSTRUCTIONS:
  1. Find 235 Call expiring Dec 26
  2. Find 245 Call expiring Dec 26
  3. Buy 235 Call at ask price
  4. Sell 245 Call at bid price
  5. Net debit should be ~$3.20 per spread
  
=================================================
```

---

## Step 5: Execute Trade with Real Options

### Find Matching Options in Today's Chain

**Model Prediction:**
- Strategy: BULL_CALL_SPREAD
- Long Strike: 235
- Short Strike: 245  
- DTE: 21

**Search Today's Option Chain:**

```
Looking for: Calls expiring in ~21 days (Dec 26, 2024)

Found Options:
Ticker: O:SMH241226C00235000
  Strike: 235
  Type: Call
  Expiration: 2024-12-26
  DTE: 21
  Bid: 6.80
  Ask: 6.95
  Volume: 850
  Open Interest: 8500
  → This is the LONG leg

Ticker: O:SMH241226C00245000
  Strike: 245
  Type: Call
  Expiration: 2024-12-26
  DTE: 21
  Bid: 3.45
  Ask: 3.58
  Volume: 620
  Open Interest: 6200
  → This is the SHORT leg
```

### Calculate Entry Prices

```
Buy 235 Call:
  - Must pay ASK price: 6.95
  - Cost: $695 per contract

Sell 245 Call:
  - Receive BID price: 3.45
  - Credit: $345 per contract

Net Debit:
  - 695 - 345 = $350 per spread
  
Trade Metrics:
  - Max Profit: (245 - 235) × 100 - 350 = $650
  - Max Loss: $350 (net debit)
  - Breakeven: 235 + 3.50 = $238.50
  - Risk/Reward: 650/350 = 1.86:1
```

### Execute Orders

**Order 1: Buy 235 Call**
```
Order Type: BUY TO OPEN
Ticker: O:SMH241226C00235000
Quantity: 1 contract (100 shares)
Order: LIMIT at $6.95 (or MARKET)
Status: FILLED at $6.95
Cost: $695
```

**Order 2: Sell 245 Call**
```
Order Type: SELL TO OPEN
Ticker: O:SMH241226C00245000
Quantity: 1 contract (100 shares)
Order: LIMIT at $3.45 (or MARKET)
Status: FILLED at $3.45
Credit: $345
```

**Position Summary:**
```
Strategy: Bull Call Spread
Entry Date: 2024-12-05
Net Debit: $350
Max Profit: $650
Max Loss: $350
Expiration: 2024-12-26
Status: OPEN
```

---

## Complete Examples

### Example 1: Iron Condor Prediction

**Input (80 features - showing key ones):**
```json
{
  "current_price": 236.80,
  "return_1d": -0.0025,
  "iv_rank": 68.5,
  "adx_14": 18.2,
  "rsi_14": 52.3,
  "trend_regime": 2,
  "volatility_regime": 3,
  "put_call_volume_ratio": 0.895,
  ... (72 more features)
}
```

**Model Output:**
```json
{
  "strategy": {
    "type": "IRON_CONDOR"
  },
  "parameters": {
    "short_put": 220.0,
    "long_put": 215.0,
    "short_call": 252.0,
    "long_call": 257.0,
    "dte": 35
  },
  "expected_performance": {
    "expected_return": 0.0285,
    "win_probability": 0.72,
    "max_profit": 315.0,
    "max_loss": -185.0
  }
}
```

**Execution:**
```
Find Jan 10, 2025 options:
- Sell 220 Put at bid: 1.35
- Buy 215 Put at ask: 0.92
- Sell 252 Call at bid: 1.85
- Buy 257 Call at ask: 1.25

Net Credit: (1.35 + 1.85) - (0.92 + 1.25) = 1.03
Credit Received: $103 per iron condor
Max Risk: $397
```

---

### Example 2: Long Call Prediction

**Input (80 features - showing key ones):**
```json
{
  "current_price": 236.80,
  "return_1d": 0.0155,
  "iv_rank": 28.5,
  "adx_14": 28.8,
  "rsi_14": 68.2,
  "macd_histogram": 0.825,
  "trend_regime": 4,
  "volatility_regime": 1,
  "spy_correlation": 0.88,
  ... (72 more features)
}
```

**Model Output:**
```json
{
  "strategy": {
    "type": "LONG_CALL"
  },
  "parameters": {
    "strike": 240.0,
    "dte": 14
  },
  "expected_performance": {
    "expected_return": 0.0485,
    "win_probability": 0.58,
    "max_profit": 999999.0,
    "max_loss": -425.0
  }
}
```

**Execution:**
```
Find Dec 19, 2024 option:
- 240 Call
- Ask: 4.25

Buy 240 Call at $4.25
Cost: $425
Max Loss: $425
Potential: Unlimited
```

---

### Example 3: Long Straddle Prediction

**Input (80 features - showing key ones):**
```json
{
  "current_price": 236.80,
  "return_1d": 0.0008,
  "iv_rank": 32.5,
  "adx_14": 15.2,
  "rsi_14": 50.8,
  "volatility_trend": 0,
  "trend_regime": 2,
  "volatility_regime": 1,
  "days_to_earnings": 2,
  ... (72 more features)
}
```

**Model Output:**
```json
{
  "strategy": {
    "type": "LONG_STRADDLE"
  },
  "parameters": {
    "strike": 235.0,
    "dte": 8
  },
  "expected_performance": {
    "expected_return": 0.0625,
    "win_probability": 0.52,
    "max_profit": 999999.0,
    "max_loss": -925.0
  }
}
```

**Execution:**
```
Find Dec 13, 2024 options:
- 235 Put - Ask: 3.85
- 235 Call - Ask: 5.40

Buy both:
Total Cost: (3.85 + 5.40) × 100 = $925
Max Loss: $925
Need >$9.25 move to profit
```

---

## Input Validation Checklist

**Before feeding to model, verify:**

### Data Completeness
- [ ] All 80 features calculated
- [ ] No missing values (NaN)
- [ ] All features in correct order

### Data Quality
- [ ] Returns within reasonable range (-0.10 to +0.10)
- [ ] RSI between 0 and 100
- [ ] IV Rank between 0 and 100
- [ ] Correlations between -1 and +1
- [ ] No extreme outliers

### Data Types
- [ ] All features are numeric
- [ ] Regime values are integers (0-4)
- [ ] Boolean flags are 0 or 1
- [ ] No string values except in labels

### Feature Consistency
- [ ] Price features consistent with current price
- [ ] IV metrics align with volatility measures
- [ ] Trend indicators consistent with regime classification
- [ ] Volume metrics reasonable vs historical averages

---

## Output Interpretation Guide

### Confidence Levels

**Strategy Confidence:**
```
> 0.80 = High confidence, strong signal
0.60 - 0.80 = Moderate confidence, reasonable signal
0.40 - 0.60 = Low confidence, weak signal
< 0.40 = Very low confidence, consider skipping trade
```

### Win Probability

**Expected Win Rates:**
```
> 0.70 = Very high probability (Iron Condor in high IV)
0.60 - 0.70 = Good probability (typical for spreads)
0.50 - 0.60 = Moderate probability (directional plays)
< 0.50 = Low probability (speculative, higher risk/reward)
```

### Expected Return

**Return Expectations:**
```
> 0.05 = Excellent (5%+ return on capital)
0.03 - 0.05 = Good (3-5% return)
0.02 - 0.03 = Moderate (2-3% return)
< 0.02 = Low (consider if win probability is very high)
```

### Risk/Reward Ratio

**Interpretation:**
```
> 2.0 = Excellent risk/reward
1.5 - 2.0 = Good risk/reward
1.0 - 1.5 = Fair risk/reward
< 1.0 = Poor risk/reward (risk > reward)
```

---

## Daily Checklist

**Every trading day at 9:05 AM:**

### Step 1: Data Collection (5 min)
- [ ] Download current SMH price
- [ ] Get yesterday's option chain
- [ ] Fetch SPY and VIX data
- [ ] Retrieve 50-day price history

### Step 2: Feature Calculation (2 min)
- [ ] Run feature engineering script
- [ ] Verify all 80 features calculated
- [ ] Check for any NaN or errors
- [ ] Validate feature ranges

### Step 3: Model Input (1 min)
- [ ] Format features as CSV/JSON/Array
- [ ] Save input file
- [ ] Verify 80 values present

### Step 4: Get Prediction (Instant)
- [ ] Feed input to model
- [ ] Receive prediction output
- [ ] Review strategy and parameters
- [ ] Check confidence and metrics

### Step 5: Execute Trade (5-10 min)
- [ ] Find matching options in chain
- [ ] Verify strikes and expiration
- [ ] Check bid/ask spreads
- [ ] Calculate net debit/credit
- [ ] Place orders
- [ ] Confirm fills
- [ ] Log position

### Step 6: Risk Management
- [ ] Verify position size < 5% of portfolio
- [ ] Confirm max loss within limits
- [ ] Set alerts for exit conditions
- [ ] Update tracking spreadsheet

---

## Summary

### Input Summary
- **Format**: 80 numeric features
- **Source**: Calculated from raw market data (not raw data itself)
- **Order**: Must match training data column order
- **Types**: All numeric (floats and integers)

### Output Summary
- **Strategy**: One of 10 strategy types
- **Parameters**: Strikes, DTE specific to strategy
- **Metrics**: Expected return, win probability, max profit/loss
- **Format**: JSON, CSV, or text summary

### Key Points
1. Model does NOT take raw option chains as input
2. You must calculate 80 features first
3. Features describe market conditions, not individual options
4. Model output gives guidelines (strikes, DTE)
5. Use output to find actual options for execution
6. Actual prices may differ slightly from expectations

### The Process
```
Raw Data → Calculate Features → Format Input → Model Prediction → Find Options → Execute Trade
```

**This ensures the model sees the same type of data it was trained on and produces reliable, actionable predictions.**

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Purpose:** Guide for preparing model input and interpreting predictions
