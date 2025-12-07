# Live Prediction Test Results

**Test Date:** 2025-12-06 14:15:55  
**Prediction Date:** 2025-11-06  
**Model:** LightGBM (84.21% accuracy)  
**Feature Extractor:** v1.0

---

## Executive Summary

**🎯 PREDICTED STRATEGY:** LONG_STRANGLE  
**Confidence:** 72.2%  
**Market Regime:** Ranging / Low Volatility

---

## STEP 1: INPUT DATA

### Option Chain

**Source:** SMH Historical Data  
**Date:** 2025-11-06  
**Total Contracts:** 222  
**Calls:** 104  
**Puts:** 118

**Strike Range:** $250 - $450  
**DTE Range:** 8 - 71 days

**Sample (10 ATM Options):**

```
Empty DataFrame
Columns: [strike, type, dte, bid, ask, volume, open_interest, iv, delta, gamma]
Index: []
```

### Price History

**Records:** 480 days  
**Date Range:** 2023-12-08 to 2025-11-06

**Last 5 Days:**

```
      date  open     high      low  close   volume
2025-10-31 72.71 73.07355 72.34645  72.71 50000000
2025-11-03 66.70 67.03350 66.36650  66.70 50000000
2025-11-04 27.40 27.53700 27.26300  27.40 50000000
2025-11-05 79.98 80.37990 79.58010  79.98 50000000
2025-11-06 81.90 82.30950 81.49050  81.90 50000000
```

---

## STEP 2: EXTRACTED FEATURES (84 Total)

### Key Features

```
current_price                  =      81.90
return_1d                      =     0.0240
return_5d                      =    -0.1394
rsi_14                         =      46.99
adx_14                         =       5.52
iv_atm                         =     0.2500
iv_rank                        =      28.57
hv_iv_ratio                    =    43.5834
put_call_volume_ratio          =     1.1346
atm_gamma                      =     0.0500
trend_regime                   =          2
volatility_regime              =          1
```

### Market Interpretation

**Price Action:**
- Current: $81.90
- 1-Day Return: +2.40%
- 5-Day Return: -13.94%

**Technical:**
- RSI: 47.0 (Neutral)
- ADX: 5.5 (Weak/Ranging)

**Volatility:**
- IV Rank: 28.6% (Low)
- HV/IV: 43.58 (IV Cheap)

**Regime:**
- Trend: Ranging
- Volatility: Low

---

## STEP 3: MODEL PREDICTION

**🎯 PREDICTED STRATEGY: LONG_STRANGLE**  
**Confidence: 72.2%**

### Top 3 Strategies

```
1. LONG_STRANGLE              72.2%
2. LONG_CALL                  15.3%
3. IRON_CONDOR                 3.7%
```

### Confidence Analysis

⚠️ **MODERATE CONFIDENCE** - Reasonable signal

---

## STEP 4: TRADE PARAMETERS (STAGE 2)

### Generated Parameters for LONG_STRANGLE

```
dte                       = 36
call_strike               = 330.00
put_strike                = 305.00
call_cost                 = $3,032.46
put_cost                  = $304.98
total_cost                = $3,337.44
max_loss                  = $3,337.44
breakeven_up              = 363.37
breakeven_down            = 271.63
contracts                 = 1
```

### Execution Instructions

1. **Buy to Open:** $330 Call ($3032.46)
2. **Buy to Open:** $305 Put ($304.98)
3. **Expiration:** 36 days
4. **Total Cost:** $3337.44
5. **Breakeven Up:** $363.37
6. **Breakeven Down:** $271.63

---

## Summary

### Complete Workflow

```
Raw Option Chain (222 contracts)
    ↓
Feature Extraction (84 features)
    ↓
ML Model (LightGBM)
    ↓
Strategy: LONG_STRANGLE (72.2%)
```

### Performance

- Feature Extraction: ~100ms
- Model Prediction: <10ms
- Total Time: ~110ms

---

**Test Status:** ✅ PASSED  
**Generated:** 2025-12-06 14:15:55
