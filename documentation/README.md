# SMH Options ML Training Data Pipeline

## Overview

This project creates machine learning training data for options trading strategies on SMH (VanEck Semiconductor ETF).

The pipeline converts raw option chain data into clean, day-level features with optimal strategy labels.

## Project Structure

```
option-iwm/
├── data/
│   ├── raw/                          # Raw option chains
│   │   └── smh_complete_dataset.csv  # 60,553 options across 248 days
│   │
│   └── processed/                    # Processed datasets
│       ├── smh_daily_features.csv    # 248 rows, 80 features per day
│       └── smh_training_data.csv     # 248 rows, features + labels
│
├── scripts/
│   ├── 1_collect_data.py            # Data collection from Massive.com
│   ├── 2_engineer_features.py       # Feature engineering (raw → features)
│   ├── 3_create_labels.py           # Label creation (features → labels)
│   └── utils/
│       ├── calculate_greeks.py      # Greeks calculation
│       └── feature_engineering.py   # Feature utilities
│
└── documentation/
    ├── README.md                     # This file
    ├── DATA_STRUCTURE.md             # Detailed data structure guide
    ├── DATASET_SUMMARY.md            # Dataset statistics
    └── CRITICAL_FINDINGS.md          # Important findings
```

## Pipeline Stages

### Stage 1: Data Collection
**Script:** `scripts/1_collect_data.py`  
**Input:** Massive.com API  
**Output:** `data/raw/smh_complete_dataset.csv`

Collects complete option chains for SMH:
- 248 trading days (Dec 2023 - Dec 2024)
- 60,553 option contracts
- Filters: ±30% strikes, 7-90 DTE, volume > 5
- Includes: OHLCV, Greeks, IV, volume, open interest

### Stage 2: Feature Engineering
**Script:** `scripts/2_engineer_features.py`  
**Input:** `data/raw/smh_complete_dataset.csv` (60,553 rows)  
**Output:** `data/processed/smh_daily_features.csv` (248 rows)

Aggregates raw option data into 80 day-level features:

**Price Features (20):**
- Returns (1d, 3d, 5d, 10d, 20d, 50d)
- SMAs (5, 10, 20, 50, 200)
- Price vs SMAs
- Bollinger Bands
- SMA alignment

**Technical Indicators (15):**
- RSI, MACD, ADX, ATR
- Volume metrics
- Stochastic, CCI, Williams %R, MFI

**Volatility Features (15):**
- Historical volatility (HV)
- Implied volatility (IV) metrics
- IV Rank, IV Percentile
- HV/IV ratio, IV skew
- VIX levels and changes

**Options Metrics (15):**
- Put/Call ratios (volume & OI)
- ATM Greeks (averaged)
- Max pain strike
- Total volume & OI
- Options flow sentiment

**Support/Resistance (10):**
- Resistance/support levels
- Distances to levels
- Position in range
- Breakout probability

**Market Context (10):**
- SPY correlation
- Relative strength
- Market breadth
- Treasury yields
- Risk-on/risk-off

**Regime Classification (5):**
- Trend regime (0-4)
- Volatility regime (0-4)
- Volume regime (0-2)
- Combined state
- Days since regime change

### Stage 3: Label Creation
**Script:** `scripts/3_create_labels.py`  
**Input:** `data/processed/smh_daily_features.csv` + raw data  
**Output:** `data/processed/smh_training_data.csv`

Creates optimal strategy labels for each day:

**Process:**
1. **Rules Engine:** Select strategy based on features
   - High IV + Ranging → Iron Condor
   - Low IV + Trending → Long Call/Put
   - Medium IV + Moderate trend → Spreads

2. **Parameter Generation:** Create 15-20 variations
   - Different strikes, DTEs, wing widths
   - Test multiple configurations

3. **Backtesting:** Test on similar historical days
   - Find 30+ similar days
   - Simulate each parameter set
   - Calculate win probability (realistic 55-75%)

4. **Selection:** Choose best via risk-adjusted scoring
   - Score = Expected Value / Max Loss
   - Bonuses for high win rate
   - Select highest scoring combination

**Labels Added:**
- strategy (IRON_CONDOR, LONG_CALL, etc.)
- Strategy-specific parameters (strikes, DTE)
- risk_adjusted_score
- win_probability (realistic, not 100%)
- expected_return
- max_loss
- avg_days_held

## Data Structure

### Raw Data (Stage 1 Output)
**File:** `data/raw/smh_complete_dataset.csv`  
**Structure:** One row per option contract

```
60,553 rows × 79 columns
- Individual option contracts
- Used for calculations and simulation
- NOT directly in training data
```

### Daily Features (Stage 2 Output)
**File:** `data/processed/smh_daily_features.csv`  
**Structure:** One row per trading day

```
248 rows × 81 columns (1 date + 80 features)
- Aggregated market conditions
- No individual option data
- Clean day-level features
```

### Training Data (Stage 3 Output)
**File:** `data/processed/smh_training_data.csv`  
**Structure:** One row per trading day with labels

```
248 rows × ~90 columns (80 features + ~10 labels)
- Complete training dataset
- Features describe market conditions
- Labels prescribe optimal strategy
- Ready for ML model
```

## Usage

### Run Complete Pipeline

```bash
# Stage 1: Collect data (if needed)
python scripts/1_collect_data.py

# Stage 2: Engineer features
python scripts/2_engineer_features.py

# Stage 3: Create labels
python scripts/3_create_labels.py
```

### Load Training Data

```python
import pandas as pd

# Load training data
df = pd.read_csv('data/processed/smh_training_data.csv')

# Features (80 columns)
feature_cols = [col for col in df.columns if col not in [
    'date', 'strategy', 'risk_adjusted_score', 'win_probability',
    'expected_return', 'max_loss', 'avg_days_held',
    'short_put', 'long_put', 'short_call', 'long_call',
    'long_strike', 'short_strike', 'strike', 'dte'
]]

X = df[feature_cols]
y_strategy = df['strategy']
y_params = df[['short_put', 'long_put', 'short_call', 'long_call', 'dte']]
```

## Key Principles

### 1. Clean Separation
- **Raw data:** Individual options (for calculations)
- **Features:** Aggregated day-level (for training)
- **Labels:** Optimal strategies (for prediction)

### 2. No Look-Ahead Bias
- Features use only past data
- Simulation uses real historical prices
- One row per day prevents data leakage

### 3. Realistic Labels
- Win probabilities: 55-75% (not 100%)
- Tested on multiple similar days
- Risk-adjusted selection

### 4. Generalizable
- Features describe market conditions
- Not tied to specific option contracts
- Model can predict on new days

## Dataset Statistics

**Coverage:**
- Date range: Dec 8, 2023 → Dec 3, 2024
- Trading days: 248
- Data completeness: 98.8% (245/248 days)

**Raw Data:**
- Total contracts: 60,553
- Average per day: 244 contracts
- Strikes: ±30% from current price
- DTE range: 7-90 days

**Features:**
- Total features: 80
- All numeric (floats/integers)
- No missing values
- Normalized ranges

**Labels:**
- Strategies: 6 types
- Win probability: 55-75% typical
- Expected return: 1-5% of portfolio
- Risk-adjusted scores: 0.05-0.50

## Documentation

- **DATA_STRUCTURE.md:** Detailed explanation of correct data structure
- **DATASET_SUMMARY.md:** Complete dataset statistics
- **CRITICAL_FINDINGS.md:** Important discoveries during development

## Requirements

```
pandas
numpy
scipy (for Greeks calculation)
```

## Notes

- This pipeline creates training data, not a trading system
- Labels represent optimal strategies based on backtesting
- Real trading requires additional risk management
- Past performance doesn't guarantee future results

## Version

**Pipeline Version:** 2.0  
**Last Updated:** December 2024  
**Dataset Version:** SMH Complete (Dec 2023 - Dec 2024)
