# Data Quality Standards & Implementation Rules
## SMH Options ML Model - Production-Ready Dataset

**Version:** 1.0  
**Date:** December 5, 2024  
**Status:** Active Guidelines  
**Quality Target:** 9/10 minimum

---

## Core Principles

### 1. NO SHORTCUTS
- ✅ Use real data only (no defaults, no placeholders)
- ✅ Calculate all features properly (no skipping)
- ✅ Test all 10 strategies (no limiting to 4)
- ✅ Sufficient historical data (minimum requirements met)
- ✅ **ALWAYS recalculate IV Rank** - API data is broken (stuck at 50.0)
- ❌ No "good enough" - aim for production quality

### 2. DATA INTEGRITY
- ✅ One row per trading day (no duplicates)
- ✅ No individual option contract data in training file
- ✅ All features are aggregated metrics
- ✅ No look-ahead bias (only use past data)
- ✅ Temporal consistency (earlier dates = earlier data only)

### 3. COMPLETENESS
- ✅ 80/80 features (100% coverage)
- ✅ 10/10 strategies represented
- ✅ Realistic win probabilities (55-75% range)
- ✅ Diverse market conditions captured
- ✅ Sufficient training examples per strategy (minimum 20 days each)

### 4. IV RANK CALCULATION (CRITICAL)
**RULE: ALWAYS recalculate IV Rank - API data is broken**

**Problem:** Massive.com API provides iv_rank stuck at 50.0 for 99% of days
- Min: 15.4, Max: 50.0 (should be 0-100)
- Std Dev: 2.3 (should be 20-30)
- Only 4 unique values (should be hundreds)

**Solution:** Calculate proper IV Rank using 252-day rolling window
```python
iv_rank = (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) × 100
```

**Expected Results:**
- Range: 0-100 ✅
- Std Dev: 20-30 ✅
- Days > 50: 150+ ✅
- Days > 70: 70+ ✅
- Days < 30: 50+ ✅

**Implementation:** Integrated into `scripts/2_engineer_features.py`

**Validation:** Check iv_rank distribution after feature engineering

---

## Feature Requirements (80 Total)

### Category 1: Price Features (22 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| current_price | Current SMH close | > 0 |
| return_1d through return_50d | 6 return periods | -0.10 to +0.10 |
| sma_5 through sma_200 | 5 SMAs | > 0, ordered |
| price_vs_sma_* | 5 relative prices | -0.20 to +0.20 |
| sma_alignment | Boolean | 0 or 1 |
| bb_upper, bb_middle, bb_lower | Bollinger Bands | upper > middle > lower |
| bb_position | Position in bands | 0 to 1 |

**Data Requirements:**
- Minimum 200 days of price history for sma_200
- If insufficient history: Start data collection earlier OR exclude sma_200 (document decision)

**Validation Rules:**
```python
assert df['sma_5'].notna().all(), "sma_5 has missing values"
assert df['sma_200'].notna().sum() > 0.8 * len(df), "sma_200 >20% missing"
assert (df['bb_upper'] > df['bb_lower']).all(), "Bollinger Bands invalid"
```

---

### Category 2: Technical Indicators (14 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| rsi_14 | 14-period RSI | 0 to 100 |
| macd, macd_signal, macd_histogram | MACD components | Real values |
| adx_14 | 14-period ADX | 0 to 100 |
| atr_14 | 14-period ATR | > 0 |
| obv | On-Balance Volume | Real values |
| stochastic_k, stochastic_d | Stochastic oscillator | 0 to 100 |
| cci | Commodity Channel Index | -200 to +200 |
| williams_r | Williams %R | -100 to 0 |
| mfi | Money Flow Index | 0 to 100 |
| volume_20d_avg, volume_vs_avg | Volume metrics | > 0 |

**Currently Missing:** obv, stochastic_k, stochastic_d, cci, williams_r, mfi

**Implementation:**
- Calculate from SMH price/volume history
- Use standard formulas (no shortcuts)
- Validate ranges after calculation

---

### Category 3: Volatility Features (14 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| hv_20d | Historical volatility | 0.10 to 1.00 |
| iv_atm | ATM implied volatility | 0.10 to 1.00 |
| iv_rank, iv_percentile | IV metrics | 0 to 100 |
| hv_iv_ratio | HV/IV ratio | 0.50 to 2.00 |
| iv_skew | Put IV - Call IV | -0.10 to +0.10 |
| iv_term_structure | Near vs far IV | -0.10 to +0.10 |
| vix_level | VIX close | 10 to 50 |
| vix_change | Daily VIX change | -5 to +5 |
| vix_vs_ma20 | VIX vs 20-day MA | -0.30 to +0.30 |
| volatility_trend | Vol increasing? | 0 or 1 |
| parkinson_vol | High-low volatility | 0.10 to 1.00 |
| garman_klass_vol | OHLC volatility | 0.10 to 1.00 |
| vol_of_vol | Volatility of volatility | 0.01 to 0.50 |

**Currently Missing:** iv_skew, iv_term_structure, vix_vs_ma20, volatility_trend, parkinson_vol, garman_klass_vol, vol_of_vol

**Implementation:**
- iv_skew: Compare OTM put IV vs OTM call IV from option chain
- iv_term_structure: Compare near-term vs far-term IV
- vix_vs_ma20: Calculate from VIX history
- volatility_trend: Track IV changes over time
- parkinson_vol, garman_klass_vol: Calculate from OHLC data
- vol_of_vol: Standard deviation of IV changes

---

### Category 4: Options Metrics (15 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| put_call_volume_ratio | Put/Call volume | 0.30 to 3.00 |
| put_call_oi_ratio | Put/Call OI | 0.30 to 3.00 |
| total_option_volume | Total volume | > 0 |
| total_open_interest | Total OI | > 0 |
| atm_delta_call, atm_delta_put | ATM deltas | 0.40 to 0.60, -0.60 to -0.40 |
| atm_gamma, atm_theta, atm_vega | ATM Greeks | Real values |
| max_pain_strike | Max pain | Near current price |
| distance_to_max_pain | Distance % | -0.10 to +0.10 |
| gamma_exposure | Aggregate gamma | Real values |
| delta_exposure | Aggregate delta | Real values |
| unusual_activity | Unusual volume? | 0 or 1 |
| options_flow_sentiment | Flow sentiment | -1 to +1 |

**Currently Missing:** total_open_interest, gamma_exposure, delta_exposure, unusual_activity, options_flow_sentiment

**Implementation:**
- total_open_interest: Sum OI across all options
- gamma_exposure: Sum (gamma × OI × 100) for all options
- delta_exposure: Sum (delta × OI × 100) for all options
- unusual_activity: Flag if volume > 2× average
- options_flow_sentiment: Net call volume - put volume, normalized

---

### Category 5: Support/Resistance (10 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| resistance_1 | Primary resistance | > current_price |
| resistance_2 | Secondary resistance | > resistance_1 |
| support_1 | Primary support | < current_price |
| support_2 | Secondary support | < support_1 |
| distance_to_resistance_1 | % to resistance | 0 to 0.20 |
| distance_to_support_1 | % to support | 0 to 0.20 |
| position_in_range | Position 0-1 | 0 to 1 |
| range_width | Range size % | 0.05 to 0.30 |
| days_in_range | Days since break | 0 to 60 |
| breakout_probability | Breakout estimate | 0 to 1 |

**Currently Missing:** resistance_2, support_2, range_width, days_in_range, breakout_probability

**Implementation:**
- resistance_2: Second highest peak in last 60 days
- support_2: Second lowest trough in last 60 days
- range_width: (resistance_1 - support_1) / current_price
- days_in_range: Days since price broke out of range
- breakout_probability: Based on position, volatility, momentum

---

### Category 6: Market Context (10 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| spy_correlation | 30-day correlation | -1 to +1 |
| spy_return_1d | SPY 1-day return | -0.10 to +0.10 |
| spy_return_5d | SPY 5-day return | -0.20 to +0.20 |
| smh_vs_spy | Relative performance | -0.10 to +0.10 |
| sector_rotation | Sector rotation score | -1 to +1 |
| market_breadth | Advance/decline | 0 to 1 |
| treasury_yield | 10-year yield | 2.0 to 6.0 |
| yield_curve_slope | 10Y - 2Y spread | -2.0 to +3.0 |
| risk_on_off | Risk appetite | -1 to +1 |
| vix_level, vix_change | VIX metrics | (counted in volatility) |

**Currently Missing:** spy_return_5d, smh_vs_spy, sector_rotation, market_breadth, treasury_yield, yield_curve_slope, risk_on_off

**Implementation:**
- spy_return_5d: Calculate from SPY history (already have SPY data)
- smh_vs_spy: SMH return - SPY return
- sector_rotation: Compare sector ETF performance (optional - can skip)
- market_breadth: NYSE advance/decline (optional - can skip)
- treasury_yield: From FRED API (optional - can skip)
- yield_curve_slope: 10Y - 2Y yields (optional - can skip)
- risk_on_off: Combine SPY/VIX signals

**Priority:** High for SPY features, Low for treasury/breadth

---

### Category 7: Regime Classification (5 features)
**Status:** MUST HAVE ALL

| Feature | Requirement | Validation |
|---------|-------------|------------|
| trend_regime | Trend classification | 0 to 4 |
| volatility_regime | Vol classification | 0 to 4 |
| volume_regime | Volume classification | 0 to 2 |
| combined_state | Combined regime | Categorical |
| days_since_regime_change | Regime stability | 0 to 60 |

**Currently Missing:** combined_state, days_since_regime_change

**Implementation:**
- combined_state: Combine trend + volatility + volume into single state
- days_since_regime_change: Track when regime last changed

---

## Strategy Requirements (10 Total)

### Minimum Representation per Strategy

| Strategy | Minimum Days | Target % | Typical Conditions |
|----------|--------------|----------|-------------------|
| IRON_CONDOR | 40 | 20-30% | High IV + Ranging |
| IRON_BUTTERFLY | 20 | 10-15% | Very High IV + Ranging |
| LONG_CALL | 30 | 15-20% | Low IV + Strong Uptrend |
| LONG_PUT | 30 | 15-20% | Low IV + Strong Downtrend |
| BULL_CALL_SPREAD | 30 | 10-15% | Medium IV + Moderate Bullish |
| BEAR_PUT_SPREAD | 30 | 10-15% | Medium IV + Moderate Bearish |
| LONG_STRADDLE | 15 | 5-10% | Pre-catalyst + High IV |
| LONG_STRANGLE | 15 | 5-10% | High IV + Uncertain direction |
| CALENDAR_SPREAD | 10 | 3-5% | Low IV + Neutral |
| DIAGONAL_SPREAD | 10 | 3-5% | Medium IV + Slight bias |

**Current Status:** Only 4 strategies present (FAIL)

**Requirements:**
- ✅ All 10 strategies must appear
- ✅ Each strategy minimum 10 days (preferably 20+)
- ✅ Distribution should match typical market conditions
- ✅ No single strategy > 40% of dataset

---

## Rules Engine Requirements

### Strategy Selection Logic

**MUST follow this decision tree:**

```
1. Check IV Rank:
   - If IV > 80: Consider LONG_STRADDLE
   - If IV > 70: Consider LONG_STRANGLE or IRON_BUTTERFLY
   - If IV > 60: Consider IRON_CONDOR
   - If IV < 35: Consider LONG_CALL/PUT or CALENDAR_SPREAD
   - If 40 <= IV <= 60: Consider SPREADS or DIAGONAL

2. Check Trend:
   - If ADX > 30 and trend_regime >= 3: LONG_CALL or BULL_CALL_SPREAD
   - If ADX > 30 and trend_regime <= 1: LONG_PUT or BEAR_PUT_SPREAD
   - If ADX < 20: IRON_CONDOR, IRON_BUTTERFLY, or CALENDAR_SPREAD

3. Check Volatility Regime:
   - If volatility_regime >= 3: Prefer selling premium (IC, IB)
   - If volatility_regime <= 1: Prefer buying options (Long, Calendar)

4. Check RSI:
   - If RSI > 70: Bearish bias (BEAR_PUT_SPREAD, LONG_PUT)
   - If RSI < 30: Bullish bias (BULL_CALL_SPREAD, LONG_CALL)
   - If 45 < RSI < 55: Neutral (IC, IB, STRADDLE, STRANGLE)
```

**Validation:**
- Test rules engine on known market conditions
- Verify each strategy gets selected appropriately
- Ensure no strategy is over/under-represented

---

## Label Quality Requirements

### Win Probability Standards

| Strategy Type | Expected Win Rate | Acceptable Range |
|---------------|-------------------|------------------|
| Iron Condor | 70-75% | 65-80% |
| Iron Butterfly | 65-70% | 60-75% |
| Spreads | 60-65% | 55-70% |
| Long Options | 50-55% | 45-60% |
| Straddles/Strangles | 45-50% | 40-55% |

**Requirements:**
- ✅ No strategy with 100% win rate (indicates bias)
- ✅ No strategy with <40% win rate (indicates poor selection)
- ✅ Win rates must vary by strategy type
- ✅ Win rates calculated from 30+ similar historical days

### Backtesting Requirements

**For EACH parameter combination:**
1. Find 30+ similar historical days
2. Simulate strategy on EACH similar day
3. Calculate aggregate statistics (not single day)
4. Win probability = wins / total_tests
5. Select best via risk-adjusted scoring

**Similarity Criteria:**
- IV Rank: ±10%
- Trend Regime: Same
- ADX: ±5
- RSI: ±10

**Minimum Tests:**
- 30+ similar days found
- 15-20 parameter combinations tested
- 450+ total simulations per day (30 days × 15 combos)

---

## Data Collection Requirements

### Historical Data Depth

| Feature Category | Minimum History | Recommended |
|------------------|----------------|-------------|
| Price Features | 200 days | 250 days |
| Technical Indicators | 50 days | 100 days |
| Volatility Features | 252 days (1 year) | 504 days (2 years) |
| Options Metrics | Same day | Same day |
| Support/Resistance | 60 days | 90 days |
| Market Context | 30 days | 60 days |

**Current Issue:** Data starts Jan 24, 2024 (insufficient for sma_200)

**Solution:**
- Extend data collection to start June 2023 (18 months)
- This provides 200+ days before Jan 2024 for sma_200
- Total dataset: June 2023 - Dec 2024 (18 months)

### Data Sources

| Data Type | Source | Cost | Required |
|-----------|--------|------|----------|
| SMH Options | Massive.com | $29/mo | ✅ Yes |
| SMH Stock | Massive.com | Included | ✅ Yes |
| SPY Stock | Massive.com | Included | ✅ Yes |
| VIX Index | Massive.com | Included | ✅ Yes |
| Treasury Yields | FRED API | Free | ⚠️ Optional |
| Market Breadth | NYSE | Free/Paid | ⚠️ Optional |

**Decision:** Use only Massive.com data (covers 95% of features)

---

## Validation Checklist

### Before Accepting Dataset

**Structure Validation:**
- [ ] One row per trading day (no duplicates)
- [ ] Date range covers sufficient history
- [ ] No individual option contract data present
- [ ] All columns have correct data types

**Feature Validation:**
- [ ] 80/80 features present (100% coverage)
- [ ] No feature has >5% missing values
- [ ] All features in valid ranges
- [ ] No constant features (std > 0)
- [ ] Feature correlations make sense

**Strategy Validation:**
- [ ] All 10 strategies represented
- [ ] Each strategy has minimum 10 days
- [ ] No strategy >40% of dataset
- [ ] Distribution matches market conditions

**Label Validation:**
- [ ] Win probabilities in acceptable ranges
- [ ] No 100% or 0% win rates
- [ ] Risk-adjusted scores positive
- [ ] Parameters valid for each strategy
- [ ] Backtesting used 30+ similar days

**Quality Metrics:**
- [ ] Overall quality score: 9/10 or higher
- [ ] Feature completeness: 100%
- [ ] Strategy diversity: 10/10
- [ ] Win probability realism: Pass
- [ ] Data integrity: Pass

---

## Implementation Plan

### Phase 1: Extend Data Collection (2-3 hours)
1. Modify data collection script to start June 2023
2. Collect 18 months of data (June 2023 - Dec 2024)
3. Verify all tickers present (SMH, SPY, VIX)
4. Save checkpoint files every 50 days

### Phase 2: Add Missing Features (1-2 hours)
1. Add 6 missing technical indicators
2. Add 7 missing volatility features
3. Add 5 missing options metrics
4. Add 5 missing support/resistance features
5. Add 7 missing market context features
6. Add 2 missing regime features
7. Validate all features calculated correctly

### Phase 3: Fix Strategy Selection (1 hour)
1. Rewrite rules engine with proper logic
2. Test on known market conditions
3. Verify all 10 strategies get selected
4. Ensure proper distribution

### Phase 4: Regenerate Labels (2-3 hours)
1. Run label creation on full dataset
2. Verify 30+ similar days used per test
3. Check win probabilities realistic
4. Validate strategy distribution
5. Ensure minimum representation per strategy

### Phase 5: Final Validation (30 min)
1. Run complete validation checklist
2. Generate quality report
3. Verify 9/10+ quality score
4. Document any remaining issues

**Total Time:** 6-10 hours
**Quality Target:** 9/10 minimum

---

## Success Criteria

### Dataset is READY when:

✅ **Feature Completeness:** 80/80 features (100%)  
✅ **Strategy Diversity:** 10/10 strategies present  
✅ **Minimum Representation:** Each strategy ≥10 days  
✅ **Win Probability:** Realistic ranges (45-75%)  
✅ **Data Quality:** <5% missing values  
✅ **Structure:** One row per day, no raw option data  
✅ **Historical Depth:** Sufficient for all features  
✅ **Validation:** All checks pass  
✅ **Quality Score:** 9/10 or higher  

### Dataset is NOT READY when:

❌ Missing features (anything <80)  
❌ Missing strategies (anything <10)  
❌ Unrealistic win rates (100% or <40%)  
❌ Insufficient data (can't calculate sma_200)  
❌ Poor strategy distribution (one strategy >40%)  
❌ High missing values (>5% in any feature)  
❌ Quality score <9/10  

---

## Maintenance & Updates

### When to Regenerate Dataset:

1. **New data available:** Monthly updates with latest trading days
2. **Feature improvements:** When new features are added
3. **Strategy changes:** When new strategies are implemented
4. **Quality issues:** When validation fails
5. **Model retraining:** Before each major model update

### Version Control:

- Tag each dataset with version number
- Document changes in CHANGELOG
- Keep previous versions for comparison
- Track quality scores over time

---

## Document Status

**Version:** 1.0  
**Last Updated:** December 5, 2024  
**Next Review:** After Phase 5 completion  
**Owner:** Data Engineering Team  
**Approval:** Required before production deployment  

---

**Remember:** No shortcuts. Production quality only. 9/10 minimum.
