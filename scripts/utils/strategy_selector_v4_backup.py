"""
Strategy Selection Module
Determines optimal options strategy based on market conditions

Version: 4.0 (BROADER RULES ALIGNED)
Date: December 6, 2024
Status: Production Ready

This module implements the corrected strategy selection rules based on
validation feedback. See .kiro/steering/strategy-selection-rules.md for
detailed documentation.
"""


def select_strategy_from_features(features):
    """
    CORRECTED rule-based strategy selection based on validation feedback
    
    Key fixes from validation report:
    - Broadened Iron Condor conditions (50-75 IV, ADX < 25)
    - Relaxed Long Call/Put thresholds (IV < 40, ADX > 25)
    - Tightened Bull/Bear Spread conditions (40-65 IV, stronger trend)
    - Fixed volatility plays (buy in LOW IV, not high)
    - Made Diagonal Spread much more restrictive
    - Proper priority ordering to prevent overmatching
    
    Args:
        features (dict): Dictionary containing market features:
            - iv_rank: Implied Volatility Rank (0-100) [corrected in feature engineering]
            - adx_14: Average Directional Index (0-100)
            - trend_regime: Trend classification (0-4)
            - rsi_14: Relative Strength Index (0-100)
            - price_vs_sma_20: Price relative to 20-day SMA (-0.20 to +0.20)
            - volatility_regime: Volatility classification (0-4)
    
    Returns:
        str: Strategy name (one of 10 strategies)
    
    Target distribution:
        - IRON_CONDOR: 20-30% (High IV + Ranging)
        - LONG_CALL: 15-20% (Low IV + Strong Uptrend)
        - LONG_PUT: 15-20% (Low IV + Strong Downtrend)
        - IRON_BUTTERFLY: 10-15% (Very High IV + Ranging)
        - BULL_CALL_SPREAD: 10-15% (Medium IV + Moderate Bullish)
        - BEAR_PUT_SPREAD: 10-15% (Medium IV + Moderate Bearish)
        - LONG_STRADDLE: 5-10% (Low IV + Neutral, expecting expansion)
        - LONG_STRANGLE: 5-10% (Low IV + Neutral, expecting expansion)
        - CALENDAR_SPREAD: 3-5% (Low IV + Very Neutral)
        - DIAGONAL_SPREAD: 3-5% (Medium IV + Slight bias)
    """
    # Use iv_rank (now corrected in feature engineering)
    iv_rank = features.get('iv_rank', 50)
    adx = features.get('adx_14', 20)
    trend_regime = features.get('trend_regime', 2)
    rsi = features.get('rsi_14', 50)
    price_vs_sma = features.get('price_vs_sma_20', 0)
    volatility_regime = features.get('volatility_regime', 1)
    
    # ========================================================================
    # PRIORITY 1: Check Diagonal Spread FIRST (most specific, rare)
    # ========================================================================
    # FIXED: Must check before IC to prevent IC from stealing these days
    # Diagonal needs very specific conditions: medium IV + slight bias + low ADX
    if 45 < iv_rank < 60 and trend_regime == 2 and 0.005 < abs(price_vs_sma) < 0.015 and adx < 15:
        return 'DIAGONAL_SPREAD'
    
    # ========================================================================
    # PRIORITY 2: High IV + Ranging = Premium Selling (MOST COMMON)
    # ========================================================================
    # FIXED v2: Removed RSI requirement - was too restrictive (10.1% vs 20-30%)
    # Iron Condor should be default for high IV ranging markets
    if 50 < iv_rank < 75 and adx < 25:
        return 'IRON_CONDOR'
    
    # Very high IV + ranging = Iron Butterfly
    # FIXED: Lowered from >75 to >70
    if iv_rank > 70 and adx < 20:
        return 'IRON_BUTTERFLY'
    
    # ========================================================================
    # PRIORITY 2: Low IV + Strong Trend = Long Options (SECOND MOST COMMON)
    # ========================================================================
    # FIXED v2: Tightened to prevent overuse (was 27.3%, should be 15-20%)
    # FIXED v3: Relaxed Long Put (was 5.1%, target 15-20%)
    if iv_rank < 42 and adx > 23:
        # Strong uptrend = Long Call
        if trend_regime >= 3 and rsi > 55:
            return 'LONG_CALL'
        # Strong downtrend = Long Put
        # FIXED: Relaxed IV (<42), ADX (>23), easier RSI/price conditions
        elif trend_regime <= 1 or (price_vs_sma < -0.025 and rsi < 45):
            return 'LONG_PUT'
        # NEW: Catch strong selloffs
        elif rsi < 33 or price_vs_sma < -0.04:
            return 'LONG_PUT'
    
    # ========================================================================
    # PRIORITY 3: Medium IV + Moderate Trend = Spreads
    # ========================================================================
    # FIXED v3: Further tightened Bull Call Spread (was 19.9%, target 10-15%)
    # Narrower IV range + higher ADX + RSI requirement
    if 45 <= iv_rank <= 60:
        # Moderate bullish = Bull Call Spread
        # FIXED: Narrower IV (45-60), higher ADX (22), added RSI check (>58)
        if trend_regime >= 3 and adx > 22 and rsi > 58:
            return 'BULL_CALL_SPREAD'
        # Moderate bearish = Bear Put Spread
        elif trend_regime <= 1 and adx > 20:
            return 'BEAR_PUT_SPREAD'
    
    # ========================================================================
    # PRIORITY 4: Low IV + Neutral = Volatility Expansion Plays
    # ========================================================================
    # FIXED v4: Relaxed IV threshold (30→35) and broadened RSI/ADX for more coverage
    if iv_rank < 35 and 45 < rsi < 58:  # Was < 30 and 45 < rsi < 55
        # Very neutral + ranging = Straddle
        if adx < 17:  # Was < 15
            return 'LONG_STRADDLE'
        # Slightly less neutral = Strangle (cheaper)
        elif adx < 22:  # Was < 20
            return 'LONG_STRANGLE'
    
    # ========================================================================
    # PRIORITY 5: Low IV + Very Neutral = Time Decay Plays
    # ========================================================================
    # Calendar spread for EXTREMELY neutral, low IV conditions
    # FIXED v2: Even more restrictive - Calendar should be RARE (3-5%)
    # FIXED v3: Slightly relaxed (was 0.8%, target 3-5%)
    # Require: Low IV + Very low ADX + Very neutral RSI + Very stable price
    if iv_rank < 33 and adx < 14 and 46 < rsi < 54 and abs(price_vs_sma) < 0.012:
        return 'CALENDAR_SPREAD'
    
    # Diagonal Spread already checked at Priority 1 (before IC)
    
    # ========================================================================
    # BROADER RULES: Catch common market conditions that don't fit strict rules
    # ========================================================================
    # These are still REAL selections based on market conditions, not defaults
    # They handle the "medium everything" days that are common in real markets
    
    # NEW v4: Catch bearish Long Put before IC steals them
    if iv_rank < 50 and (trend_regime <= 1 or rsi < 40 or price_vs_sma < -0.03):
        if adx > 18:
            return 'LONG_PUT'
    
    # Medium-High IV + Ranging = Iron Condor (most common neutral strategy)
    # FIXED v4: Raised threshold from 45 to 50 to prevent stealing Long Put days
    if iv_rank > 50 and adx < 25:
        return 'IRON_CONDOR'
    
    # Medium IV + Moderate Trend = Spreads
    # FIXED v4: Further tightened Bull Call BROADER rule to align with PRIORITY rule
    if 40 <= iv_rank <= 65:  # Was 35-70 (too broad)
        if adx > 20:  # Was 18 (too low)
            if rsi > 60 and trend_regime >= 3:  # Was 55 (too easy)
                return 'BULL_CALL_SPREAD'
            elif rsi < 45:  # Was 48
                return 'BEAR_PUT_SPREAD'
    
    # Low-Medium IV + Weak Trend = Long Options (less strict)
    # FIXED v3: Easier for Long Put to trigger
    if iv_rank < 45:
        if adx > 20:
            if rsi > 52:
                return 'LONG_CALL'
            elif rsi < 50:  # Easier threshold for Long Put
                return 'LONG_PUT'
    
    # Very Neutral + Medium IV = Calendar or Diagonal
    # FIXED v4: Reversed logic - stable price = Calendar, slight bias = Diagonal
    if 40 < iv_rank < 60 and adx < 18 and 46 < rsi < 54:
        if abs(price_vs_sma) < 0.008:  # Very stable (< 0.8% from SMA) = Calendar
            return 'CALENDAR_SPREAD'
        elif 0.005 < abs(price_vs_sma) < 0.015:  # Slight bias (0.5-1.5%) = Diagonal
            return 'DIAGONAL_SPREAD'
        # If > 1.5% from SMA, fall through to other strategies
    
    # ========================================================================
    # FINAL FALLBACK: Only for truly ambiguous days
    # ========================================================================
    # If we still haven't matched, use the most common strategy for the IV regime
    # This is better than skipping, as it's based on volatility regime
    
    if iv_rank > 55:
        # High IV = sell premium
        return 'IRON_CONDOR'
    elif iv_rank < 35:
        # Low IV = buy options
        if rsi >= 50:
            return 'LONG_CALL'
        else:
            return 'LONG_PUT'
    else:
        # Medium IV = spreads
        if rsi >= 50:
            return 'BULL_CALL_SPREAD'
        else:
            return 'BEAR_PUT_SPREAD'


def validate_strategy_distribution(training_data):
    """
    Validate that strategy distribution matches expected ranges
    
    Args:
        training_data (pd.DataFrame): Training data with 'strategy' column
    
    Returns:
        tuple: (is_valid, failures)
            - is_valid (bool): True if all validations pass
            - failures (list): List of validation failures
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
            'missing': list(set(expected_ranges.keys()) - set(strategy_pct.index)),
            'status': 'FAIL'
        })
    
    return len(failures) == 0, failures


def get_strategy_info(strategy_name):
    """
    Get information about a specific strategy
    
    Args:
        strategy_name (str): Name of the strategy
    
    Returns:
        dict: Strategy information including description, conditions, target %
    """
    strategy_info = {
        'IRON_CONDOR': {
            'description': 'Sell OTM call spread + OTM put spread',
            'conditions': 'High IV (50-75) + Ranging (ADX < 25) + Neutral RSI',
            'target_pct': '20-30%',
            'risk_profile': 'Defined risk, neutral',
            'ideal_market': 'High volatility, sideways movement'
        },
        'IRON_BUTTERFLY': {
            'description': 'Sell ATM call + ATM put, buy OTM wings',
            'conditions': 'Very High IV (>70) + Very Ranging (ADX < 20)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, neutral, tighter profit zone',
            'ideal_market': 'Very high volatility, very stable price'
        },
        'LONG_CALL': {
            'description': 'Buy OTM call option',
            'conditions': 'Low IV (<40) + Strong Uptrend (ADX > 25, trend >= 3)',
            'target_pct': '15-20%',
            'risk_profile': 'Limited risk, unlimited upside',
            'ideal_market': 'Low volatility, strong bullish trend'
        },
        'LONG_PUT': {
            'description': 'Buy OTM put option',
            'conditions': 'Low IV (<40) + Strong Downtrend (ADX > 25, trend <= 1)',
            'target_pct': '15-20%',
            'risk_profile': 'Limited risk, high downside profit',
            'ideal_market': 'Low volatility, strong bearish trend'
        },
        'BULL_CALL_SPREAD': {
            'description': 'Buy call, sell higher strike call',
            'conditions': 'Medium IV (40-65) + Moderate Bullish (trend >= 3, ADX > 20)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, defined profit',
            'ideal_market': 'Medium volatility, moderate uptrend'
        },
        'BEAR_PUT_SPREAD': {
            'description': 'Buy put, sell lower strike put',
            'conditions': 'Medium IV (40-65) + Moderate Bearish (trend <= 1, ADX > 20)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, defined profit',
            'ideal_market': 'Medium volatility, moderate downtrend'
        },
        'LONG_STRADDLE': {
            'description': 'Buy ATM call + ATM put (same strike)',
            'conditions': 'Low IV (<30) + Very Neutral (RSI 45-55, ADX < 15)',
            'target_pct': '5-10%',
            'risk_profile': 'Limited risk, profit from large move either direction',
            'ideal_market': 'Low volatility expecting expansion, uncertain direction'
        },
        'LONG_STRANGLE': {
            'description': 'Buy OTM call + OTM put (different strikes)',
            'conditions': 'Low IV (<30) + Neutral (RSI 45-55, ADX < 20)',
            'target_pct': '5-10%',
            'risk_profile': 'Limited risk, cheaper than straddle',
            'ideal_market': 'Low volatility expecting expansion, uncertain direction'
        },
        'CALENDAR_SPREAD': {
            'description': 'Sell near-term option, buy far-term option (same strike)',
            'conditions': 'Low IV (<35) + Very Neutral (ADX < 15, RSI 45-55, stable price)',
            'target_pct': '3-5%',
            'risk_profile': 'Limited risk, profit from time decay',
            'ideal_market': 'Low volatility, very stable price'
        },
        'DIAGONAL_SPREAD': {
            'description': 'Sell near-term option, buy far-term option (different strikes)',
            'conditions': 'Medium IV (45-60) + Slight Bias (0.5-1.5% from SMA, ADX < 15)',
            'target_pct': '3-5%',
            'risk_profile': 'Limited risk, combines time decay + directional',
            'ideal_market': 'Medium volatility, slight directional bias'
        }
    }
    
    return strategy_info.get(strategy_name, {
        'description': 'Unknown strategy',
        'conditions': 'N/A',
        'target_pct': 'N/A',
        'risk_profile': 'N/A',
        'ideal_market': 'N/A'
    })
