# Model Input/Output Standards
## Production Requirements for SMH Options ML Model

**Version:** 1.0  
**Date:** December 5, 2025  
**Status:** Active Guidelines  
**Purpose:** Define strict standards for model input/output structure

---

## Core Principle

**RULE: The model takes 80 aggregated features as input, NOT raw option chains**

### Why This Matters

- ✅ Consistent input format across training and prediction
- ✅ Model learns from market conditions, not individual options
- ✅ Scalable and efficient (80 numbers vs thousands of options)
- ✅ Reproducible feature calculation
- ✅ Clear separation: Features → Model → Strategy → Execution

---

## Input Requirements

### Mandatory: 80 Features (100% Coverage)

**RULE: ALL 80 features must be present for every prediction**

| Category | Count | Status | Required |
|----------|-------|--------|----------|
| Price Features | 22 | ⚠️ Need 22 | ✅ YES |
| Technical Indicators | 14 | ⚠️ Need 6 | ✅ YES |
| Volatility Features | 14 | ⚠️ Need 7 | ✅ YES |
| Options Metrics | 15 | ⚠️ Need 5 | ✅ YES |
| Support/Resistance | 10 | ⚠️ Need 5 | ✅ YES |
| Market Context | 10 | ⚠️ Need 7 | ✅ YES |
| Regime Classification | 5 | ⚠️ Need 2 | ✅ YES |
| **TOTAL** | **80** | **Current: 58** | **Target: 80** |

### Input Format Standards

**RULE: Input must be ONE row with 80 numeric values in exact order**

#### Format Option 1: CSV (Preferred for Batch)

```csv
current_price,return_1d,return_3d,...,days_since_regime_change
236.80,0.0055,0.0125,...,8
```

**Requirements:**
- Header row with exact feature names
- One data row per prediction
- All values numeric (no strings except header)
- No missing values (NaN not allowed)
- Decimal precision: 4 places minimum

#### Format Option 2: JSON (Preferred for API)

```json
{
  "date": "2024-12-05",
  "features": {
    "current_price": 236.80,
    "return_1d": 0.0055,
    ...
    "days_since_regime_change": 8
  }
}
```

**Requirements:**
- All 80 features in "features" object
- Feature names must match training exactly
- All values numeric
- Optional metadata (date, timestamp) allowed

#### Format Option 3: Array (Preferred for Direct Model)

```python
[236.80, 0.0055, 0.0125, ..., 8]  # Exactly 80 values
```

**Requirements:**
- Exactly 80 numeric values
- Order must match training data columns
- No labels, no metadata
- Pure numeric array

---

## Feature Calculation Standards

### Category 1: Price Features (22 Required)

**Data Source:** SMH price history (minimum 200 days)

**Required Features:**
```python
# Current price
current_price = latest_close

# Returns (6 features)
return_1d = (price_today - price_yesterday) / price_yesterday
return_3d = (price_today - price_3d_ago) / price_3d_ago
return_5d = (price_today - price_5d_ago) / price_5d_ago
return_10d = (price_today - price_10d_ago) / price_10d_ago
return_20d = (price_today - price_20d_ago) / price_20d_ago
return_50d = (price_today - price_50d_ago) / price_50d_ago

# Moving averages (5 features)
sma_5 = mean(last_5_closes)
sma_10 = mean(last_10_closes)
sma_20 = mean(last_20_closes)
sma_50 = mean(last_50_closes)
sma_200 = mean(last_200_closes)

# Relative prices (5 features)
price_vs_sma_5 = (current_price - sma_5) / sma_5
price_vs_sma_10 = (current_price - sma_10) / sma_10
price_vs_sma_20 = (current_price - sma_20) / sma_20
price_vs_sma_50 = (current_price - sma_50) / sma_50
price_vs_sma_200 = (current_price - sma_200) / sma_200

# SMA alignment (1 feature)
sma_alignment = 1 if (sma_5 > sma_10 > sma_20 > sma_50 > sma_200) else 0

# Bollinger Bands (4 features)
bb_middle = sma_20
bb_std = std(last_20_closes)
bb_upper = bb_middle + (2 * bb_std)
bb_lower = bb_middle - (2 * bb_std)
bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
```

**Validation Rules:**
- Returns: -0.10 to +0.10 (±10% max)
- SMAs: Must be > 0 and ordered (5 < 10 < 20 < 50 < 200 for uptrend)
- Relative prices: -0.20 to +0.20 (±20% max)
- BB position: 0 to 1 (within bands)

---

### Category 2: Technical Indicators (14 Required)

**Data Source:** SMH price/volume history

**Required Features:**
```python
# RSI (1 feature)
rsi_14 = calculate_rsi(closes, period=14)  # 0-100

# MACD (3 features)
macd, macd_signal, macd_histogram = calculate_macd(closes)

# ADX (1 feature)
adx_14 = calculate_adx(high, low, close, period=14)  # 0-100

# ATR (1 feature)
atr_14 = calculate_atr(high, low, close, period=14)  # > 0

# Volume (2 features)
volume_20d_avg = mean(last_20_volumes)
volume_vs_avg = current_volume / volume_20d_avg

# Additional indicators (6 features)
obv = calculate_obv(close, volume)
stochastic_k, stochastic_d = calculate_stochastic(high, low, close, period=14)
cci = calculate_cci(high, low, close, period=20)
williams_r = calculate_williams_r(high, low, close, period=14)
mfi = calculate_mfi(high, low, close, volume, period=14)
```

**Validation Rules:**
- RSI: 0 to 100
- ADX: 0 to 100
- ATR: > 0
- Stochastic: 0 to 100
- CCI: -200 to +200
- Williams %R: -100 to 0
- MFI: 0 to 100
- Volume ratio: > 0

---

### Category 3: Volatility Features (14 Required)

**Data Source:** Option chain + price history

**Required Features:**
```python
# Historical volatility (1 feature)
hv_20d = calculate_historical_volatility(returns, period=20)

# Implied volatility (2 features)
iv_atm = mean([iv for option in atm_options])
iv_rank = (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) * 100
iv_percentile = percentile_rank(current_iv, last_252_ivs)

# HV/IV ratio (1 feature)
hv_iv_ratio = hv_20d / iv_atm

# IV skew (1 feature)
iv_skew = mean(otm_put_ivs) - mean(otm_call_ivs)

# IV term structure (1 feature)
iv_term_structure = mean(near_term_ivs) - mean(far_term_ivs)

# VIX metrics (3 features)
vix_level = current_vix
vix_change = current_vix - yesterday_vix
vix_vs_ma20 = current_vix / vix_ma20

# Volatility trend (1 feature)
volatility_trend = 1 if (iv_increasing) else 0

# Advanced volatility (3 features)
parkinson_vol = calculate_parkinson(high, low)
garman_klass_vol = calculate_garman_klass(open, high, low, close)
vol_of_vol = std(last_20_ivs)
```

**Validation Rules:**
- HV: 0.10 to 1.00
- IV: 0.10 to 1.00
- IV Rank: 0 to 100
- IV Percentile: 0 to 100
- HV/IV Ratio: 0.50 to 2.00
- IV Skew: -0.10 to +0.10
- VIX: 10 to 50
- Vol of Vol: 0.01 to 0.50

---

### Category 4: Options Metrics (15 Required)

**Data Source:** Option chain

**Required Features:**
```python
# Put/Call ratios (2 features)
put_call_volume_ratio = sum(put_volumes) / sum(call_volumes)
put_call_oi_ratio = sum(put_ois) / sum(call_ois)

# Total metrics (2 features)
total_option_volume = sum(all_volumes)
total_open_interest = sum(all_ois)

# ATM Greeks (5 features)
atm_options = [opt for opt in chain if abs(opt.strike - current_price) < 5]
atm_delta_call = mean([opt.delta for opt in atm_options if opt.type == 'call'])
atm_delta_put = mean([opt.delta for opt in atm_options if opt.type == 'put'])
atm_gamma = mean([opt.gamma for opt in atm_options])
atm_theta = mean([opt.theta for opt in atm_options])
atm_vega = mean([opt.vega for opt in atm_options])

# Max pain (2 features)
max_pain_strike = calculate_max_pain(chain)
distance_to_max_pain = (current_price - max_pain_strike) / current_price

# Exposure metrics (2 features)
gamma_exposure = sum([opt.gamma * opt.oi * 100 for opt in chain])
delta_exposure = sum([opt.delta * opt.oi * 100 for opt in chain])

# Activity flags (2 features)
unusual_activity = 1 if (current_volume > 2 * avg_volume) else 0
options_flow_sentiment = (call_volume - put_volume) / total_volume
```

**Validation Rules:**
- Put/Call ratios: 0.30 to 3.00
- Total volume: > 0
- Total OI: > 0
- ATM delta call: 0.40 to 0.60
- ATM delta put: -0.60 to -0.40
- Max pain: Near current price (±10%)
- Flow sentiment: -1 to +1

---

### Category 5: Support/Resistance (10 Required)

**Data Source:** Price history (30-60 days)

**Required Features:**
```python
# Resistance levels (2 features)
resistance_1 = find_recent_high(last_30_days)
resistance_2 = find_second_high(last_30_days)

# Support levels (2 features)
support_1 = find_recent_low(last_30_days)
support_2 = find_second_low(last_30_days)

# Distance calculations (2 features)
distance_to_resistance_1 = (resistance_1 - current_price) / current_price
distance_to_support_1 = (current_price - support_1) / current_price

# Range metrics (4 features)
position_in_range = (current_price - support_1) / (resistance_1 - support_1)
range_width = (resistance_1 - support_1) / current_price
days_in_range = count_days_since_breakout()
breakout_probability = estimate_breakout_probability()
```

**Validation Rules:**
- Resistance > current price
- Support < current price
- Resistance_1 < Resistance_2
- Support_1 > Support_2
- Position in range: 0 to 1
- Range width: 0.05 to 0.30

---

### Category 6: Market Context (10 Required)

**Data Source:** SPY, VIX, Treasury data

**Required Features:**
```python
# SPY correlation (1 feature)
spy_correlation = calculate_correlation(smh_returns, spy_returns, period=30)

# SPY returns (2 features)
spy_return_1d = (spy_today - spy_yesterday) / spy_yesterday
spy_return_5d = (spy_today - spy_5d_ago) / spy_5d_ago

# Relative performance (1 feature)
smh_vs_spy = smh_return_5d - spy_return_5d

# Market metrics (6 features)
sector_rotation = calculate_sector_rotation()  # Optional
market_breadth = nyse_advances / (nyse_advances + nyse_declines)  # Optional
treasury_yield = get_10y_yield()  # Optional
yield_curve_slope = treasury_10y - treasury_2y  # Optional
risk_on_off = calculate_risk_sentiment()  # Optional
```

**Validation Rules:**
- Correlation: -1 to +1
- Returns: -0.10 to +0.10
- Relative performance: -0.10 to +0.10
- Market breadth: 0 to 1
- Treasury yield: 2.0 to 6.0
- Yield curve: -2.0 to +3.0
- Risk sentiment: -1 to +1

**Note:** Last 5 features are optional if data unavailable. Can use defaults:
- sector_rotation = 0.5
- market_breadth = 0.5
- treasury_yield = 4.0
- yield_curve_slope = 0.5
- risk_on_off = 0.5

---

### Category 7: Regime Classification (5 Required)

**Data Source:** Calculated from other features

**Required Features:**
```python
# Trend regime (1 feature)
if adx > 30 and macd_histogram > 0 and price > sma_50:
    trend_regime = 4  # strong_up
elif adx > 25 and price > sma_20:
    trend_regime = 3  # weak_up
elif adx < 20:
    trend_regime = 2  # ranging
elif adx > 25 and price < sma_20:
    trend_regime = 1  # weak_down
else:
    trend_regime = 0  # strong_down

# Volatility regime (1 feature)
if iv_rank > 75:
    volatility_regime = 4  # very_high
elif iv_rank > 60:
    volatility_regime = 3  # elevated
elif iv_rank > 40:
    volatility_regime = 2  # normal
elif iv_rank > 25:
    volatility_regime = 1  # low
else:
    volatility_regime = 0  # very_low

# Volume regime (1 feature)
if volume_vs_avg > 1.5:
    volume_regime = 2  # high
elif volume_vs_avg > 0.8:
    volume_regime = 1  # normal
else:
    volume_regime = 0  # low

# Combined state (1 feature)
combined_state = (trend_regime * 15) + (volatility_regime * 3) + volume_regime
# Range: 0-74

# Regime stability (1 feature)
days_since_regime_change = count_days_in_current_regime()
```

**Validation Rules:**
- Trend regime: 0 to 4 (integer)
- Volatility regime: 0 to 4 (integer)
- Volume regime: 0 to 2 (integer)
- Combined state: 0 to 74 (integer)
- Days since change: 0 to 60

---

## Output Requirements

### Mandatory Output Structure

**RULE: Model must output strategy + parameters + metrics**

#### Output Format: JSON (Preferred)

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
  }
}
```

### Required Output Fields

**Strategy Section:**
- `type`: One of 10 strategy names (string)
- `confidence`: 0.0 to 1.0 (float)

**Parameters Section:**
- Strategy-specific parameters (strikes, DTE, etc.)
- All numeric values
- Must be executable (valid strikes, realistic DTE)

**Performance Section:**
- `expected_return`: Expected % return (float)
- `win_probability`: 0.0 to 1.0 (float)
- `max_profit`: Maximum profit in $ (float)
- `max_loss`: Maximum loss in $ (float, negative)
- `risk_reward_ratio`: Profit/Loss ratio (float)
- `avg_days_to_exit`: Expected holding period (float)

---

## Validation Standards

### Input Validation Checklist

**Before feeding to model:**

- [ ] Exactly 80 features present
- [ ] No missing values (NaN)
- [ ] All values numeric
- [ ] All features in correct order
- [ ] Feature names match training (if using dict/JSON)
- [ ] All values within valid ranges
- [ ] No extreme outliers
- [ ] Data types correct (float for continuous, int for categorical)

### Output Validation Checklist

**After receiving prediction:**

- [ ] Strategy type is one of 10 valid strategies
- [ ] Confidence between 0 and 1
- [ ] Parameters are realistic (strikes near current price, DTE 7-90)
- [ ] Win probability between 0 and 1
- [ ] Expected return is reasonable (-0.50 to +0.50)
- [ ] Max profit/loss are realistic
- [ ] Risk/reward ratio > 0

---

## Production Workflow Standards

### Daily Prediction Process

**Timeline: Every trading day at 9:05 AM ET**

```
9:00 AM - Market Opens
9:05 AM - Start Process
  ↓
Step 1: Collect Raw Data (5 min)
  - SMH price history (50 days)
  - Option chain (current)
  - SPY/VIX data
  - Treasury yields (optional)
  ↓
Step 2: Calculate 80 Features (2 min)
  - Run feature engineering script
  - Validate all features
  - Check for errors
  ↓
Step 3: Format Model Input (1 min)
  - Create CSV/JSON/Array
  - Verify 80 values
  - Save input file
  ↓
Step 4: Get Model Prediction (Instant)
  - Feed input to model
  - Receive output
  - Validate output
  ↓
Step 5: Execute Trade (5-10 min)
  - Find matching options
  - Calculate entry prices
  - Place orders
  - Confirm fills
  ↓
9:15 AM - Position Opened
```

### Error Handling

**RULE: Never proceed with incomplete or invalid data**

**If feature calculation fails:**
1. Log error with details
2. Do NOT use default values
3. Do NOT proceed to prediction
4. Alert operator
5. Skip trading for the day

**If model output is invalid:**
1. Log prediction details
2. Do NOT execute trade
3. Alert operator
4. Review model health

---

## Data Quality Standards

### Minimum Data Requirements

**For Training:**
- Minimum 200 trading days of data
- All 80 features for every day
- No more than 5% missing values per feature
- Realistic value ranges

**For Prediction:**
- Minimum 200 days of price history (for sma_200)
- Current day's option chain
- Last 30 days of SPY/VIX data
- All 80 features calculable

### Feature Consistency

**RULE: Training and prediction features must be calculated identically**

**Ensure:**
- Same calculation methods
- Same lookback periods
- Same data sources
- Same rounding/precision
- Same handling of edge cases

---

## Documentation Requirements

### Feature Calculation Documentation

**For each feature, document:**
- Calculation formula
- Data sources required
- Lookback period
- Valid range
- Edge case handling
- Example calculation

### Model Input/Output Examples

**Maintain examples for:**
- Each of 10 strategies
- Various market conditions
- Edge cases
- Error scenarios

---

## Monitoring and Maintenance

### Daily Monitoring

**Track:**
- Feature calculation success rate
- Feature value distributions
- Model prediction confidence
- Strategy distribution
- Execution success rate

### Weekly Review

**Analyze:**
- Feature drift (values changing over time)
- Model performance vs expectations
- Strategy selection patterns
- Win rate by strategy

### Monthly Audit

**Verify:**
- All 80 features still calculating correctly
- Feature ranges still valid
- Model output still reasonable
- Documentation up to date

---

## Version Control

### Feature Schema Versioning

**When adding/modifying features:**
1. Increment schema version
2. Document changes
3. Retrain model with new schema
4. Update all documentation
5. Update validation rules

### Model Version Tracking

**Track:**
- Model version
- Training date
- Feature schema version
- Performance metrics
- Known issues

---

## Summary

### Input Requirements
- ✅ Exactly 80 numeric features
- ✅ Calculated from raw market data
- ✅ All features in correct order
- ✅ No missing values
- ✅ All values within valid ranges

### Output Requirements
- ✅ Strategy type (one of 10)
- ✅ Parameters (strikes, DTE)
- ✅ Performance metrics
- ✅ Confidence score
- ✅ All values validated

### Critical Rules
1. **Never** feed raw option chains to model
2. **Always** calculate all 80 features
3. **Never** use default values for missing features
4. **Always** validate input before prediction
5. **Always** validate output before execution
6. **Never** proceed with incomplete data

---

**Status:** Active Guidelines  
**Compliance:** Mandatory for production use  
**Next Review:** After Phase 4 completion
