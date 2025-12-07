"""
Advanced Feature Calculations for Phase 2
Adds 22 missing features to reach 80/80 target
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


# ============================================================================
# TECHNICAL INDICATORS (6 features)
# ============================================================================

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    On-Balance Volume (OBV)
    Cumulative volume indicator based on price direction
    """
    obv = [0.0]
    for i in range(1, len(df)):
        try:
            vol = float(df['volume'].iloc[i]) if df['volume'].iloc[i] != 'average' else 0.0
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + vol)
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - vol)
            else:
                obv.append(obv[-1])
        except (ValueError, TypeError):
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def calculate_stochastic(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator (%K and %D)
    Range: 0 to 100
    """
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    stoch_k = 100 * (df['close'] - low_min) / (high_max - low_min)
    stoch_d = stoch_k.rolling(window=3).mean()
    
    return stoch_k, stoch_d


def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Commodity Channel Index (CCI)
    Range: typically -200 to +200
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci


def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Williams %R
    Range: -100 to 0
    """
    high_max = df['high'].rolling(window=period).max()
    low_min = df['low'].rolling(window=period).min()
    
    williams_r = -100 * (high_max - df['close']) / (high_max - low_min)
    return williams_r


def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Money Flow Index (MFI)
    Range: 0 to 100
    """
    tp = (df['high'] + df['low'] + df['close']) / 3
    mf = tp * df['volume']
    
    mf_pos = pd.Series(0.0, index=df.index)
    mf_neg = pd.Series(0.0, index=df.index)
    
    for i in range(1, len(df)):
        if tp.iloc[i] > tp.iloc[i-1]:
            mf_pos.iloc[i] = mf.iloc[i]
        elif tp.iloc[i] < tp.iloc[i-1]:
            mf_neg.iloc[i] = mf.iloc[i]
    
    mf_pos_sum = mf_pos.rolling(window=period).sum()
    mf_neg_sum = mf_neg.rolling(window=period).sum()
    
    mfr = mf_pos_sum / mf_neg_sum
    mfi = 100 - (100 / (1 + mfr))
    
    return mfi


# ============================================================================
# VOLATILITY FEATURES (7 features)
# ============================================================================

def calculate_iv_skew(options_df: pd.DataFrame, current_price: float) -> float:
    """
    IV Skew: OTM Put IV - OTM Call IV
    Range: -0.10 to +0.10
    """
    # OTM puts: strike < current_price
    otm_puts = options_df[
        (options_df['type'] == 'put') & 
        (options_df['strike'] < current_price * 0.95)
    ]
    
    # OTM calls: strike > current_price
    otm_calls = options_df[
        (options_df['type'] == 'call') & 
        (options_df['strike'] > current_price * 1.05)
    ]
    
    if len(otm_puts) > 0 and len(otm_calls) > 0:
        put_iv = otm_puts['implied_volatility'].mean()
        call_iv = otm_calls['implied_volatility'].mean()
        return put_iv - call_iv
    return 0.0


def calculate_iv_term_structure(options_df: pd.DataFrame) -> float:
    """
    IV Term Structure: Near-term IV - Far-term IV
    Range: -0.10 to +0.10
    """
    # Near-term: DTE < 30
    near_term = options_df[options_df['dte'] < 30]
    
    # Far-term: DTE > 60
    far_term = options_df[options_df['dte'] > 60]
    
    if len(near_term) > 0 and len(far_term) > 0:
        near_iv = near_term['implied_volatility'].mean()
        far_iv = far_term['implied_volatility'].mean()
        return near_iv - far_iv
    return 0.0


def calculate_vix_vs_ma20(vix_history: pd.Series) -> float:
    """
    VIX vs 20-day MA
    Range: -0.30 to +0.30
    """
    if len(vix_history) >= 20:
        current_vix = vix_history.iloc[-1]
        vix_ma20 = vix_history.iloc[-20:].mean()
        return (current_vix - vix_ma20) / vix_ma20
    return 0.0


def calculate_volatility_trend(iv_history: pd.Series) -> int:
    """
    Volatility Trend: Is IV increasing?
    Returns: 1 if increasing, 0 if decreasing
    """
    if len(iv_history) >= 5:
        recent_iv = iv_history.iloc[-3:].mean()
        older_iv = iv_history.iloc[-6:-3].mean()
        return 1 if recent_iv > older_iv else 0
    return 0


def calculate_parkinson_vol(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Parkinson Volatility (High-Low estimator)
    More efficient than close-to-close
    Range: 0.10 to 1.00
    """
    hl_ratio = np.log(df['high'] / df['low'])
    parkinson = np.sqrt((1 / (4 * np.log(2))) * hl_ratio ** 2)
    return parkinson.rolling(window=period).mean() * np.sqrt(252)


def calculate_garman_klass_vol(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Garman-Klass Volatility (OHLC estimator)
    Most efficient volatility estimator
    Range: 0.10 to 1.00
    """
    hl = np.log(df['high'] / df['low']) ** 2
    co = np.log(df['close'] / df['open']) ** 2
    
    gk = 0.5 * hl - (2 * np.log(2) - 1) * co
    return np.sqrt(gk.rolling(window=period).mean() * 252)


def calculate_vol_of_vol(iv_history: pd.Series, period: int = 20) -> float:
    """
    Volatility of Volatility
    Standard deviation of IV changes
    Range: 0.01 to 0.50
    """
    if len(iv_history) >= period:
        return iv_history.iloc[-period:].std()
    return 0.0


# ============================================================================
# OPTIONS METRICS (4 features - total_open_interest already exists)
# ============================================================================

def calculate_gamma_exposure(options_df: pd.DataFrame) -> float:
    """
    Aggregate Gamma Exposure
    Sum of (gamma × OI × 100) for all options
    """
    return (options_df['gamma'] * options_df['open_interest'] * 100).sum()


def calculate_delta_exposure(options_df: pd.DataFrame) -> float:
    """
    Aggregate Delta Exposure
    Sum of (delta × OI × 100) for all options
    """
    return (options_df['delta'] * options_df['open_interest'] * 100).sum()


def calculate_unusual_activity(current_volume: float, avg_volume: float) -> int:
    """
    Unusual Activity Flag
    Returns: 1 if volume > 2× average, else 0
    """
    return 1 if current_volume > 2 * avg_volume else 0


def calculate_options_flow_sentiment(options_df: pd.DataFrame) -> float:
    """
    Options Flow Sentiment
    (Call Volume - Put Volume) / Total Volume
    Range: -1 to +1
    """
    call_volume = options_df[options_df['type'] == 'call']['transactions'].sum()
    put_volume = options_df[options_df['type'] == 'put']['transactions'].sum()
    total_volume = call_volume + put_volume
    
    if total_volume > 0:
        return (call_volume - put_volume) / total_volume
    return 0.0


# ============================================================================
# SUPPORT/RESISTANCE (5 features)
# ============================================================================

def find_support_resistance_levels(price_history: pd.Series, n_levels: int = 2) -> Dict:
    """
    Find multiple support and resistance levels
    Returns: resistance_1, resistance_2, support_1, support_2
    """
    if len(price_history) < 30:
        current = price_history.iloc[-1]
        return {
            'resistance_1': current * 1.05,
            'resistance_2': current * 1.10,
            'support_1': current * 0.95,
            'support_2': current * 0.90
        }
    
    # Find local maxima (resistance) and minima (support)
    window = 5
    highs = []
    lows = []
    
    for i in range(window, len(price_history) - window):
        if price_history.iloc[i] == price_history.iloc[i-window:i+window+1].max():
            highs.append(price_history.iloc[i])
        if price_history.iloc[i] == price_history.iloc[i-window:i+window+1].min():
            lows.append(price_history.iloc[i])
    
    current_price = price_history.iloc[-1]
    
    # Get resistance levels (above current price)
    resistances = sorted([h for h in highs if h > current_price])
    resistance_1 = resistances[0] if len(resistances) > 0 else current_price * 1.05
    resistance_2 = resistances[1] if len(resistances) > 1 else current_price * 1.10
    
    # Get support levels (below current price)
    supports = sorted([l for l in lows if l < current_price], reverse=True)
    support_1 = supports[0] if len(supports) > 0 else current_price * 0.95
    support_2 = supports[1] if len(supports) > 1 else current_price * 0.90
    
    return {
        'resistance_1': resistance_1,
        'resistance_2': resistance_2,
        'support_1': support_1,
        'support_2': support_2
    }


def calculate_range_width(resistance: float, support: float, current_price: float) -> float:
    """
    Range Width: (Resistance - Support) / Current Price
    Range: 0.05 to 0.30
    """
    return (resistance - support) / current_price


def calculate_days_in_range(price_history: pd.Series, resistance: float, support: float) -> int:
    """
    Days Since Breakout
    Count days since price broke out of range
    Range: 0 to 60
    """
    days = 0
    for i in range(len(price_history) - 1, -1, -1):
        price = price_history.iloc[i]
        if support <= price <= resistance:
            days += 1
        else:
            break
    return min(days, 60)


def calculate_breakout_probability(
    position_in_range: float,
    volatility: float,
    adx: float
) -> float:
    """
    Breakout Probability Estimate
    Based on position, volatility, and momentum
    Range: 0 to 1
    """
    # Near edges = higher breakout probability
    edge_factor = 1 - abs(position_in_range - 0.5) * 2
    
    # High volatility = higher breakout probability
    vol_factor = min(volatility / 0.5, 1.0)
    
    # High ADX = higher breakout probability
    adx_factor = min(adx / 40, 1.0)
    
    # Weighted average
    probability = (edge_factor * 0.4 + vol_factor * 0.3 + adx_factor * 0.3)
    return max(0.0, min(1.0, probability))


# ============================================================================
# MARKET CONTEXT (2 features)
# ============================================================================

def calculate_spy_return_5d(spy_history: pd.Series) -> float:
    """
    SPY 5-day return
    Range: -0.20 to +0.20
    """
    if len(spy_history) >= 5:
        return (spy_history.iloc[-1] - spy_history.iloc[-5]) / spy_history.iloc[-5]
    return 0.0


def calculate_smh_vs_spy(smh_return: float, spy_return: float) -> float:
    """
    Relative Performance: SMH vs SPY
    Range: -0.10 to +0.10
    """
    return smh_return - spy_return


# ============================================================================
# REGIME CLASSIFICATION (2 features)
# ============================================================================

def calculate_combined_state(trend_regime: int, volatility_regime: int, volume_regime: int) -> int:
    """
    Combined State: Encode all three regimes into single number
    Formula: (trend × 15) + (volatility × 3) + volume
    Range: 0 to 74
    """
    return (trend_regime * 15) + (volatility_regime * 3) + volume_regime


def calculate_days_since_regime_change(regime_history: pd.Series) -> int:
    """
    Days Since Regime Change
    Count consecutive days in current regime
    Range: 0 to 60
    """
    if len(regime_history) < 2:
        return 0
    
    current_regime = regime_history.iloc[-1]
    days = 0
    
    for i in range(len(regime_history) - 1, -1, -1):
        if regime_history.iloc[i] == current_regime:
            days += 1
        else:
            break
    
    return min(days, 60)
