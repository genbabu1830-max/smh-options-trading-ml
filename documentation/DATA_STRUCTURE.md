# Training Data Structure Issues & Corrections
## Analysis of SMH Sample Labeled Data

---

## Executive Summary

**Status:** Data contains good elements but has critical structural problems

**Main Issues:**
1. ❌ Mixing raw option-level data with aggregated features
2. ❌ Multiple rows per day (should be one row per day)
3. ❌ 100% win rate (unrealistic, indicates selection bias)
4. ❌ Missing ~40 features from the 80-feature target

**Required Action:** Restructure data pipeline to separate raw data collection from feature aggregation and label creation.

---

## Current Data Structure (Wrong)

### What Was Found in Sample Data

**Total Columns:** 100
**Total Rows:** 10 (representing 10 days)

**Columns Present:**
- Labels: date, strategy, score, pnl, max_loss, days_held, exit_type, win ✓
- Strategy Parameters: strikes for each strategy type ✓
- Price Features: 22 features (returns, SMAs, Bollinger Bands) ✓
- Volatility Features: 7 features (IV rank, HV, VIX) ✓
- Greek Features: 4 features (delta, gamma, theta, vega) ✓
- Technical Indicators: 4 features (RSI, MACD, ADX, ATR) ✓
- **PROBLEM:** Raw option contract data mixed in ❌

---

### Critical Structural Problems

#### Problem 1: Individual Option Contract Data Present

**These columns should NOT be in training data:**

```
ticker: "O:SMH240308C00190000"
  → This is a SINGLE option contract identifier
  → Training data should have DAY-LEVEL aggregates, not individual contracts

volume: 4, open: 27.35, close: 31.45, high: 31.45, low: 27.35
  → These are OHLCV for ONE specific option contract
  → Should aggregate ALL options into features like "average_volume"

transactions: 4
  → Number of trades for ONE option contract
  → Should aggregate: "total_option_transactions" across all relevant options

window_start: 1709269200000000000
  → Unix timestamp for ONE option bar
  → Only need the trading date

underlying: "SMH", expiration: "2024-03-08", type: "call", strike: 190.0
  → Identifier fields for ONE specific option
  → These describe one option in the chain, not the day's market conditions

expiration_date: "2024-03-08", dte_y: 7
  → Data for ONE specific option's expiration
  → Should have aggregated metrics like "avg_dte_of_liquid_options"
```

**Why This Is Wrong:**

Your training data should describe the MARKET CONDITIONS on each day, not individual option contracts. When you predict, you're not predicting "what happened to the 190 call" - you're predicting "what strategy and parameters are optimal given TODAY'S market conditions."

Think of it like weather prediction:
- ❌ Wrong: Including individual raindrop measurements
- ✓ Right: Aggregate metrics like rainfall amount, humidity, temperature

---

#### Problem 2: Data Represents Individual Options, Not Trading Days

**Current Structure:**
```
Each row = One option contract from one day + some day features + labels

Example row represents:
- The SMH March 8 190 Call contract (ticker: O:SMH240308C00190000)
- Its OHLCV (open: 27.35, close: 31.45, volume: 4)
- Plus some aggregated market features
- Plus simulation labels
```

**This creates confusion:**
- Is this row about March 1st market conditions? 
- Or is it about the 190 Call contract?
- How do you handle the 200+ other options that existed that day?

**The Problem:**
On March 1, 2024, SMH had approximately 150-200 liquid option contracts across different strikes and expirations. Your current structure seems to pick ONE contract and attach that day's features to it. This is incorrect because:

1. The model needs to see AGGREGATE conditions, not individual contracts
2. You can't train on individual option performance - that's look-ahead bias
3. Multiple rows for the same day with different options creates data leakage

---

#### Problem 3: 100% Win Rate

**Found:** 10/10 trades won = 100% win rate

**This is unrealistic and indicates a problem:**

Real-world expected win rates by strategy:
- Iron Condor: 65-75%
- Long Call/Put: 50-60%
- Spreads: 55-65%
- Straddles: 45-55%

**Possible causes:**
1. **Cherry-picking winners:** Only storing simulations that won, discarding losses
2. **Insufficient testing:** Not testing enough parameter combinations
3. **Overfitting:** Selecting parameters that won on that specific day without generalizing
4. **Look-ahead bias:** Using future information to select "winning" options

**Why this matters:**
A model trained only on winning scenarios will:
- Overestimate win probability
- Take excessive risk
- Fail in real trading when losses occur
- Not learn proper risk management

**The fix:**
Test 15-20 parameter combinations per strategy per day. Select the BEST one using risk-adjusted scoring, even if its historical win rate is only 60-70%. The model must learn from realistic win/loss patterns.

---

#### Problem 4: Missing ~40 Features

**You have ~40 features, need 80+ for robust predictions.**

**Missing feature categories:**

1. **Volume Analysis:**
   - Volume relative to 20-day average
   - Volume trend (increasing/decreasing)
   - Volume distribution across strikes
   - Unusual volume indicators

2. **Options-Specific Metrics:**
   - Put/Call volume ratio (aggregated)
   - Put/Call open interest ratio (aggregated)
   - Skew metrics (OTM put IV vs OTM call IV)
   - Term structure (near-term IV vs longer-term IV)
   - Max pain strike and distance to it

3. **Support/Resistance Levels:**
   - Recent high (resistance)
   - Recent low (support)  
   - Distance to resistance
   - Distance to support
   - Position in recent range

4. **Market Context:**
   - SPY correlation (30-day rolling)
   - SPY relative performance
   - Sector rotation indicators
   - Market breadth metrics

5. **Regime Classification:**
   - Trend regime: strong_up, weak_up, ranging, weak_down, strong_down
   - Volatility regime: very_low, low, normal, elevated, very_high
   - Volume regime: low, normal, high
   - Combined market state

6. **Greeks Aggregation:**
   - You have individual Greeks, but need aggregates:
   - Average delta for ATM options
   - Average gamma for ATM options
   - Average theta for ATM options
   - Average vega for ATM options
   - Weighted by open interest or volume

7. **Time-Based Features:**
   - Days to next earnings (if applicable)
   - Days since last earnings
   - Day of week effect
   - Month effect
   - Quarter effect

---

## Correct Data Structure

### Proper Three-Stage Pipeline

#### Stage 1: Raw Data Collection (NOT in training data)

**Purpose:** Collect all raw market data

**What to collect:**
- Complete option chain for SMH (filtered: ±15% strikes, 7-90 DTE)
- All option contracts with their OHLCV
- All option contracts with their Greeks (delta, gamma, theta, vega)
- Underlying SMH price data (OHLCV)
- Market data (VIX, SPY)

**Storage:** 
- Store in database or separate files
- Keep as reference for simulation
- DO NOT include in training CSV directly

**Example (stored separately):**
```
Date: 2024-03-01
SMH Price: $205.89

Option Chain (150+ options):
Ticker                    | Strike | Type | DTE | Volume | OI    | IV    | Delta | ...
O:SMH240308C00190000     | 190    | call | 7   | 4      | 1250  | 0.32  | 0.99  | ...
O:SMH240308C00195000     | 195    | call | 7   | 12     | 2100  | 0.29  | 0.95  | ...
O:SMH240308C00200000     | 200    | call | 7   | 45     | 5600  | 0.26  | 0.85  | ...
... (147 more options)
```

This data is used for:
1. Calculating aggregated features
2. Running simulations
3. Getting option prices for strategy entries

**But is NOT directly in the training CSV.**

---

#### Stage 2: Feature Engineering (Aggregation)

**Purpose:** Convert raw option chain + market data into 80 day-level features

**Process:** For each trading day, calculate:

1. **From option chain → Aggregate metrics:**

```
Example: IV Rank
- Look at ALL options (ATM ±2 strikes)
- Calculate current average IV: 0.285
- Compare to 52-week range: low=0.18, high=0.42
- IV Rank = (0.285 - 0.18) / (0.42 - 0.18) × 100 = 43.75%
- Store: iv_rank = 43.75

Example: Put/Call Volume Ratio  
- Sum all put volumes today: 45,230
- Sum all call volumes today: 62,150
- Put/Call Ratio = 45,230 / 62,150 = 0.728
- Store: put_call_volume_ratio = 0.728

Example: ATM Greeks (aggregated)
- Find ATM options (strike closest to current price)
- Average their Greeks across multiple contracts
- ATM Call delta avg: 0.52, ATM Put delta avg: -0.48
- Store: atm_delta_call = 0.52, atm_delta_put = -0.48
```

2. **From price data → Technical features:**

```
Example: RSI
- Calculate from SMH daily close prices
- 14-period RSI
- Store: rsi_14 = 61.18

Example: Price vs SMA
- Current price: 205.89
- 20-day SMA: 199.24
- Percent above SMA = (205.89 - 199.24) / 199.24 = 3.34%
- Store: price_vs_sma_20 = 0.0334
```

3. **From multiple sources → Derived features:**

```
Example: Regime Classification
- ADX = 17.8 (ranging)
- Price vs SMA20 = +3.34% (slight uptrend)
- RSI = 61.18 (neutral-bullish)
- Decision: "ranging" market
- Store: trend_regime = "ranging" (or encode as numeric: 2)

Example: Volatility Regime  
- IV Rank = 50%
- HV/IV Ratio = 0.87 (IV > HV)
- VIX = 15
- Decision: "normal" volatility
- Store: volatility_regime = "normal" (or encode as numeric: 1)
```

**Result:** One row with 80 features representing March 1, 2024 market conditions:

```
Date: 2024-03-01
current_price: 205.89
return_1d: 0.0106
return_5d: 0.0300
rsi_14: 61.18
macd: 2.247
adx_14: 17.80
iv_rank: 50.0
iv_percentile: 44.84
hv_20d: 0.253
put_call_volume_ratio: 0.728
put_call_oi_ratio: 0.868
atm_delta_call: 0.52
... (68 more features)
trend_regime: 2 (ranging)
volatility_regime: 1 (normal)
```

**No ticker, no individual option data, just pure aggregated market conditions.**

---

#### Stage 3: Label Creation (Simulation)

**Purpose:** Determine optimal strategy and parameters for this day

**Process:**

1. **Apply rules engine to features:**
   - Input: The 80 features from March 1
   - Output: Selected strategy (e.g., "IRON_CONDOR")

2. **Generate parameter combinations:**
   - For Iron Condor, test 20 different configurations:
   - Combination 1: 195P/190P/225C/230C, 35 DTE
   - Combination 2: 200P/195P/220C/225C, 35 DTE  
   - Combination 3: 195P/190P/225C/230C, 45 DTE
   - ... 17 more combinations

3. **Simulate each combination:**
   - Use the raw option chain data (from Stage 1)
   - Look forward to see what happened
   - Calculate P&L, win/loss, days held, exit type

4. **Calculate statistics for each:**
   - Combo 1: Win rate 72%, Avg profit $140, Max loss $220, Score 0.275
   - Combo 2: Win rate 65%, Avg profit $220, Max loss $380, Score 0.118
   - ... results for all 20 combos

5. **Select best via risk-adjusted scoring:**
   - Highest score: Combo 1 with score 0.275
   - This becomes the label for March 1

**Label output:**
```
strategy: IRON_CONDOR
short_put: 195
long_put: 190
short_call: 225
long_call: 230
dte: 35
risk_adjusted_score: 0.275
expected_return: 0.0224
win_probability: 0.72
max_loss: -220
simulation_days_held: 18
simulation_pnl: 140
simulation_exit_type: profit_target
simulation_win: True
```

**Important:** The simulation results (simulation_*) are from testing this specific combo on similar historical days, NOT just this single day. That's why win probability can be 72% instead of 100%.

---

#### Stage 4: Combine Features + Labels

**Purpose:** Create final training dataset

**Structure:** One row per day

```csv
date,current_price,return_1d,return_5d,rsi_14,macd,adx_14,iv_rank,...(70 more features),strategy,short_put,long_put,short_call,long_call,dte,risk_adjusted_score,expected_return,win_probability,max_loss
2024-03-01,205.89,0.0106,0.0300,61.18,2.247,17.80,50.0,...,IRON_CONDOR,195,190,225,230,35,0.275,0.0224,0.72,-220
2024-03-04,205.70,-0.0009,0.0167,60.80,2.413,18.30,50.0,...,IRON_CONDOR,200,195,220,225,35,0.312,0.0198,0.68,-280
2024-03-05,203.73,-0.0096,0.0,56.77,2.342,18.57,...,LONG_CALL,215,,,,14,0.185,0.0315,0.58,-350
```

**Total columns:** ~90
- 80 features (market conditions)
- ~10 label columns (optimal strategy + parameters + metrics)

**Total rows:** 504 (one per trading day in your dataset)

**Key characteristics:**
- ✓ One row = one trading day
- ✓ No individual option contract data
- ✓ Only aggregated features
- ✓ Labels show optimal strategy for that day's conditions
- ✓ Win probability is realistic (55-75%, not 100%)

---

## Detailed Comparison

### Wrong Structure (Current)

```
Columns (100 total):
├── Labels (8)
│   ├── date
│   ├── strategy  
│   ├── score
│   └── ... other labels
│
├── RAW Option Data (12) ❌ SHOULD NOT BE HERE
│   ├── ticker: "O:SMH240308C00190000"
│   ├── volume: 4
│   ├── open: 27.35
│   ├── close: 31.45
│   ├── high: 31.45
│   ├── low: 27.35
│   ├── transactions: 4
│   ├── window_start: timestamp
│   ├── underlying: "SMH"
│   ├── expiration: "2024-03-08"
│   ├── type: "call"
│   └── strike: 190.0
│
├── Some Aggregated Features (40)
│   ├── current_price ✓
│   ├── return_1d ✓
│   ├── rsi_14 ✓
│   └── ... others
│
└── Strategy Parameters (8)
    ├── dte_x, dte_y (duplicates)
    ├── long_strike, short_strike
    └── various strike/price fields

Problems:
1. Mixing individual option data with aggregates
2. Unclear what the row represents (a day? an option?)
3. Only ~40 features instead of 80
4. 100% win rate (selection bias)
```

---

### Right Structure (Target)

```
Columns (90 total):
├── Date Identifier (1)
│   └── date
│
├── Aggregated Features (80) ✓ CLEAN DAY-LEVEL DATA
│   ├── Price Features (20)
│   │   ├── current_price
│   │   ├── return_1d, return_3d, return_5d, return_10d, return_20d, return_50d
│   │   ├── sma_5, sma_10, sma_20, sma_50, sma_200
│   │   ├── price_vs_sma_5, price_vs_sma_10, price_vs_sma_20, price_vs_sma_50, price_vs_sma_200
│   │   ├── bb_upper, bb_middle, bb_lower, bb_position
│   │   └── sma_alignment (boolean: all SMAs aligned)
│   │
│   ├── Technical Indicators (15)
│   │   ├── rsi_14
│   │   ├── macd, macd_signal, macd_histogram
│   │   ├── adx_14
│   │   ├── atr_14
│   │   ├── volume_20d_avg, volume_vs_avg
│   │   ├── obv (on-balance volume)
│   │   ├── stochastic_k, stochastic_d
│   │   ├── cci (commodity channel index)
│   │   ├── williams_r
│   │   └── mfi (money flow index)
│   │
│   ├── Volatility Features (15)
│   │   ├── hv_20d (historical volatility)
│   │   ├── iv_atm (implied vol at-the-money)
│   │   ├── iv_rank (0-100 scale)
│   │   ├── iv_percentile (0-100 scale)
│   │   ├── hv_iv_ratio
│   │   ├── iv_skew (OTM put IV - OTM call IV)
│   │   ├── iv_term_structure (near vs far IV)
│   │   ├── vix_level
│   │   ├── vix_change
│   │   ├── vix_vs_ma20
│   │   ├── volatility_trend (increasing/decreasing)
│   │   ├── garch_forecast (if using GARCH)
│   │   ├── parkinson_vol (high-low volatility)
│   │   ├── garman_klass_vol
│   │   └── volatility_of_volatility
│   │
│   ├── Options Metrics (15)
│   │   ├── put_call_volume_ratio
│   │   ├── put_call_oi_ratio
│   │   ├── total_volume (all options)
│   │   ├── total_open_interest
│   │   ├── atm_delta_call (average)
│   │   ├── atm_delta_put (average)
│   │   ├── atm_gamma (average)
│   │   ├── atm_theta (average)
│   │   ├── atm_vega (average)
│   │   ├── max_pain_strike
│   │   ├── distance_to_max_pain (%)
│   │   ├── gamma_exposure (aggregate)
│   │   ├── delta_exposure (aggregate)
│   │   ├── unusual_options_activity (boolean)
│   │   └── options_flow_sentiment (bullish/bearish score)
│   │
│   ├── Support/Resistance (10)
│   │   ├── resistance_level_1 (recent high)
│   │   ├── resistance_level_2
│   │   ├── support_level_1 (recent low)
│   │   ├── support_level_2
│   │   ├── distance_to_resistance_1 (%)
│   │   ├── distance_to_support_1 (%)
│   │   ├── position_in_range (0-1 scale)
│   │   ├── range_width (%)
│   │   ├── days_in_range
│   │   └── breakout_probability (derived)
│   │
│   ├── Market Context (10)
│   │   ├── spy_correlation (30-day rolling)
│   │   ├── spy_return_1d
│   │   ├── spy_return_5d
│   │   ├── smh_vs_spy (relative strength)
│   │   ├── sector_rotation_score
│   │   ├── market_breadth (advance/decline)
│   │   ├── vix_vs_vvix (volatility of volatility)
│   │   ├── treasury_yield_10y
│   │   ├── yield_curve_slope
│   │   └── risk_on_risk_off_indicator
│   │
│   └── Regime Classification (5)
│       ├── trend_regime (strong_up=4, weak_up=3, ranging=2, weak_down=1, strong_down=0)
│       ├── volatility_regime (very_high=4, elevated=3, normal=2, low=1, very_low=0)
│       ├── volume_regime (high=2, normal=1, low=0)
│       ├── combined_market_state (categorical or encoded)
│       └── days_since_regime_change
│
└── Labels (9) ✓ OPTIMAL STRATEGY FOR THIS DAY
    ├── strategy (IRON_CONDOR, LONG_CALL, etc.)
    ├── Strategy-specific parameters (varies):
    │   For Iron Condor: short_put, long_put, short_call, long_call, dte
    │   For Long Call: strike, dte
    │   For Spreads: long_strike, short_strike, dte
    ├── risk_adjusted_score (0-1, higher is better)
    ├── expected_return (% of portfolio)
    ├── win_probability (0.55-0.75 typically)
    ├── max_loss ($ per contract)
    └── avg_days_held (from simulation)

Characteristics:
✓ One row = one trading day
✓ All data is aggregated (no individual options)
✓ Clean separation: features describe market, labels prescribe action
✓ Win probabilities are realistic (not 100%)
✓ Ready for ML training
```

---

## Why The Structure Matters

### The Prediction Task

**What you're building:**
A model that says: "Given TODAY'S market conditions (features), what strategy and parameters should I use (labels)?"

**Not:**
"Given this specific option contract's data, what happened to it?"

**Analogy:**

Think of it like a chess engine:

❌ **Wrong approach:**
- Training data: Individual piece positions and what happened to each piece
- "The knight at e4 moved to f6 and survived"
- "The pawn at d5 was captured"
- This doesn't teach the engine to play chess

✓ **Right approach:**
- Training data: Complete board state (aggregated position)
- Label: Best move given that position
- "When board looks like THIS, the best move is Nf6"
- This teaches strategic decision-making

**Same for options:**

❌ **Wrong:** "The 190 Call had volume of 4 and closed at 31.45"
- This is one piece of data from one option
- Doesn't describe the overall market
- Can't generalize to future decisions

✓ **Right:** "When IV Rank is 50%, ADX is 17, trend is ranging, the optimal strategy is Iron Condor with these strikes"
- Describes complete market state
- Provides actionable strategy
- Can generalize to similar future conditions

---

### The Training Process

**With wrong structure:**
```
Model sees: ticker="O:SMH240308C00190000", volume=4, close=31.45, ...
Model learns: "When I see this ticker and this volume, use Iron Condor"

Problem: Next day has different tickers (new option contracts)
         Model can't generalize
         Prediction fails
```

**With right structure:**
```
Model sees: iv_rank=50%, adx=17.8, rsi=61.2, ranging market, ...
Model learns: "When IV is moderate, market is ranging, momentum neutral, use Iron Condor with wide wings"

Next day: Different option contracts but similar conditions
         Model recognizes the pattern
         Makes accurate prediction
```

---

### Data Leakage Prevention

**Current structure risk:**

If you have multiple rows for the same day (different options), the model can "cheat":
```
2024-03-01, option A, features..., IRON_CONDOR
2024-03-01, option B, features..., IRON_CONDOR
2024-03-01, option C, features..., IRON_CONDOR
```

During training/validation split, if some March 1 rows are in training and others in validation, the model sees the same day in both sets. This is data leakage.

**Correct structure prevents this:**
```
2024-03-01, aggregated features..., IRON_CONDOR
```

One row per day ensures clean temporal splitting. Training uses past days, validation uses future days, no overlap.

---

## How to Fix Your Pipeline

### Step 1: Keep Raw Data Separate

**Create a separate storage system for raw options data:**

```
Directory structure:
/data
  /raw
    /options_chains
      2024-03-01_smh_options.parquet
      2024-03-04_smh_options.parquet
      ...
    /underlying
      smh_daily_bars.csv
    /market
      spy_daily.csv
      vix_daily.csv
```

**Do not mix this with training data.**

---

### Step 2: Build Aggregation Functions

**Create functions that take raw data and output aggregated features:**

**Function 1: Calculate Price Features**
- Input: SMH daily price history
- Output: returns, SMAs, Bollinger Bands, price vs SMA ratios
- One value per feature per day

**Function 2: Calculate Technical Indicators**
- Input: SMH daily price history
- Output: RSI, MACD, ADX, ATR, volume metrics
- One value per feature per day

**Function 3: Calculate Volatility Features**
- Input: SMH prices + option chain for the day
- Process: 
  - Historical volatility from price data
  - IV metrics from options (ATM IV average)
  - IV Rank/Percentile from 52-week IV range
  - HV/IV ratio
  - VIX data
- Output: One value per volatility feature per day

**Function 4: Calculate Options Metrics**
- Input: Complete option chain for the day
- Process:
  - Sum all put volumes, sum all call volumes → Put/Call ratio
  - Sum all put OI, sum all call OI → Put/Call OI ratio
  - Find ATM options (±2 strikes from current price)
  - Average their Greeks → ATM delta, gamma, theta, vega
  - Calculate max pain strike
- Output: One value per options metric per day

**Function 5: Calculate Support/Resistance**
- Input: SMH price history (last 20-60 days)
- Process:
  - Find recent highs → Resistance levels
  - Find recent lows → Support levels
  - Calculate distances
  - Determine position in range
- Output: Support/resistance metrics for the day

**Function 6: Calculate Market Context**
- Input: SMH, SPY, VIX data
- Process:
  - Rolling correlation between SMH and SPY
  - Relative performance
  - VIX levels and changes
- Output: Market context features for the day

**Function 7: Classify Regimes**
- Input: All calculated features
- Process:
  - Trend: Use ADX, MACD, price vs SMAs → Classify as strong_up/weak_up/ranging/weak_down/strong_down
  - Volatility: Use IV Rank, HV/IV ratio → Classify as very_high/elevated/normal/low/very_low
  - Volume: Compare to average → Classify as high/normal/low
- Output: Regime classifications for the day

**Result:** One row with 80 features for each day

---

### Step 3: Restructure Label Creation

**Current problem:** Appears to be selecting winning options retrospectively

**Correct approach:**

**For each day:**

1. **Calculate all 80 features** (as above)

2. **Apply rules engine:**
   - Input: The 80 features
   - Decision logic: Based on IV rank, trend, momentum
   - Output: Selected strategy (e.g., IRON_CONDOR)

3. **Generate parameter variations:**
   - Create 15-20 different parameter sets for the selected strategy
   - Example for Iron Condor:
     - Variation 1: Short strikes at ±7%, wings 5 wide, 35 DTE
     - Variation 2: Short strikes at ±10%, wings 5 wide, 35 DTE
     - Variation 3: Short strikes at ±7%, wings 7 wide, 35 DTE
     - ... 15 more variations

4. **Simulate EACH variation:**
   - Use raw option chain data to get entry prices
   - Look forward through historical data
   - Track daily position value
   - Apply exit rules (profit target, stop loss, expiration)
   - Record outcome: P&L, days held, exit type, win/loss

5. **Test on similar historical scenarios:**
   - Find 20-50 past days with similar conditions (same IV rank ±10, same trend regime, etc.)
   - Run the same variation on those days
   - Calculate aggregate statistics:
     - Win rate: 14 won, 6 lost = 70%
     - Avg profit when won: $180
     - Avg loss when lost: $240
     - Max loss observed: $320

6. **Calculate risk-adjusted score for each variation:**
   - Expected Value = (180 × 0.70) + (-240 × 0.30) = 126 - 72 = $54
   - Score = 54 / 320 = 0.169
   - Apply bonuses/penalties based on win rate, risk %, etc.

7. **Select best variation:**
   - Variation with highest risk-adjusted score becomes the label
   - Even if its win rate is 65% (not 100%)

8. **Store label:**
   ```
   strategy: IRON_CONDOR
   short_put: 195
   long_put: 190  
   short_call: 225
   long_call: 230
   dte: 35
   risk_adjusted_score: 0.275
   win_probability: 0.65  ← Realistic!
   expected_return: 0.0169
   max_loss: -320
   ```

**Key difference:** You're not storing "what happened" to individual options. You're storing "what would have been the optimal strategy given the market conditions, based on backtesting."

---

### Step 4: Combine into Clean CSV

**Final step:**

For each day:
- Take the 80 aggregated features
- Append the optimal strategy labels
- Write as one row
- No raw option data, no individual contract info

**Output:**
```csv
date,current_price,return_1d,...(78 more features),strategy,short_put,long_put,short_call,long_call,dte,score,win_probability,max_loss
2024-03-01,205.89,0.0106,...,IRON_CONDOR,195,190,225,230,35,0.275,0.65,-320
2024-03-04,205.70,-0.0009,...,IRON_CONDOR,200,195,220,225,35,0.312,0.68,-280
2024-03-05,203.73,-0.0096,...,LONG_CALL,215,,,14,0.185,0.58,-350
...
```

**Clean, ready for ML training.**

---

## Expected Characteristics of Final Data

### Dimensions
- **Rows:** 504 (one per trading day)
- **Columns:** ~90 total
  - 1 date column
  - 80 feature columns (aggregated market conditions)
  - 9 label columns (optimal strategy + parameters + metrics)

### Data Types
- Date: datetime or string "YYYY-MM-DD"
- Features: All numeric (floats or integers)
  - Some may be encoded categoricals (trend_regime: 0-4)
- Labels:
  - strategy: categorical string
  - Parameters: numeric (strikes, DTE)
  - Metrics: numeric (scores, probabilities)

### Data Quality Checks

**Features:**
- ✓ No NaN values (or minimal, handled appropriately)
- ✓ All values in reasonable ranges
  - Returns: -0.10 to +0.10 (±10% daily)
  - RSI: 0 to 100
  - IV Rank: 0 to 100
  - Correlations: -1 to +1
- ✓ No outliers (or documented/capped)
- ✓ Features make sense (RSI=150 would be an error)

**Labels:**
- ✓ Strategy present for every day
- ✓ Parameters appropriate for strategy
  - Iron Condor: Has 4 strikes + DTE
  - Long Call: Has 1 strike + DTE
- ✓ Win probability: 0.50 to 0.80 (realistic range)
- ✓ Risk-adjusted score: 0.05 to 0.50 (typical range)
- ✓ Mix of strategies (not all Iron Condor)

**Distribution:**
- ✓ Win probability distribution:
  - Mean: 0.60-0.65
  - Std: 0.05-0.10
  - Range: 0.50-0.75
  - NOT all 0.70 or all 1.0
- ✓ Strategy distribution:
  - Iron Condor: 35-45% (most common)
  - Directional: 30-40% combined
  - Volatility: 15-25% combined
  - Good variety, not 90% one strategy

---

## Validation Checklist

**Before using data for training, verify:**

### Structure Validation
- [ ] One row per day (504 rows)
- [ ] 80+ feature columns, all numeric/encoded
- [ ] 9 label columns present
- [ ] No individual option contract data (ticker, option OHLCV)
- [ ] No duplicate dates
- [ ] Dates in chronological order

### Feature Validation
- [ ] All 80 features calculated correctly
- [ ] No excessive NaN values (<1%)
- [ ] Features in valid ranges
- [ ] Correlations between features make sense
- [ ] Features are aggregated (not individual option data)

### Label Validation
- [ ] All strategies represented (not just one or two)
- [ ] Win probabilities realistic (55-75%, not 100%)
- [ ] Risk-adjusted scores positive
- [ ] Parameters appropriate for each strategy
- [ ] Max losses within risk limits

### Quality Checks
- [ ] No look-ahead bias (features only use past data)
- [ ] No data leakage (one row per day prevents overlap)
- [ ] Temporal consistency (earlier dates have earlier data only)
- [ ] Strategy selection makes sense for conditions
  - High IV → Iron Condor ✓
  - Strong trend + Low IV → Long Call/Put ✓
  - Pre-catalyst → Straddle ✓

---

## Complete Sample Data Formats for Each Stage

### Stage 1: Raw Options Data Collection (Separate Storage)

**File:** `2024-03-01_smh_options.csv`

**Purpose:** Store complete option chain for the day (NOT in training data)

**Format Specification:**
- Storage: CSV or Parquet files, one per day
- Rows: 100-200 options per day (filtered for liquidity and DTE)
- Location: `/data/raw/options_chains/`

**Complete Column Set (25 columns):**

```csv
date,ticker,underlying,strike,expiration,type,dte,open,high,low,close,volume,open_interest,bid,ask,bid_size,ask_size,implied_volatility,delta,gamma,theta,vega,midpoint,last_trade_time,underlying_price
2024-03-01,O:SMH240308P00190000,SMH,190.0,2024-03-08,put,7,0.18,0.22,0.18,0.20,125,3200,0.19,0.21,150,200,0.28,-0.15,0.08,-0.05,0.12,0.20,2024-03-01T15:55:00,205.89
2024-03-01,O:SMH240308P00195000,SMH,195.0,2024-03-08,put,7,0.35,0.42,0.34,0.38,450,5600,0.37,0.39,300,250,0.26,-0.25,0.11,-0.08,0.18,0.38,2024-03-01T15:58:00,205.89
2024-03-01,O:SMH240308P00200000,SMH,200.0,2024-03-08,put,7,0.68,0.78,0.66,0.72,890,8900,0.70,0.74,400,350,0.24,-0.38,0.13,-0.12,0.22,0.72,2024-03-01T15:59:00,205.89
2024-03-01,O:SMH240308P00205000,SMH,205.0,2024-03-08,put,7,1.25,1.38,1.22,1.32,1200,12000,1.30,1.34,500,450,0.23,-0.52,0.14,-0.16,0.24,1.32,2024-03-01T15:59:00,205.89
2024-03-01,O:SMH240308C00205000,SMH,205.0,2024-03-08,call,7,2.10,2.35,2.08,2.25,1500,15000,2.22,2.28,600,550,0.22,0.54,0.14,-0.18,0.25,2.25,2024-03-01T15:59:00,205.89
2024-03-01,O:SMH240308C00210000,SMH,210.0,2024-03-08,call,7,1.15,1.28,1.12,1.22,980,9500,1.20,1.24,450,400,0.24,0.40,0.13,-0.14,0.22,1.22,2024-03-01T15:58:00,205.89
2024-03-01,O:SMH240308C00215000,SMH,215.0,2024-03-08,call,7,0.55,0.62,0.54,0.58,520,6200,0.56,0.60,300,280,0.26,0.26,0.11,-0.10,0.18,0.58,2024-03-01T15:57:00,205.89
2024-03-01,O:SMH240308C00220000,SMH,220.0,2024-03-08,call,7,0.24,0.28,0.23,0.26,280,3800,0.25,0.27,200,180,0.28,0.14,0.08,-0.06,0.12,0.26,2024-03-01T15:56:00,205.89
... (92-192 more option rows for this day)
```

**Additional supporting files:**

**File:** `smh_daily_bars.csv`
```csv
date,open,high,low,close,volume,vwap
2024-02-29,204.50,206.20,203.80,204.72,45200000,205.10
2024-03-01,204.85,207.10,204.20,205.89,48300000,205.65
2024-03-04,205.50,206.80,205.10,205.70,42100000,206.15
2024-03-05,205.20,205.80,202.90,203.73,51200000,204.25
...
```

**File:** `market_data.csv`
```csv
date,spy_close,spy_volume,vix_close,treasury_10y,sector_rotation_score
2024-03-01,512.50,85000000,14.85,4.25,0.65
2024-03-04,513.25,78000000,15.10,4.28,0.62
2024-03-05,510.80,92000000,15.45,4.31,0.58
...
```

---

### Stage 2: Feature Engineering Output (Day-Level Aggregates)

**File:** `smh_features_daily.csv`

**Purpose:** Aggregated features calculated from raw data, one row per day

**Format Specification:**
- One row per trading day
- 80 feature columns (all numeric)
- No individual option data
- Ready for label joining

**Complete Column Set (81 columns: 1 date + 80 features):**

```csv
date,current_price,return_1d,return_3d,return_5d,return_10d,return_20d,return_50d,sma_5,sma_10,sma_20,sma_50,sma_200,price_vs_sma_5,price_vs_sma_10,price_vs_sma_20,price_vs_sma_50,price_vs_sma_200,sma_alignment,bb_upper,bb_middle,bb_lower,bb_position,rsi_14,macd,macd_signal,macd_histogram,adx_14,atr_14,obv,stochastic_k,stochastic_d,cci,williams_r,mfi,hv_20d,iv_atm,iv_rank,iv_percentile,hv_iv_ratio,iv_skew,iv_term_structure,vix_level,vix_change,vix_vs_ma20,volatility_trend,parkinson_vol,garman_klass_vol,vol_of_vol,put_call_volume_ratio,put_call_oi_ratio,total_option_volume,total_open_interest,atm_delta_call,atm_delta_put,atm_gamma,atm_theta,atm_vega,max_pain_strike,distance_to_max_pain,gamma_exposure,delta_exposure,unusual_activity,options_flow_sentiment,resistance_1,resistance_2,support_1,support_2,distance_to_resistance_1,distance_to_support_1,position_in_range,range_width,days_in_range,breakout_probability,spy_correlation,spy_return_1d,spy_return_5d,smh_vs_spy,sector_rotation,market_breadth,treasury_yield,yield_curve_slope,risk_on_off,trend_regime,volatility_regime,volume_regime,combined_state,days_since_regime_change
2024-03-01,205.89,0.0106,0.0092,0.0300,0.0071,0.0535,0.0445,203.42,201.49,199.24,197.57,185.32,0.0121,0.0218,0.0334,0.0421,0.1109,1,207.29,199.24,191.19,0.9131,61.18,2.247,1.727,0.520,17.80,3.530,425000000,68.5,65.2,142.5,-28.5,58.3,0.253,0.291,50.0,44.84,0.869,0.035,0.018,14.85,0.0,0.985,0,0.248,0.242,0.028,0.728,0.868,125000,485000,0.52,-0.48,0.14,-0.16,0.24,200.0,0.0286,0.245,-0.085,0,0.15,210.41,212.50,190.06,188.25,0.0219,0.0768,0.7733,0.1086,12,0.22,0.85,0.0094,0.0285,0.0012,0.65,0.58,4.25,0.85,0.72,2,1,1,5,3
2024-03-04,205.70,-0.0009,0.0167,0.0226,0.0200,0.0581,0.0237,204.33,201.89,199.80,197.67,185.45,0.0067,0.0189,0.0295,0.0406,0.1096,1,208.00,199.80,191.60,0.8596,60.80,2.413,1.868,0.544,18.30,3.448,428000000,72.3,68.8,155.8,-24.2,62.5,0.252,0.344,50.0,62.30,0.732,0.028,0.015,15.10,0.25,-1.015,0,0.245,0.238,0.025,0.770,0.841,118000,492000,0.54,-0.46,0.15,-0.18,0.26,202.5,0.0154,0.268,-0.092,0,0.18,210.41,212.50,191.02,189.50,0.0229,0.0717,0.7945,0.1029,15,0.18,0.85,-0.0010,0.0256,0.0003,0.68,0.55,4.28,0.82,0.75,2,1,0,4,6
2024-03-05,203.73,-0.0096,0.0000,-0.0013,0.0244,0.0614,0.0380,204.27,202.38,200.39,197.82,185.58,0.0027,0.0067,0.0167,0.0299,0.0978,1,207.91,200.39,192.87,0.7219,56.77,2.342,1.946,0.395,18.57,3.408,422000000,58.2,65.3,135.2,-38.5,54.8,0.249,0.323,50.0,50.79,0.771,0.032,0.020,15.45,0.35,-1.082,1,0.258,0.251,0.032,0.815,0.892,135000,498000,0.52,-0.48,0.16,-0.19,0.27,200.0,0.0186,0.285,-0.098,1,0.22,210.41,212.50,191.02,189.50,0.0328,0.0625,0.6544,0.1029,15,0.25,0.85,-0.0100,-0.0045,0.0004,0.72,0.52,4.31,0.78,0.68,2,1,1,5,0
...
```

**Data Types:**
- `date`: string (YYYY-MM-DD) or datetime
- All feature columns: float64
- Regime columns: int (encoded: 0-4)
- Boolean flags: int (0 or 1)

**Feature Ranges (validation):**
- Returns: typically -0.10 to +0.10
- RSI: 0 to 100
- MACD: -5 to +5
- ADX: 0 to 100
- IV Rank/Percentile: 0 to 100
- Ratios: 0 to 2 typically
- Correlations: -1 to +1
- Distances (%): 0 to 0.20

---

### Stage 3: Label Creation Output (Optimal Strategy per Day)

**File:** `smh_labels_daily.csv`

**Purpose:** Optimal strategy and parameters determined via simulation for each day

**Format Specification:**
- One row per trading day
- Strategy-specific parameter columns (some will be null depending on strategy)
- Performance metrics from simulation

**Complete Column Set (20 columns for comprehensive labeling):**

```csv
date,rules_selected_strategy,optimal_strategy,short_put,long_put,short_call,long_call,long_strike,short_strike,strike,put_strike,call_strike,center_strike,wing_width,near_dte,far_dte,dte,risk_adjusted_score,expected_return,win_probability,max_loss,max_profit,avg_days_held,simulations_tested,best_exit_type
2024-03-01,IRON_CONDOR,IRON_CONDOR,195.0,190.0,225.0,230.0,,,,,,,5,,35,0.275,0.0224,0.72,-220,280,18.5,20,profit_target
2024-03-04,IRON_CONDOR,IRON_CONDOR,200.0,195.0,220.0,225.0,,,,,,,5,,35,0.312,0.0198,0.68,-280,250,21.3,20,profit_target
2024-03-05,LONG_CALL,LONG_CALL,,,,,,215.0,,,,,,14,0.185,0.0315,0.58,-350,1500,8.2,18,profit_target
2024-03-06,BEAR_PUT_SPREAD,BEAR_PUT_SPREAD,,,,,207.5,205.0,,,,,,,9,0.228,0.0268,0.65,-250,250,12.8,16,expiration
2024-03-07,IRON_CONDOR,IRON_CONDOR,202.5,199.0,212.5,215.0,,,,,,,3,,11,0.405,0.0182,0.75,-300,290,15.2,18,profit_target
2024-03-08,LONG_PUT,LONG_PUT,,,,,,200.0,,,,,,,7,0.168,0.0288,0.56,-420,1800,6.5,15,profit_target
2024-03-11,BULL_CALL_SPREAD,BULL_CALL_SPREAD,,,,,210.0,215.0,,,,,,,14,0.245,0.0425,0.62,-180,320,9.8,17,profit_target
2024-03-12,IRON_BUTTERFLY,IRON_BUTTERFLY,,,,,,,,,,205.0,5,,35,0.198,0.0156,0.70,-450,500,22.5,19,expiration
2024-03-13,LONG_STRADDLE,LONG_STRADDLE,,,,,,,205.0,,,,,14,0.142,0.0385,0.52,-850,2500,3.2,12,profit_target
2024-03-14,CALENDAR_SPREAD,CALENDAR_SPREAD,,,,,,,210.0,,,,,14,45,0.188,0.0245,0.64,-180,350,19.8,15,near_expiration
...
```

**Parameter Usage by Strategy:**

| Strategy | Uses These Columns |
|----------|-------------------|
| IRON_CONDOR | short_put, long_put, short_call, long_call, dte |
| IRON_BUTTERFLY | center_strike, wing_width, dte |
| LONG_CALL | strike, dte |
| LONG_PUT | strike, dte |
| BULL_CALL_SPREAD | long_strike, short_strike, dte |
| BEAR_PUT_SPREAD | long_strike, short_strike, dte |
| LONG_STRADDLE | strike, dte |
| LONG_STRANGLE | put_strike, call_strike, dte |
| CALENDAR_SPREAD | strike, near_dte, far_dte |
| DIAGONAL_SPREAD | long_strike, short_strike, near_dte, far_dte |

**Note:** Unused columns for each strategy will be null/NaN.

**Label Metrics:**
- `risk_adjusted_score`: 0.05 to 0.50 typical range (higher is better)
- `expected_return`: 0.01 to 0.05 (1% to 5% of portfolio)
- `win_probability`: 0.50 to 0.80 (50% to 80%)
- `max_loss`: Negative values in dollars per contract
- `max_profit`: Positive values in dollars per contract
- `avg_days_held`: 5 to 35 days typically
- `simulations_tested`: How many parameter combinations were tested

---

### Stage 4: Final Training Dataset (Features + Labels Combined)

**File:** `smh_training_data.csv`

**Purpose:** Complete training dataset ready for ML model

**Format Specification:**
- One row per trading day
- Left join: features + labels on date
- 90 total columns (1 date + 80 features + 9 core labels)

**Sample showing first 20 columns + last 10 label columns:**

```csv
date,current_price,return_1d,return_3d,return_5d,return_10d,return_20d,return_50d,sma_5,sma_10,sma_20,sma_50,sma_200,price_vs_sma_5,price_vs_sma_10,price_vs_sma_20,price_vs_sma_50,price_vs_sma_200,sma_alignment,bb_upper,bb_middle,...(60 more feature columns),optimal_strategy,param_1,param_2,param_3,param_4,param_5,risk_adjusted_score,expected_return,win_probability,max_loss
2024-03-01,205.89,0.0106,0.0092,0.0300,0.0071,0.0535,0.0445,203.42,201.49,199.24,197.57,185.32,0.0121,0.0218,0.0334,0.0421,0.1109,1,207.29,199.24,...,IRON_CONDOR,195.0,190.0,225.0,230.0,35,0.275,0.0224,0.72,-220
2024-03-04,205.70,-0.0009,0.0167,0.0226,0.0200,0.0581,0.0237,204.33,201.89,199.80,197.67,185.45,0.0067,0.0189,0.0295,0.0406,0.1096,1,208.00,199.80,...,IRON_CONDOR,200.0,195.0,220.0,225.0,35,0.312,0.0198,0.68,-280
2024-03-05,203.73,-0.0096,0.0000,-0.0013,0.0244,0.0614,0.0380,204.27,202.38,200.39,197.82,185.58,0.0027,0.0067,0.0167,0.0299,0.0978,1,207.91,200.39,...,LONG_CALL,215.0,,,,14,0.185,0.0315,0.58,-350
2024-03-06,205.25,0.0075,0.0061,0.0158,0.0377,0.0711,0.0272,205.06,203.86,201.66,197.93,185.72,0.0009,0.0068,0.0178,0.0370,0.1053,1,208.30,201.66,...,BEAR_PUT_SPREAD,207.5,205.0,,,9,0.228,0.0268,0.65,-250
2024-03-07,206.96,0.0083,0.0083,0.0061,0.0159,0.0378,0.0272,205.51,204.56,202.19,198.04,185.86,0.0071,0.0117,0.0236,0.0451,0.1135,1,208.69,202.19,...,IRON_CONDOR,202.5,199.0,212.5,215.0,11,0.405,0.0182,0.75,-300
...
```

**Simplified Parameter Storage (Alternative):**

Since parameters vary by strategy, you might use a unified approach:

```csv
date,current_price,...(78 more features),strategy,param_1,param_2,param_3,param_4,param_5,score,expected_return,win_prob,max_loss
2024-03-01,205.89,...,IRON_CONDOR,195.0,190.0,225.0,230.0,35,0.275,0.0224,0.72,-220
2024-03-05,203.73,...,LONG_CALL,215.0,NaN,NaN,NaN,14,0.185,0.0315,0.58,-350
```

**Where:**
- For IRON_CONDOR: param_1=short_put, param_2=long_put, param_3=short_call, param_4=long_call, param_5=dte
- For LONG_CALL: param_1=strike, param_5=dte (others NaN)
- For SPREADS: param_1=long_strike, param_2=short_strike, param_5=dte (others NaN)

**Data Types:**
- All features: float64
- strategy: string (categorical)
- param_*: float64 (with NaN for unused)
- score, expected_return, win_prob: float64
- max_loss: float64 (negative values)

---

## Complete Transformation Example (One Day)

### Input: Raw Data for March 1, 2024

**From option chain file (150 options, showing 8):**
```
ticker,strike,type,dte,volume,oi,iv,delta,gamma,theta,vega,bid,ask,underlying_price
O:SMH240308P00190000,190.0,put,7,125,3200,0.28,-0.15,0.08,-0.05,0.12,0.19,0.21,205.89
O:SMH240308P00195000,195.0,put,7,450,5600,0.26,-0.25,0.11,-0.08,0.18,0.37,0.39,205.89
O:SMH240308P00200000,200.0,put,7,890,8900,0.24,-0.38,0.13,-0.12,0.22,0.70,0.74,205.89
O:SMH240308P00205000,205.0,put,7,1200,12000,0.23,-0.52,0.14,-0.16,0.24,1.30,1.34,205.89
O:SMH240308C00205000,205.0,call,7,1500,15000,0.22,0.54,0.14,-0.18,0.25,2.22,2.28,205.89
O:SMH240308C00210000,210.0,call,7,980,9500,0.24,0.40,0.13,-0.14,0.22,1.20,1.24,205.89
O:SMH240308C00215000,215.0,call,7,520,6200,0.26,0.26,0.11,-0.10,0.18,0.56,0.60,205.89
O:SMH240308C00220000,220.0,call,7,280,3800,0.28,0.14,0.08,-0.06,0.12,0.25,0.27,205.89
... (142 more options)
```

**From price history file:**
```
date,open,high,low,close,volume
2024-02-28,203.80,205.10,203.20,204.50,44500000
2024-02-29,204.50,206.20,203.80,204.72,45200000
2024-03-01,204.85,207.10,204.20,205.89,48300000
```

**From market data file:**
```
date,spy_close,vix_close
2024-03-01,512.50,14.85
```

---

### Processing: Feature Calculation

**Step 1: Price Features**
```python
# From price history
current_price = 205.89
return_1d = (205.89 - 204.72) / 204.72 = 0.0106
sma_20 = average(last_20_closes) = 199.24
price_vs_sma_20 = (205.89 - 199.24) / 199.24 = 0.0334
rsi_14 = calculate_rsi(prices, 14) = 61.18
... calculate all 20 price features
```

**Step 2: Volatility Features**
```python
# From option chain
atm_options = filter(options, strike between 203-208)
iv_values = [0.22, 0.23, 0.24, 0.26]
iv_atm = average(iv_values) = 0.2375

# From 52-week IV history
iv_52w_low = 0.18
iv_52w_high = 0.42
iv_rank = (0.2375 - 0.18) / (0.42 - 0.18) * 100 = 23.96 ≈ 24.0

hv_20d = calculate_historical_vol(prices, 20) = 0.253
hv_iv_ratio = 0.253 / 0.2375 = 1.065
... calculate all 15 volatility features
```

**Step 3: Options Metrics**
```python
# From option chain
put_volume = sum(all put volumes) = 45230
call_volume = sum(all call volumes) = 62150
put_call_volume_ratio = 45230 / 62150 = 0.728

atm_call_deltas = [0.54, 0.52, 0.48]  # for strikes 203-208
atm_delta_call = average(atm_call_deltas) = 0.52

atm_gammas = [0.14, 0.14, 0.13]
atm_gamma = average(atm_gammas) = 0.14
... calculate all 15 options metrics
```

**Step 4: Other Features**
```python
# Support/Resistance from price history
resistance_1 = max(prices, last_30_days) = 210.41
support_1 = min(prices, last_30_days) = 190.06
distance_to_resistance = (210.41 - 205.89) / 205.89 = 0.0219

# Market Context
spy_correlation = correlation(smh_returns, spy_returns, 30d) = 0.85
spy_return_1d = (512.50 - 511.55) / 511.55 = 0.0094

# Regime Classification
# Based on: adx=17.80 (ranging), price_vs_sma_20=3.34% (slight up), rsi=61.18
trend_regime = 2  # (ranging)
volatility_regime = 1  # (normal, based on iv_rank=24)
... calculate remaining features
```

---

### Output: Feature Row

**One row with 80 features:**
```csv
date,current_price,return_1d,return_3d,return_5d,return_10d,return_20d,return_50d,sma_5,sma_10,sma_20,sma_50,sma_200,price_vs_sma_5,price_vs_sma_10,price_vs_sma_20,price_vs_sma_50,price_vs_sma_200,sma_alignment,bb_upper,bb_middle,bb_lower,bb_position,rsi_14,macd,macd_signal,macd_histogram,adx_14,atr_14,obv,stochastic_k,stochastic_d,cci,williams_r,mfi,hv_20d,iv_atm,iv_rank,iv_percentile,hv_iv_ratio,iv_skew,iv_term_structure,vix_level,vix_change,vix_vs_ma20,volatility_trend,parkinson_vol,garman_klass_vol,vol_of_vol,put_call_volume_ratio,put_call_oi_ratio,total_option_volume,total_open_interest,atm_delta_call,atm_delta_put,atm_gamma,atm_theta,atm_vega,max_pain_strike,distance_to_max_pain,gamma_exposure,delta_exposure,unusual_activity,options_flow_sentiment,resistance_1,resistance_2,support_1,support_2,distance_to_resistance_1,distance_to_support_1,position_in_range,range_width,days_in_range,breakout_probability,spy_correlation,spy_return_1d,spy_return_5d,smh_vs_spy,sector_rotation,market_breadth,treasury_yield,yield_curve_slope,risk_on_off,trend_regime,volatility_regime,volume_regime,combined_state,days_since_regime_change
2024-03-01,205.89,0.0106,0.0092,0.0300,0.0071,0.0535,0.0445,203.42,201.49,199.24,197.57,185.32,0.0121,0.0218,0.0334,0.0421,0.1109,1,207.29,199.24,191.19,0.9131,61.18,2.247,1.727,0.520,17.80,3.530,425000000,68.5,65.2,142.5,-28.5,58.3,0.253,0.291,50.0,44.84,0.869,0.035,0.018,14.85,0.0,0.985,0,0.248,0.242,0.028,0.728,0.868,125000,485000,0.52,-0.48,0.14,-0.16,0.24,200.0,0.0286,0.245,-0.085,0,0.15,210.41,212.50,190.06,188.25,0.0219,0.0768,0.7733,0.1086,12,0.22,0.85,0.0094,0.0285,0.0012,0.65,0.58,4.25,0.85,0.72,2,1,1,5,3
```

---

### Label Creation: Simulation Process

**Step 1: Rules Engine Decision**
```python
# Input: The 80 features calculated above
# Key decision factors:
#   - iv_rank = 50.0 (moderate)
#   - adx_14 = 17.80 (ranging market, <20)
#   - trend_regime = 2 (ranging)
#   - rsi_14 = 61.18 (neutral)

# Decision: IRON_CONDOR (high IV + ranging market)
selected_strategy = "IRON_CONDOR"
```

**Step 2: Generate Parameter Combinations**
```python
# Test 20 different Iron Condor configurations
combos = [
    {short_put: 195, long_put: 190, short_call: 225, long_call: 230, dte: 35},
    {short_put: 200, long_put: 195, short_call: 220, long_call: 225, dte: 35},
    {short_put: 195, long_put: 190, short_call: 225, long_call: 230, dte: 45},
    ... (17 more combinations)
]
```

**Step 3: Simulate Each (showing combo #1)**
```python
# Combo 1: 195P/190P/225C/230C, 35 DTE
# Entry March 1, expiration April 5

# Get entry prices from option chain
short_put_195_price = 0.38  # From raw data
long_put_190_price = 0.20
short_call_225_price = 1.30
long_call_230_price = 0.95

entry_credit = (0.38 + 1.30) - (0.20 + 0.95) = 0.53
credit_per_contract = 0.53 * 100 = $53

# Simulate forward through historical data
# Track daily, check exit conditions
# Result: Exited after 18 days at profit target
# P&L: +$140 per contract
# Exit type: profit_target
# Win: True
```

**Step 4: Test on Similar Days**
```python
# Find 45 historical days with similar conditions:
#   - IV Rank 40-60%
#   - ADX 15-20
#   - Trend = ranging
#   - RSI 55-65

# Run same combo on each day
# Results: 32 wins, 13 losses
# Win probability = 32/45 = 0.711 ≈ 0.72
# Avg profit when won = $140
# Avg loss when lost = $-180
# Max loss observed = $-220
```

**Step 5: Calculate Risk-Adjusted Score**
```python
expected_value = (140 * 0.72) + (-180 * 0.28) = 100.8 - 50.4 = 50.4
score = 50.4 / 220 = 0.229

# Apply bonuses/penalties
# Bonus: win_prob > 0.70 → score * 1.2
final_score = 0.229 * 1.2 = 0.275
```

**Step 6: Repeat for all 20 combos, select best**
```python
# After testing all 20:
# Combo 1 score: 0.275  ← BEST
# Combo 2 score: 0.118
# Combo 3 score: 0.198
# ... others lower

# Combo 1 selected as optimal
```

---

### Output: Label Row

**One row with labels:**
```csv
date,optimal_strategy,short_put,long_put,short_call,long_call,dte,risk_adjusted_score,expected_return,win_probability,max_loss
2024-03-01,IRON_CONDOR,195.0,190.0,225.0,230.0,35,0.275,0.0224,0.72,-220
```

---

### Final: Combined Training Row

**Features + Labels = One complete row:**
```csv
date,current_price,return_1d,...(77 more features),optimal_strategy,short_put,long_put,short_call,long_call,dte,risk_adjusted_score,expected_return,win_probability,max_loss
2024-03-01,205.89,0.0106,...,IRON_CONDOR,195.0,190.0,225.0,230.0,35,0.275,0.0224,0.72,-220
```

**This row is ready for ML training!**

The model will learn:
"When current_price=205.89, return_1d=0.0106, iv_rank=50, adx=17.8, trend_regime=ranging, ... (all 80 features look like this), the optimal action is: Iron Condor with strikes 195/190/225/230 and 35 DTE, which has expected return of 2.24% and 72% win probability."

---

## Summary

### Current Issues (Critical)

1. **❌ Mixing raw option-level data with aggregated features**
   - Ticker, volume, OHLCV of individual options present
   - Should only have day-level aggregates

2. **❌ Unclear row definition**
   - Each row seems to represent an individual option contract
   - Should represent one trading day

3. **❌ 100% win rate**
   - Indicates selection bias or insufficient testing
   - Should be 60-70% for realistic training

4. **❌ Missing ~40 features**
   - Have ~40, need 80 for robust predictions
   - Missing: detailed options metrics, support/resistance, regime classification, market context

### Required Changes

1. **✓ Separate raw data collection from feature engineering**
   - Keep option chains in separate storage
   - Use them for calculations and simulation
   - Don't include in training CSV

2. **✓ Create clean day-level aggregations**
   - 80 features describing each day's market conditions
   - All derived from raw data, but aggregated
   - One value per feature per day

3. **✓ Fix label creation process**
   - Test 15-20 parameter variations per strategy
   - Calculate realistic win probabilities via backtesting
   - Select best using risk-adjusted scoring
   - Accept that best may still only win 65% of time

4. **✓ Structure final dataset properly**
   - One row per day
   - 80 feature columns + 9 label columns
   - No raw option data
   - Clean, ready for ML training

### End Goal

**A training dataset where:**
- Each row represents ONE trading day
- Features describe that day's market conditions (aggregated from all available data)
- Labels prescribe the optimal strategy and parameters for those conditions
- Win probabilities are realistic (not perfect)
- Structure enables the model to learn: "When market conditions look like X, the best strategy is Y with parameters Z"

This structure allows the ML model to generalize to new days with similar conditions, which is the entire point of machine learning for trading.

---

**Document Version:** 1.0  
**Date:** December 2024  
**Purpose:** Correct training data structure for SMH options ML model
