# Feature Extraction Layer Documentation

**Date:** December 6, 2024  
**Status:** ✅ Production Ready  
**Purpose:** Convert raw market data into 84 model-ready features

---

## Overview

The **Feature Extraction Layer** is a critical component that sits between raw market data and the ML model. It transforms raw inputs (option chains, price history, market data) into the 84 aggregated features the model requires.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

Raw Inputs                Feature Extraction           Model Input
───────────               ──────────────────           ───────────

Option Chain    ─┐
(~150 contracts) │
                 │
Price History    ├──►  FeatureExtractor  ──►  84 Features  ──►  ML Model
(200+ days)      │     (scripts/utils/           Array              │
                 │      feature_extractor.py)                       │
SPY/VIX Data    ─┘                                                  ▼
(optional)                                                    Strategy
                                                              Prediction
```

---

## Why This Layer Exists

### Problem Without It
- Model expects exactly 84 features in specific order
- Raw data comes in various formats (option chains, OHLC, etc.)
- Feature calculation is complex (Greeks, indicators, regimes)
- Easy to make mistakes in feature ordering or calculation

### Solution With It
- ✅ Single source of truth for feature calculation
- ✅ Consistent feature extraction across training and prediction
- ✅ Handles missing data gracefully
- ✅ Validates inputs and outputs
- ✅ Modular and testable

---

## Module: `scripts/utils/feature_extractor.py`

### Class: `FeatureExtractor`

Main class for converting raw data to features.

#### Initialization

```python
from scripts.utils.feature_extractor import FeatureExtractor

extractor = FeatureExtractor()
```

Automatically loads feature names from `models/feature_names_clean.json`.

#### Main Method: `extract_features()`

```python
features = extractor.extract_features(
    option_chain=option_chain_df,      # Required
    price_history=price_history_df,    # Required
    current_date='2024-12-05',         # Required
    spy_history=spy_df,                # Optional
    vix_history=vix_df                 # Optional
)
```

**Returns:** Dictionary with 84 features

---

## Input Requirements

### 1. Option Chain (Required)

**Format:** pandas DataFrame

**Required Columns:**
- `strike` (float): Strike price
- `type` (str): 'call' or 'put'
- `expiration` (str): Expiration date
- `dte` (int): Days to expiration
- `bid` (float): Bid price
- `ask` (float): Ask price
- `volume` (int): Trading volume
- `open_interest` (int): Open interest
- `iv` (float): Implied volatility (0.0-1.0)
- `delta` (float): Delta Greek
- `gamma` (float): Gamma Greek
- `theta` (float): Theta Greek
- `vega` (float): Vega Greek

**Example:**
```python
option_chain = pd.DataFrame({
    'strike': [230, 235, 240, 245, 250],
    'type': ['call', 'call', 'call', 'call', 'call'],
    'expiration': ['2024-12-20'] * 5,
    'dte': [15, 15, 15, 15, 15],
    'bid': [8.50, 5.20, 2.80, 1.20, 0.45],
    'ask': [8.65, 5.35, 2.95, 1.30, 0.52],
    'volume': [850, 1200, 980, 650, 420],
    'open_interest': [8500, 12000, 9800, 6500, 4200],
    'iv': [0.24, 0.23, 0.22, 0.24, 0.26],
    'delta': [0.75, 0.58, 0.42, 0.28, 0.15],
    'gamma': [0.08, 0.14, 0.13, 0.11, 0.08],
    'theta': [-0.12, -0.19, -0.17, -0.13, -0.09],
    'vega': [0.15, 0.22, 0.21, 0.18, 0.14]
})
```

**Typical Size:** 100-150 contracts (various strikes and expirations)

---

### 2. Price History (Required)

**Format:** pandas DataFrame

**Required Columns:**
- `date` (str): Date in 'YYYY-MM-DD' format
- `open` (float): Opening price
- `high` (float): High price
- `low` (float): Low price
- `close` (float): Closing price
- `volume` (int): Trading volume

**Minimum Length:** 200 days (for sma_200 calculation)

**Example:**
```python
price_history = pd.DataFrame({
    'date': ['2024-06-01', '2024-06-02', '2024-06-03', ...],
    'open': [228.50, 229.50, 230.90, ...],
    'high': [230.20, 231.10, 232.50, ...],
    'low': [227.80, 229.00, 230.20, ...],
    'close': [229.45, 230.85, 231.20, ...],
    'volume': [42000000, 45000000, 48000000, ...]
})
```

---

### 3. SPY History (Optional)

**Format:** pandas DataFrame (same structure as price_history)

**Used For:**
- `spy_return_1d`
- `spy_return_5d`
- `spy_correlation`
- `smh_vs_spy`

**If Not Provided:** Uses default values (0.0 for returns, 0.80 for correlation)

---

### 4. VIX History (Optional)

**Format:** pandas DataFrame (same structure as price_history)

**Used For:**
- `vix_level`
- `vix_change`
- `vix_vs_ma20`

**If Not Provided:** Uses default values (16.0 for level, 0.0 for change, 1.0 for ratio)

---

## Output Format

### Dictionary with 84 Features

```python
{
    'current_price': 236.80,
    'return_1d': 0.0055,
    'return_3d': 0.0125,
    ...
    'days_since_regime_change': 8
}
```

### Feature Categories

| Category | Count | Examples |
|----------|-------|----------|
| Price Features | 22 | current_price, return_1d, sma_20, bb_position |
| Technical Indicators | 14 | rsi_14, macd, adx_14, stochastic_k |
| Volatility Features | 14 | hv_20d, iv_atm, iv_rank, parkinson_vol |
| Options Metrics | 15 | put_call_volume_ratio, atm_gamma, max_pain_strike |
| Support/Resistance | 10 | resistance_level, support_level, position_in_range |
| Market Context | 4 | spy_return_1d, vix_level, spy_correlation |
| Regime Classification | 5 | trend_regime, volatility_regime, combined_state |

---

## Helper Methods

### Convert to Array

```python
feature_array = extractor.get_feature_array(features)
# Returns: numpy array with 84 values in correct order
```

### Convert to DataFrame

```python
feature_df = extractor.get_feature_dataframe(features)
# Returns: pandas DataFrame with 1 row, 84 columns
```

---

## Validation

### Input Validation

The extractor automatically validates:
- ✅ All required columns present
- ✅ Sufficient historical data (warns if < 200 days)
- ✅ Date exists in price history
- ✅ No missing critical data

### Output Validation

The extractor ensures:
- ✅ Exactly 84 features present
- ✅ No NaN values
- ✅ All features in correct order
- ✅ Feature names match model expectations

---

## Usage Examples

### Example 1: Basic Usage

```python
from scripts.utils.feature_extractor import FeatureExtractor
import pandas as pd

# Load raw data
option_chain = pd.read_csv('option_chain.csv')
price_history = pd.read_csv('price_history.csv')

# Extract features
extractor = FeatureExtractor()
features = extractor.extract_features(
    option_chain=option_chain,
    price_history=price_history,
    current_date='2024-12-05'
)

print(f"Extracted {len(features)} features")
print(f"Current Price: ${features['current_price']:.2f}")
print(f"IV Rank: {features['iv_rank']:.1f}%")
```

### Example 2: With Optional Data

```python
# Include SPY and VIX for better accuracy
spy_history = pd.read_csv('spy_history.csv')
vix_history = pd.read_csv('vix_history.csv')

features = extractor.extract_features(
    option_chain=option_chain,
    price_history=price_history,
    current_date='2024-12-05',
    spy_history=spy_history,
    vix_history=vix_history
)
```

### Example 3: Feed to Model

```python
import pickle

# Extract features
features = extractor.extract_features(...)

# Load model
with open('models/lightgbm_clean_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Convert to DataFrame
feature_df = extractor.get_feature_dataframe(features)

# Predict
prediction = model.predict(feature_df)[0]
probabilities = model.predict_proba(feature_df)[0]

print(f"Predicted Strategy: {prediction}")
print(f"Confidence: {probabilities[prediction]:.1%}")
```

---

## Production Script

### `scripts/7_predict_with_raw_data.py`

Complete production workflow that:
1. Loads raw market data
2. Extracts 84 features
3. Predicts strategy using ML model
4. Outputs prediction with confidence

**Usage:**
```bash
# Predict for specific date
python scripts/7_predict_with_raw_data.py --date 2024-12-05

# Use latest available data
python scripts/7_predict_with_raw_data.py --live

# Save prediction to file
python scripts/7_predict_with_raw_data.py --live --save prediction.json
```

**Output:**
```json
{
  "prediction_date": "2024-12-05",
  "prediction_time": "2024-12-06T10:30:00",
  "model_version": "v1.0",
  "strategy": {
    "type": "BULL_CALL_SPREAD",
    "confidence": 0.807
  },
  "market_conditions": {
    "current_price": 236.80,
    "iv_rank": 21.88,
    "adx": 22.45,
    "rsi": 58.35,
    "trend_regime": 3,
    "volatility_regime": 1
  },
  "top_3_strategies": [
    {"strategy": "BULL_CALL_SPREAD", "confidence": 0.807},
    {"strategy": "LONG_CALL", "confidence": 0.112},
    {"strategy": "CALENDAR_SPREAD", "confidence": 0.045}
  ]
}
```

---

## Feature Calculation Details

### Price Features (22)

**Returns:** Calculated as percentage change
```python
return_1d = (price_today - price_yesterday) / price_yesterday
```

**SMAs:** Simple moving averages
```python
sma_20 = mean(last_20_closes)
```

**Bollinger Bands:** 2 standard deviations
```python
bb_upper = sma_20 + (2 × std_20)
bb_lower = sma_20 - (2 × std_20)
bb_position = (price - bb_lower) / (bb_upper - bb_lower)
```

### Technical Indicators (14)

**RSI:** 14-period Relative Strength Index
```python
avg_gain = mean(positive_changes)
avg_loss = mean(negative_changes)
rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

**MACD:** Moving Average Convergence Divergence
```python
macd = ema_12 - ema_26
macd_signal = ema_9(macd)
macd_histogram = macd - macd_signal
```

**ADX:** Average Directional Index (trend strength)

**Stochastic:** %K and %D oscillators

**CCI:** Commodity Channel Index

**Williams %R:** Momentum indicator

**MFI:** Money Flow Index (volume-weighted RSI)

### Volatility Features (14)

**Historical Volatility:** Annualized standard deviation of returns
```python
hv_20d = std(returns_20d) × sqrt(252)
```

**IV Rank:** Percentile of current IV in 52-week range
```python
iv_rank = (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) × 100
```

**IV Skew:** Put IV premium over Call IV
```python
iv_skew = mean(otm_put_ivs) - mean(otm_call_ivs)
```

**Parkinson/Garman-Klass:** High-low and OHLC volatility estimators

### Options Metrics (15)

**Put/Call Ratios:** Volume and open interest ratios

**ATM Greeks:** Averaged from options near current price

**Max Pain:** Strike where most options expire worthless

**Gamma/Delta Exposure:** Aggregate market maker positions

### Support/Resistance (10)

**Levels:** Recent highs and lows from 60-day lookback

**Position in Range:** Where price sits between support/resistance

**Breakout Probability:** Heuristic based on distance and volatility

### Regime Classification (5)

**Trend Regime:** 0-4 scale based on ADX, MACD, price vs SMAs

**Volatility Regime:** 0-4 scale based on IV Rank

**Volume Regime:** 0-2 scale based on volume vs average

**Combined State:** Encoded combination of all regimes

---

## Error Handling

### Missing Data

```python
try:
    features = extractor.extract_features(...)
except ValueError as e:
    print(f"Error: {e}")
    # Handle missing data
```

### Insufficient History

```python
# Warns but continues if < 200 days
# Uses available data for calculations
```

### Invalid Dates

```python
# Raises ValueError if date not in price_history
```

---

## Testing

### Unit Tests

```python
# Test feature extraction
def test_feature_extraction():
    extractor = FeatureExtractor()
    features = extractor.extract_features(
        option_chain=test_chain,
        price_history=test_history,
        current_date='2024-12-05'
    )
    
    assert len(features) == 84
    assert 'current_price' in features
    assert not any(pd.isna(v) for v in features.values())
```

### Integration Tests

```python
# Test end-to-end workflow
def test_prediction_workflow():
    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract_features(...)
    
    # Load model
    model = load_model()
    
    # Predict
    feature_df = extractor.get_feature_dataframe(features)
    prediction = model.predict(feature_df)[0]
    
    assert prediction in range(10)  # Valid strategy index
```

---

## Performance

### Extraction Time

- **Typical:** 50-100ms for 84 features
- **With 200 days history:** ~100ms
- **With 500 days history:** ~150ms

### Memory Usage

- **Feature dict:** ~10 KB
- **Option chain (150 contracts):** ~50 KB
- **Price history (200 days):** ~20 KB

---

## Maintenance

### Adding New Features

1. Add feature name to `feature_names_clean.json`
2. Implement calculation in appropriate `_extract_*` method
3. Update feature count (84 → 85)
4. Retrain model with new feature
5. Update documentation

### Modifying Calculations

1. Update calculation in `feature_extractor.py`
2. Regenerate training data with new calculation
3. Retrain model
4. Test on validation set
5. Deploy if performance improves

---

## Summary

The Feature Extraction Layer provides:

✅ **Consistent** feature calculation across training and prediction  
✅ **Validated** inputs and outputs  
✅ **Modular** design for easy testing and maintenance  
✅ **Production-ready** with error handling and logging  
✅ **Documented** with clear examples and usage patterns  

**Key Files:**
- `scripts/utils/feature_extractor.py` - Main extraction module
- `scripts/7_predict_with_raw_data.py` - Production prediction script
- `models/feature_names_clean.json` - Feature name reference

**Next Steps:**
- Integrate with live data feeds
- Add real-time feature caching
- Implement feature monitoring
- Set up alerting for anomalies

---

**Status:** ✅ Production Ready  
**Last Updated:** December 6, 2024  
**Version:** 1.0
