"""
Strategy Selection Module
Determines optimal options strategy based on market conditions

Version: 6.0 (SINGLE-TIER RULES - TUNED)
Date: December 6, 2024
Status: Production Ready

MAJOR CHANGE v6.0: Applied 5 critical fixes based on v5 validation feedback:
1. Tightened Bull Call Spread direct rule (prevent overuse)
2. Added multiple paths for Long Put (increase coverage)
3. Relaxed Calendar Spread conditions (reach 3-5% target)
4. Made fallback more selective (most important fix)
5. Slightly relaxed Long Call (reach 15-20% target)

Expected improvement: 5/10 → 8-9/10 strategies in range

Backup of v5.0 available at: strategy_selector_v5_backup.py
"""


def select_strategy_from_features(features):
    """
    Single-tier rule-based strategy selection
    
    SIMPLIFIED APPROACH:
    - One rule per strategy (no PRIORITY vs BROADER conflicts)
    - Predictable outcomes (adjust one threshold = immediate effect)
    - Easier to maintain and tune
    
    Args:
        features (dict): Dictionary containing market features:
            - iv_rank: Implied Volatility Rank (0-100)
            - adx_14: Average Directional Index (0-100)
            - trend_regime: Trend classification (0-4)
            - rsi_14: Relative Strength Index (0-100)
            - price_vs_sma_20: Price relative to 20-day SMA (-0.20 to +0.20)
    
    Returns:
        str: Strategy name (one of 10 strategies)
    
    Target distribution:
        - IRON_CONDOR: 20-30% (High IV + Ranging)
        - LONG_CALL: 15-20% (Low IV + Strong Uptrend)
        - LONG_PUT: 15-20% (Low IV + Strong Downtrend)
        - IRON_BUTTERFLY: 10-15% (Very High IV + Ranging)
        - BULL_CALL_SPREAD: 10-15% (Medium IV + Moderate Bullish)
        - BEAR_PUT_SPREAD: 10-15% (Medium IV + Moderate Bearish)
        - LONG_STRADDLE: 5-10% (Low IV + Neutral)
        - LONG_STRANGLE: 5-10% (Low IV + Neutral)
        - CALENDAR_SPREAD: 3-5% (Low IV + Very Neutral)
        - DIAGONAL_SPREAD: 3-5% (Medium IV + Slight bias)
    """
    # Extract features
    iv_rank = features.get('iv_rank', 50)
    adx = features.get('adx_14', 20)
    trend_regime = features.get('trend_regime', 2)
    rsi = features.get('rsi_14', 50)
    price_vs_sma = features.get('price_vs_sma_20', 0)
    
    # ========================================================================
    # RULE 1: Diagonal Spread (Check first - most specific)
    # ========================================================================
    # Medium IV + Neutral trend + Slight bias + Low ADX
    if 45 < iv_rank < 60 and trend_regime == 2 and 0.005 < abs(price_vs_sma) < 0.012 and adx < 15:
        return 'DIAGONAL_SPREAD'
    
    # ========================================================================
    # RULE 2: Iron Condor (Most common - 20-30%)
    # ========================================================================
    # High IV + Ranging + Neutral RSI
    # REALISTIC: Sell premium when IV is elevated (expensive options) and
    # market is ranging (low ADX). Neutral RSI confirms no directional bias.
    # This is the bread-and-butter strategy for high IV environments.
    if 52 < iv_rank < 75 and adx < 25 and 45 < rsi < 55:
        return 'IRON_CONDOR'
    
    # ========================================================================
    # RULE 3: Iron Butterfly (10-15%)
    # ========================================================================
    # Very High IV + Very Ranging
    # REALISTIC: Use when IV is very high (premium rich) and market is very stable.
    # Tighter profit zone than IC but higher premium collected. Requires more
    # precise market stability prediction.
    if iv_rank > 68 and adx < 20:
        return 'IRON_BUTTERFLY'
    
    # ========================================================================
    # RULE 4: Long Call (15-20%)
    # ========================================================================
    # Low IV + Strong Uptrend
    # REALISTIC: Buy calls when options are cheap (low IV) and strong uptrend
    # is confirmed (high ADX, bullish regime, RSI > 55). Classic directional play.
    # V6: Slightly relaxed to reach 15-20% target
    if iv_rank < 46 and adx > 21:  # Relaxed by 1 point each
        if trend_regime >= 3 and rsi > 54:  # RSI relaxed from 55 to 54
            return 'LONG_CALL'
    
    # ========================================================================
    # RULE 5: Long Put (15-20%)
    # ========================================================================
    # Low IV + Strong Downtrend OR Strong Bearish Signals
    # REALISTIC: Buy puts when options are cheap (low IV) AND market is bearish
    # V6: Added multiple qualifying paths to catch more bearish days
    if iv_rank < 48:  # Slightly broader - still "cheap options"
        # Path 1: Strong bearish trend (original condition)
        if adx > 20 and (trend_regime <= 1 or rsi < 42 or price_vs_sma < -0.025):
            return 'LONG_PUT'
        # Path 2: Moderate trend but clear bearish signals
        elif adx >= 15 and (rsi < 38 or price_vs_sma < -0.035):
            return 'LONG_PUT'
        # Path 3: Very oversold (regardless of trend)
        elif rsi < 33:
            return 'LONG_PUT'
    
    # ========================================================================
    # RULE 6: Bull Call Spread (10-15%)
    # ========================================================================
    # Medium-High IV + Moderate Bullish + Strong Momentum
    # REALISTIC: Use spreads when IV is elevated (not cheap enough for long calls)
    # but trend is bullish. Defined risk strategy.
    # V6: Tightened all thresholds to prevent overuse
    if 56 <= iv_rank <= 63 and trend_regime >= 3 and adx > 26 and rsi > 62:
        return 'BULL_CALL_SPREAD'
    
    # ========================================================================
    # RULE 7: Bear Put Spread (10-15%)
    # ========================================================================
    # Medium-High IV + Moderate Bearish + Strong Momentum
    # REALISTIC: Use spreads when IV is elevated but trend is bearish
    # Defined risk, lower cost than long puts in medium IV
    if 54 <= iv_rank <= 65 and trend_regime <= 1 and adx > 22 and rsi < 45:
        return 'BEAR_PUT_SPREAD'
    
    # ========================================================================
    # RULE 8: Long Straddle (5-10%)
    # ========================================================================
    # Low IV + Very Neutral + Very Ranging
    if iv_rank < 35 and 45 < rsi < 58:
        if adx < 17:
            return 'LONG_STRADDLE'
    
    # ========================================================================
    # RULE 9: Long Strangle (5-10%)
    # ========================================================================
    # Low IV + Neutral + Ranging
    # REALISTIC: Buy strangles when options are cheap and expecting big move
    # but uncertain of direction. Cheaper than straddle (OTM options)
    if iv_rank < 36 and 44 < rsi < 59:
        if adx < 25:  # Slightly more lenient for ranging markets
            return 'LONG_STRANGLE'
    
    # ========================================================================
    # RULE 10: Calendar Spread (3-5%)
    # ========================================================================
    # Low IV + Very Neutral + Very Stable Price
    # REALISTIC: Time decay play when market is stable and IV is low
    # Profit from theta decay as near-term option loses value faster
    # V6: Slightly relaxed all conditions to reach 3-5% target
    if iv_rank < 42 and adx < 20 and 42 < rsi < 58 and abs(price_vs_sma) < 0.022:
        return 'CALENDAR_SPREAD'
    
    # ========================================================================
    # FINAL FALLBACK: For days that don't match any specific rule
    # ========================================================================
    # V6: More selective - require stronger signals for spreads
    # Otherwise default to neutral strategy
    
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
        # Medium IV (35-55): Be more selective for spreads
        if rsi > 58 and adx > 18:  # Strong bullish momentum
            return 'BULL_CALL_SPREAD'
        elif rsi < 42 and adx > 18:  # Strong bearish momentum
            return 'BEAR_PUT_SPREAD'
        else:
            # Weak signals in medium IV → default to neutral strategy
            return 'IRON_CONDOR'


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
            'conditions': 'High IV (52-75) + Ranging (ADX < 25) + Neutral RSI (45-55)',
            'target_pct': '20-30%',
            'risk_profile': 'Defined risk, neutral',
            'ideal_market': 'High volatility, sideways movement'
        },
        'IRON_BUTTERFLY': {
            'description': 'Sell ATM call + ATM put, buy OTM wings',
            'conditions': 'Very High IV (>68) + Very Ranging (ADX < 20)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, neutral, tighter profit zone',
            'ideal_market': 'Very high volatility, very stable price'
        },
        'LONG_CALL': {
            'description': 'Buy OTM call option',
            'conditions': 'Low IV (<45) + Strong Uptrend (ADX > 22, trend >= 3, RSI > 55)',
            'target_pct': '15-20%',
            'risk_profile': 'Limited risk, unlimited upside',
            'ideal_market': 'Low volatility, strong bullish trend'
        },
        'LONG_PUT': {
            'description': 'Buy OTM put option',
            'conditions': 'Low IV (<45) + Strong Downtrend OR Bearish Signals',
            'target_pct': '15-20%',
            'risk_profile': 'Limited risk, high downside profit',
            'ideal_market': 'Low volatility, strong bearish trend'
        },
        'BULL_CALL_SPREAD': {
            'description': 'Buy call, sell higher strike call',
            'conditions': 'Medium-High IV (50-62) + Strong Bullish (trend >= 3, ADX > 24, RSI > 62)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, defined profit',
            'ideal_market': 'Medium volatility, moderate uptrend'
        },
        'BEAR_PUT_SPREAD': {
            'description': 'Buy put, sell lower strike put',
            'conditions': 'Medium-High IV (50-62) + Strong Bearish (trend <= 1, ADX > 22, RSI < 42)',
            'target_pct': '10-15%',
            'risk_profile': 'Defined risk, defined profit',
            'ideal_market': 'Medium volatility, moderate downtrend'
        },
        'LONG_STRADDLE': {
            'description': 'Buy ATM call + ATM put (same strike)',
            'conditions': 'Low IV (<35) + Very Neutral (RSI 45-58, ADX < 17)',
            'target_pct': '5-10%',
            'risk_profile': 'Limited risk, profit from large move either direction',
            'ideal_market': 'Low volatility expecting expansion, uncertain direction'
        },
        'LONG_STRANGLE': {
            'description': 'Buy OTM call + OTM put (different strikes)',
            'conditions': 'Low IV (<35) + Neutral (RSI 45-58, ADX < 24)',
            'target_pct': '5-10%',
            'risk_profile': 'Limited risk, cheaper than straddle',
            'ideal_market': 'Low volatility expecting expansion, uncertain direction'
        },
        'CALENDAR_SPREAD': {
            'description': 'Sell near-term option, buy far-term option (same strike)',
            'conditions': 'Low IV (<38) + Very Neutral (ADX < 16, RSI 44-56, stable price)',
            'target_pct': '3-5%',
            'risk_profile': 'Limited risk, profit from time decay',
            'ideal_market': 'Low volatility, very stable price'
        },
        'DIAGONAL_SPREAD': {
            'description': 'Sell near-term option, buy far-term option (different strikes)',
            'conditions': 'Medium IV (45-60) + Slight Bias (0.5-1.2% from SMA, ADX < 15)',
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
