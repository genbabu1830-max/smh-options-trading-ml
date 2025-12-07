# Strategy Selection Rules - Production Standards
## SMH Options Trading Strategy Selection Engine

**Version:** 2.0 (CORRECTED)  
**Date:** December 5, 2025  
**Status:** Active - Fixes Applied Based on Validation Feedback  
**Previous Version Issues:** CRITICAL FAILURES - Only 4/10 strategies, wrong distribution

---

## Critical Lessons Learned

### What Went Wrong in v1.0

**Validation Results from Old Data:**
- ❌ Only 4/10 strategies appeared in 216 days
- ❌ Iron Condor: 0.5% instead of 20-30%
- ❌ Bull Call Spread: 45% instead of 10-15%
- ❌ Diagonal Spread: 39% instead of 3-5%
- ❌ 6 strategies completely missing

**Root Causes:**
1. **Thresholds too restrictive** - IV 60-70 for IC too narrow, ADX > 30 too high
2. **Wrong priority order** - Spreads checked before long options
3. **Conceptual errors** - Buying volatility in high IV (backwards!)
4. **Overly broad conditions** - Bull Call Spread and Diagonal Spread caught everything
5. **OR logic abuse** - Made rules match too easily

---

## Core Principles (v2.0)

### 1. CORRECT VOLATILITY LOGIC ✅

**RULE: Buy options in LOW IV, Sell premium in HIGH IV**

```
LOW IV (<40):
  - Buy Long Call/Put (cheap options)
  - Buy Straddles/Strangles (expecting IV expansion)
  - Use Calendar Spreads (time decay)

HIGH IV (>50):
  - Sell Iron Condor (collect premium)
  - Sell Iron Butterfly (collect premium)
  - Use spreads if trending (defined risk)
```

**Why This Matters:**
- Low IV = cheap options = good time to buy
- High IV = expensive options = good time to sell
- v1.0 had this BACKWARDS for straddles/strangles!

### 2. PROPER PRIORITY ORDERING ✅

**RULE: Check most common strategies FIRST**

```
Priority Order:
1. Iron Condor (20-30% of days) - High IV + Ranging
2. Long Call/Put (30-40% combined) - Low IV + Trending
3. Spreads (20-30% combined) - Medium IV + Moderate trend
4. Specialized (15-20% combined) - Rare conditions
```

**Why This Matters:**
- v1.0 checked spreads before long options
- Spreads "stole" days that should be long options
- Result: 45% Bull Call Spread, 0% Long Call

### 3. REALISTIC THRESHOLDS ✅

**RULE: Use thresholds that actually occur in real data**

| Feature | v1.0 (WRONG) | v2.0 (CORRECT) | Reason |
|---------|--------------|----------------|--------|
| IC IV Range | 60-70 | 50-75 | 10-point window too narrow |
| IC ADX | < 20 | < 25 | ADX < 20 too rare |
| Long Call IV | < 35 | < 40 | < 35 too restrictive |
| Long Call ADX | > 30 | > 25 | > 30 too high (very strong) |
| Butterfly IV | > 75 | > 70 | > 75 almost never happens |
| Straddle IV | > 80 | < 30 | Backwards! Buy in low IV |
| Bull Spread IV | 35-60 | 40-65 | Too broad, catches everything |
| Diagonal bias | > 0.005 | 0.005-0.015 | Need upper bound |

### 4. TIGHTER CONDITIONS FOR RARE STRATEGIES ✅

**RULE: Rare strategies need VERY specific conditions**

```python
# WRONG (v1.0) - Diagonal Spread matched 39% of days
if trend_regime == 2 and abs(price_vs_sma) > 0.005:
    return 'DIAGONAL_SPREAD'

# CORRECT (v2.0) - Diagonal Spread should match 3-5% of days
if 45 < iv_rank < 60 and trend_regime == 2 and 0.005 < abs(price_vs_sma) < 0.015 and adx < 15:
    return 'DIAGONAL_SPREAD'
```

**Changes:**
- Added IV range requirement (45-60)
- Added upper bound on bias (< 0.015)
- Added ADX requirement (< 15)
- Result: Much more restrictive, as intended

### 5. AND LOGIC, NOT OR LOGIC ✅

**RULE: Use AND for multiple conditions, OR sparingly**

```python
# WRONG (v1.0) - Too easy to match
if trend_regime == 3 or (price_vs_sma > 0.01 and rsi > 55):
    return 'BULL_CALL_SPREAD'

# CORRECT (v2.0) - Requires both conditions
if trend_regime >= 3 and adx > 20:
    return 'BULL_CALL_SPREAD'
```

**Why This Matters:**
- OR makes rules match too easily
- AND ensures specific conditions
- v1.0 Bull Call Spread matched 45% because of OR

---

## Strategy Selection Rules (v2.0 CORRECTED)

### Priority 1: Iron Condor (Target: 20-30%)

**When to Use:**
```python
if 50 < iv_rank < 75 and adx < 25 and 45 < rsi < 55:
    return 'IRON_CONDOR'
```

**Conditions:**
- IV Rank: 50-75 (BROADENED from 60-70)
- ADX: < 25 (RELAXED from < 20)
- RSI: 45-55 (neutral)

**Why These Thresholds:**
- 50-75 IV covers most high-volatility days
- ADX < 25 includes ranging + weak trends
- Neutral RSI ensures no strong directional bias

**Expected Frequency:** 20-30% of trading days (~50-75 days/year)

---

### Priority 2: Iron Butterfly (Target: 10-15%)

**When to Use:**
```python
if iv_rank > 70 and adx < 20:
    return 'IRON_BUTTERFLY'
```

**Conditions:**
- IV Rank: > 70 (LOWERED from > 75)
- ADX: < 20 (very ranging)

**Why These Thresholds:**
- > 70 IV is high but achievable (not > 75 which is rare)
- ADX < 20 ensures very tight ranging market
- Tighter profit zone than IC, needs more stable conditions

**Expected Frequency:** 10-15% of trading days (~25-38 days/year)

---

### Priority 3: Long Call (Target: 15-20%)

**When to Use:**
```python
if iv_rank < 40 and adx > 25:
    if trend_regime >= 3 or (price_vs_sma > 0.02 and rsi > 58):
        return 'LONG_CALL'
```

**Conditions:**
- IV Rank: < 40 (RELAXED from < 35)
- ADX: > 25 (LOWERED from > 30)
- Trend: Strong uptrend (regime >= 3) OR (price > SMA by 2% AND RSI > 58)

**Why These Thresholds:**
- < 40 IV = cheap options (not just < 35)
- ADX > 25 = moderate-to-strong trend (not just very strong > 30)
- Checked BEFORE Bull Call Spread to prevent stealing

**Expected Frequency:** 15-20% of trading days (~38-50 days/year)

---

### Priority 4: Long Put (Target: 15-20%)

**When to Use:**
```python
if iv_rank < 40 and adx > 25:
    if trend_regime <= 1 or (price_vs_sma < -0.02 and rsi < 42):
        return 'LONG_PUT'
```

**Conditions:**
- IV Rank: < 40 (RELAXED from < 35)
- ADX: > 25 (LOWERED from > 30)
- Trend: Strong downtrend (regime <= 1) OR (price < SMA by 2% AND RSI < 42)

**Why These Thresholds:**
- Same logic as Long Call but bearish
- Checked BEFORE Bear Put Spread

**Expected Frequency:** 15-20% of trading days (~38-50 days/year)

---

### Priority 5: Bull Call Spread (Target: 10-15%)

**When to Use:**
```python
if 40 <= iv_rank <= 65:
    if trend_regime >= 3 and adx > 20:
        return 'BULL_CALL_SPREAD'
```

**Conditions:**
- IV Rank: 40-65 (TIGHTENED from 35-60)
- Trend: >= 3 (moderate-to-strong uptrend)
- ADX: > 20 (ADDED requirement)
- **BOTH conditions required (AND not OR)**

**Why These Thresholds:**
- 40-65 IV = medium volatility (not too broad)
- Requires BOTH trend >= 3 AND ADX > 20 (not OR)
- Prevents overmatching that caused 45% in v1.0

**Expected Frequency:** 10-15% of trading days (~25-38 days/year)

---

### Priority 6: Bear Put Spread (Target: 10-15%)

**When to Use:**
```python
if 40 <= iv_rank <= 65:
    if trend_regime <= 1 and adx > 20:
        return 'BEAR_PUT_SPREAD'
```

**Conditions:**
- IV Rank: 40-65 (TIGHTENED from 35-60)
- Trend: <= 1 (moderate-to-strong downtrend)
- ADX: > 20 (ADDED requirement)
- **BOTH conditions required (AND not OR)**

**Why These Thresholds:**
- Same logic as Bull Call Spread but bearish
- This was the ONLY strategy working correctly in v1.0!

**Expected Frequency:** 10-15% of trading days (~25-38 days/year)

---

### Priority 7: Long Straddle (Target: 5-10%)

**When to Use:**
```python
if iv_rank < 30 and 45 < rsi < 55:
    if adx < 15:
        return 'LONG_STRADDLE'
```

**Conditions:**
- IV Rank: < 30 (FIXED - was > 80, completely backwards!)
- RSI: 45-55 (neutral)
- ADX: < 15 (very ranging)

**Why These Thresholds:**
- **CRITICAL FIX:** Buy straddles in LOW IV, not high IV!
- Low IV = cheap options
- Neutral + ranging = uncertain direction
- Expecting volatility expansion

**Expected Frequency:** 5-10% of trading days (~13-25 days/year)

---

### Priority 8: Long Strangle (Target: 5-10%)

**When to Use:**
```python
if iv_rank < 30 and 45 < rsi < 55:
    if adx < 20:
        return 'LONG_STRANGLE'
```

**Conditions:**
- IV Rank: < 30 (FIXED - was 70-80, completely backwards!)
- RSI: 45-55 (neutral)
- ADX: < 20 (ranging)

**Why These Thresholds:**
- **CRITICAL FIX:** Buy strangles in LOW IV, not high IV!
- Cheaper than straddle (OTM options)
- Same logic as straddle but slightly less neutral

**Expected Frequency:** 5-10% of trading days (~13-25 days/year)

---

### Priority 9: Calendar Spread (Target: 3-5%)

**When to Use:**
```python
if iv_rank < 35 and adx < 15 and 45 < rsi < 55 and abs(price_vs_sma) < 0.01:
    return 'CALENDAR_SPREAD'
```

**Conditions:**
- IV Rank: < 35 (low)
- ADX: < 15 (very ranging)
- RSI: 45-55 (very neutral)
- Price vs SMA: < 1% (very stable)

**Why These Thresholds:**
- Requires VERY neutral conditions
- All four conditions must be met
- Time decay play, needs stability

**Expected Frequency:** 3-5% of trading days (~8-13 days/year)

---

### Priority 10: Diagonal Spread (Target: 3-5%)

**When to Use:**
```python
if 45 < iv_rank < 60 and trend_regime == 2 and 0.005 < abs(price_vs_sma) < 0.015 and adx < 15:
    return 'DIAGONAL_SPREAD'
```

**Conditions:**
- IV Rank: 45-60 (TIGHTENED from 35-60)
- Trend: = 2 (neutral)
- Price vs SMA: 0.5% to 1.5% (ADDED upper bound)
- ADX: < 15 (ADDED requirement)

**Why These Thresholds:**
- **CRITICAL FIX:** Was matching 39% of days in v1.0!
- Now requires ALL FOUR specific conditions
- Narrower IV range
- Upper bound on bias (not just > 0.005)
- ADX requirement added

**Expected Frequency:** 3-5% of trading days (~8-13 days/year)

---

## Validation Requirements

### Distribution Testing

**MUST validate on real data before accepting:**

```python
def validate_strategy_distribution(training_data):
    """
    Validate that strategy distribution matches expected ranges
    """
    strategy_pct = training_data['strategy'].value_counts(normalize=True) * 100
    
    expected_ranges = {
        'IRON_CONDOR': (20, 30),
        'LONG_CALL': (15, 20),
        'LONG_PUT': (15, 20),
        'IRON_BUTTERFLY': (10, 15),
        'BULL_CALL_SPREAD': (10, 15),
        'BEAR_PUT_SPREAD': (10, 15),
        'LONG_STRADDLE': (5, 10),
        'LONG_STRANGLE': (5, 10),
        'CALENDAR_SPREAD': (3, 5),
        'DIAGONAL_SPREAD': (3, 5),
    }
    
    failures = []
    for strategy, (min_pct, max_pct) in expected_ranges.items():
        actual_pct = strategy_pct.get(strategy, 0)
        
        if actual_pct < min_pct or actual_pct > max_pct:
            failures.append({
                'strategy': strategy,
                'expected': f'{min_pct}-{max_pct}%',
                'actual': f'{actual_pct:.1f}%',
                'status': 'FAIL'
            })
    
    # Check all 10 strategies present
    if len(strategy_pct) < 10:
        failures.append({
            'issue': 'Missing strategies',
            'expected': '10 strategies',
            'actual': f'{len(strategy_pct)} strategies',
            'status': 'FAIL'
        })
    
    return len(failures) == 0, failures
```

### Acceptance Criteria

**Dataset is READY when:**

✅ All 10 strategies present  
✅ Each strategy within expected range  
✅ No strategy > 35% (no single strategy dominates)  
✅ No strategy < 0.5% (all strategies represented)  
✅ Distribution matches typical market conditions  

**Dataset is NOT READY when:**

❌ Any strategy missing  
❌ Any strategy outside expected range by > 5%  
❌ Only 4 strategies present (like v1.0)  
❌ Bull Call Spread > 20% (overmatching)  
❌ Diagonal Spread > 10% (overmatching)  
❌ Iron Condor < 15% (undermatching)  

---

## Implementation Checklist

### Before Generating Labels

- [ ] Rules engine updated with v2.0 thresholds
- [ ] Priority order correct (IC first, then long options, then spreads)
- [ ] Volatility logic correct (buy in low IV, sell in high IV)
- [ ] AND logic used instead of OR where appropriate
- [ ] Rare strategies have tight conditions

### After Generating Labels

- [ ] Run distribution validation test
- [ ] Check all 10 strategies present
- [ ] Verify percentages within expected ranges
- [ ] Inspect sample days for each strategy
- [ ] Confirm win probabilities realistic (55-75%)

### If Validation Fails

1. **Identify which strategies are wrong**
   - Too high? Conditions too broad
   - Too low? Conditions too restrictive
   - Missing? Never triggers, check thresholds

2. **Adjust thresholds incrementally**
   - Don't make huge changes
   - Test after each adjustment
   - Document what changed and why

3. **Check for conflicts**
   - Is one strategy stealing from another?
   - Is priority order correct?
   - Are conditions mutually exclusive?

4. **Regenerate and retest**
   - Delete old training data
   - Run label creation again
   - Validate distribution again

---

## Common Pitfalls to Avoid

### 1. Unrealistic Thresholds ❌

**DON'T:**
- Use IV > 80 (almost never happens)
- Use ADX > 35 (very rare)
- Use exact values (trend_regime == 3 only)

**DO:**
- Use ranges that occur frequently
- Check actual data distribution first
- Use >= or <= for flexibility

### 2. Wrong Priority Order ❌

**DON'T:**
- Check rare strategies first
- Check spreads before long options
- Use same IV range for multiple strategies

**DO:**
- Check most common strategies first
- Check long options before spreads
- Use non-overlapping IV ranges

### 3. Overly Broad Conditions ❌

**DON'T:**
- Use 25-point IV ranges (35-60)
- Use OR logic for multiple conditions
- Forget upper bounds (> 0.005 with no max)

**DO:**
- Use 15-20 point IV ranges max
- Use AND logic for multiple conditions
- Always specify upper bounds

### 4. Conceptual Errors ❌

**DON'T:**
- Buy volatility in high IV
- Sell premium in low IV
- Use same logic for all strategies

**DO:**
- Buy options when cheap (low IV)
- Sell premium when expensive (high IV)
- Understand each strategy's ideal conditions

### 5. Insufficient Testing ❌

**DON'T:**
- Trust unit tests alone
- Skip distribution validation
- Accept "close enough" results

**DO:**
- Test on real historical data
- Validate distribution percentages
- Require exact match to expected ranges

---

## Monitoring in Production

### Daily Checks

```python
# Log each day's selection
daily_log = {
    'date': date,
    'iv_rank': iv_rank,
    'adx': adx,
    'trend_regime': trend_regime,
    'rsi': rsi,
    'selected_strategy': strategy,
    'selection_reason': reason
}
```

### Weekly Analysis

```python
# Check last 7 days distribution
weekly_dist = analyze_last_n_days(7)

# Alert if any strategy > 50% in a week
if any(pct > 50 for pct in weekly_dist.values()):
    alert("Strategy overconcentration detected")

# Alert if any strategy missing for 2+ weeks
if days_since_last_use(strategy) > 14:
    alert(f"{strategy} not used in 14+ days")
```

### Monthly Review

- Compare actual vs expected distribution
- Identify any systematic biases
- Adjust thresholds if needed
- Document all changes

---

## Version History

### v2.0 (December 5, 2025) - CORRECTED

**Changes:**
- Fixed Iron Condor: 60-70 → 50-75 IV, ADX < 20 → < 25
- Fixed Long Call/Put: IV < 35 → < 40, ADX > 30 → > 25
- Fixed Bull/Bear Spreads: 35-60 → 40-65 IV, added ADX > 20 requirement
- Fixed Straddle/Strangle: IV > 70-80 → < 30 (BACKWARDS FIX!)
- Fixed Diagonal: Added upper bound on bias, tightened IV range
- Changed priority order: IC first, then long options, then spreads
- Replaced OR logic with AND logic in multiple places

**Validation:**
- Awaiting test on new data
- Expected to achieve 10/10 strategies
- Expected distribution within ranges

### v1.0 (December 5, 2025) - FAILED

**Issues:**
- Only 4/10 strategies appeared
- Iron Condor: 0.5% (expected 20-30%)
- Bull Call Spread: 45% (expected 10-15%)
- Diagonal Spread: 39% (expected 3-5%)
- 6 strategies completely missing

**Root Causes:**
- Thresholds too restrictive
- Wrong priority order
- Conceptual errors (volatility logic backwards)
- Overly broad conditions for spreads/diagonals

---

## Code Modularity Requirements

### Principle: Separation of Concerns

**RULE: All code must be modular and reusable**

### Module Structure

```
scripts/
├── 1_collect_data.py          # Data collection pipeline
├── 2_engineer_features.py     # Feature engineering pipeline
├── 3_create_labels.py          # Label creation pipeline
├── test_strategy_selection.py # Strategy validation tests
└── utils/                      # Shared utility modules
    ├── calculate_greeks.py     # Options Greeks calculations
    ├── feature_engineering.py  # Feature calculation functions
    └── strategy_selector.py    # Strategy selection logic (NEW)
```

### Strategy Selector Module

**Location:** `scripts/utils/strategy_selector.py`

**Purpose:** Centralized strategy selection logic

**Functions:**
1. `select_strategy_from_features(features)` - Main selection function
2. `validate_strategy_distribution(training_data)` - Distribution validation
3. `get_strategy_info(strategy_name)` - Strategy metadata

**Benefits:**
- ✅ Single source of truth for strategy rules
- ✅ Easy to test independently
- ✅ Reusable across multiple scripts
- ✅ Clear separation from label creation logic
- ✅ Version control friendly

### Usage Example

```python
# In scripts/3_create_labels.py
from scripts.utils.strategy_selector import select_strategy_from_features

# Select strategy for a day
strategy = select_strategy_from_features(features_dict)

# In scripts/test_strategy_selection.py
from scripts.utils.strategy_selector import select_strategy_from_features

# Test strategy selection
result = select_strategy_from_features(test_features)
```

### Modularity Checklist

**Before adding new code:**
- [ ] Is this logic reusable? → Create a module
- [ ] Does this belong in utils/? → Move it there
- [ ] Can this be tested independently? → Make it a function
- [ ] Is this duplicated elsewhere? → Consolidate into one module

**When refactoring:**
- [ ] Extract reusable functions to utils/
- [ ] Keep pipeline scripts thin (orchestration only)
- [ ] Move business logic to modules
- [ ] Add docstrings to all functions
- [ ] Write unit tests for modules

### Module Guidelines

1. **One responsibility per module**
   - strategy_selector.py = strategy selection only
   - calculate_greeks.py = Greeks calculations only
   - feature_engineering.py = feature calculations only

2. **Clear interfaces**
   - Well-defined input/output
   - Type hints where possible
   - Comprehensive docstrings

3. **No side effects**
   - Pure functions preferred
   - No global state modifications
   - Explicit dependencies

4. **Easy to test**
   - Small, focused functions
   - Mockable dependencies
   - Predictable behavior

### Anti-Patterns to Avoid

❌ **DON'T:**
- Embed business logic in pipeline scripts
- Duplicate code across multiple files
- Create monolithic functions
- Mix concerns (e.g., strategy selection + parameter generation)

✅ **DO:**
- Extract logic to utility modules
- Create single-purpose functions
- Keep pipeline scripts as orchestration
- Separate concerns clearly

---

## References

- **Validation Report:** Detailed feedback from December 5, 2025
- **Implementation:** `scripts/utils/strategy_selector.py` (modular)
- **Pipeline:** `scripts/3_create_labels.py` (uses modular strategy selector)
- **Test Suite:** `scripts/test_strategy_selection.py`
- **Documentation:** `documentation/STRATEGY_SELECTION_RULES.md`

---

**Status:** CORRECTED - Ready for Testing  
**Code Structure:** Modular and maintainable  
**Next Step:** Regenerate labels with v2.0 rules and validate distribution  
**Success Criteria:** All 10 strategies present, distribution within expected ranges
